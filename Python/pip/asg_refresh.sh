#!/bin/bash

# Configurable Variables
VAULT_ADDR="https://<YOUR_VAULT_SERVER_ADDRESS>"
VAULT_TOKEN="<YOUR_VAULT_TOKEN>"
VAULT_SECRET_PATH="<YOUR_CONSUL_ACL_TOKEN_PATH_IN_VAULT>"
AWS_REGION="<YOUR_AWS_REGION>"
ASG_NAME="<YOUR_ASG_NAME>"
CONSUL_HTTP_ADDR="https://<YOUR_CONSUL_SERVER_ADDRESS>:8501"

# Retrieve Consul ACL token from Vault
retrieve_consul_acl_from_vault() {
    CONSUL_ACL_TOKEN=$(vault read -address=${VAULT_ADDR} -token=${VAULT_TOKEN} ${VAULT_SECRET_PATH} -format=json | jq -r .data.token)
    if [ -z "$CONSUL_ACL_TOKEN" ]; then
        echo "Failed to retrieve Consul ACL token from Vault"
        exit 1
    else
        echo "Consul ACL token retrieved successfully."
    fi
}

# Retrieve ELB name from ASG Tags
retrieve_elb_name_from_asg() {
    ELB_NAME=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names ${ASG_NAME} --region ${AWS_REGION} \
    --query 'AutoScalingGroups[].Tags[?Key==`ELBName`].Value' --output text)
    if [ -z "$ELB_NAME" ]; then
        echo "Failed to retrieve ELB name from ASG tags"
        exit 1
    else
        echo "ELB Name: ${ELB_NAME}"
    fi
}

# Function to get leader node ID from Consul
get_consul_leader_instance_id() {
    LEADER_IP=$(curl -s --header "X-Consul-Token: ${CONSUL_ACL_TOKEN}" ${CONSUL_HTTP_ADDR}/v1/status/leader | jq -r . | cut -d'"' -f 2 | cut -d':' -f 1)
    LEADER_ID=$(aws ec2 describe-instances --region ${AWS_REGION} \
    --filters "Name=private-ip-address,Values=${LEADER_IP}" \
    --query 'Reservations[*].Instances[*].[InstanceId]' --output text)
    echo "${LEADER_ID}"
}

function assign_consul_roles() {
    # Get the Consul leader
    LEADER=$(curl -s --header "X-Consul-Token: $CONSUL_ACL_TOKEN" "$CONSUL_HTTP_ADDR/v1/status/leader" | jq -r .)
    LEADER_IP=${LEADER%:*}

    # Get Raft configuration
    RAFT_CONFIG=$(curl -s --header "X-Consul-Token: $CONSUL_ACL_TOKEN" "$CONSUL_HTTP_ADDR/v1/operator/raft/configuration" | jq -r .)

    # Initialize arrays for followers
    declare -a FOLLOWER_INSTANCE_IDS=()

    # Process servers
    for row in $(echo "${RAFT_CONFIG}" | jq -r '.Configuration.Servers[] | @base64'); do
        _jq() {
            echo ${row} | base64 --decode | jq -r ${1}
        }
            # Extract and process each server from the raft configuration
            echo "${RAFT_CONFIG}" | jq -c '.Servers[]' | while IFS= read -r server; do
                server_ip=$(echo "$server" | jq -r '.Address' | cut -d':' -f1)
                
                if [[ "$server_ip" == "$LEADER_IP" ]]; then
                    # Process leader
                    LEADER_INSTANCE_ID=$(aws ec2 describe-instances --region "$AWS_REGION" \
                        --filters "Name=private-ip-address,Values=$server_ip" \
                        --query 'Reservations[*].Instances[*].InstanceId' --output text)
                    echo "Leader Instance ID: $LEADER_INSTANCE_ID"
                else
                    # Process followers
                    instance_id=$(aws ec2 describe-instances --region "$AWS_REGION" \
                        --filters "Name=private-ip-address,Values=$server_ip" \
                        --query 'Reservations[*].Instances[*].InstanceId' --output text)
                    FOLLOWER_INSTANCE_IDS+=("$instance_id")
                fi
            done
    done

    # Dynamically assign follower instance IDs to variables
    for i in "${!FOLLOWER_INSTANCE_IDS[@]}"; do
        declare "FOLLOWER$((i+1))_INSTANCE_ID=${FOLLOWER_INSTANCE_IDS[$i]}"
        echo "Follower $((i+1)) Instance ID: ${FOLLOWER_INSTANCE_IDS[$i]}"
    done
}



# Protect the leader instance in ASG
protect_leader_instance() {
    LEADER_ID=$(get_consul_leader_instance_id)
    aws autoscaling set-instance-protection --instance-ids ${LEADER_ID} \
    --auto-scaling-group-name ${ASG_NAME} --protected-from-scale-in
    echo "Leader instance ${LEADER_ID} is protected from scale-in."
}

# Scale out ASG by one instance
scale_out_asg() {
    CURRENT_CAPACITY=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name ${ASG_NAME} \
    --query 'AutoScalingGroups[*].DesiredCapacity' --output text)
    NEW_CAPACITY=$((CURRENT_CAPACITY + 1))
    aws autoscaling update-auto-scaling-group --auto-scaling-group-name ${ASG_NAME} \
    --desired-capacity ${NEW_CAPACITY}
    echo "Scaled out ASG to ${NEW_CAPACITY}."
}

# Wait for new node to join the cluster
wait_for_new_node_join() {
    echo "Waiting for the new node to join the cluster..."
    while true; do
        NEW_MEMBERS_COUNT=$(curl -s --header "X-Consul-Token: ${CONSUL_ACL_TOKEN}" ${CONSUL_HTTP_ADDR}/v1/catalog/nodes | jq length)
        if [ "${NEW_MEMBERS_COUNT}" -eq "$((CURRENT_CAPACITY + 1))" ]; then
            echo "New node has joined the cluster."
            break
        else
            sleep 10
        fi
    done
}

start_asg_refresh() {
    echo "Starting ASG refresh with 100% health check strategy..."
    aws autoscaling start-instance-refresh \
        --auto-scaling-group-name ${ASG_NAME} \
        --strategy Rolling \
        --preferences '{"MinHealthyPercentage": 100, "InstanceWarmup": 300}' \
        --region ${AWS_REGION}
    echo "ASG refresh initiated."
}

# Monitor ASG refresh and ELB health
monitor_asg_refresh_and_elb() {
    echo "Monitoring ASG refresh and ELB health..."
    while true; do
        STATUS=$(aws autoscaling describe-instance-refreshes --auto-scaling-group-name ${ASG_NAME} \
        --instance-refresh-ids ${REFRESH_ID} --query 'InstanceRefreshes[*].Status' --output text)
        if [[ ${STATUS} == "InProgress" ]]; then
            HEALTHY_COUNT=$(aws elb describe-instance-health --load-balancer-name ${ELB_NAME} \
            --query 'InstanceStates[?State==`InService`].InstanceId' --output text | wc -w)
            if [ "${HEALTHY_COUNT}" -eq "${NEW_CAPACITY}" ]; then
                echo "All instances are healthy in ELB."
                break
            fi
        elif [[ ${STATUS} == "Successful" ]]; then
            echo "ASG refresh completed successfully."
            break
        else
            sleep 10
        fi
    done
}

# Transfer leadership in Consul (if applicable)
transfer_consul_leadership() {
    curl --request PUT --header "X-Consul-Token: ${CONSUL_ACL_TOKEN}" ${CONSUL_HTTP_ADDR}/v1/operator/raft/transfer-leadership
    echo "Consul leadership transferred."
}

# Verify the new leader and raft peers
verify_consul_raft_peers() {
    echo "Verifying new leader and raft peers..."
    sleep 10  # Give some time for leadership transition
    RAFT_INFO=$(curl -s --header "X-Consul-Token: ${CONSUL_ACL_TOKEN}" ${CONSUL_HTTP_ADDR}/v1/operator/raft/configuration)
    
    # Check if there's a leader and it's not the old leader
    NEW_LEADER=$(echo "$RAFT_INFO" | jq -r '.Configuration.Leader')
    if [ -z "$NEW_LEADER" ] || [ "$NEW_LEADER" == "$LEADER_IP" ]; then
        echo "Leader transition failed or old leader still in charge."
        exit 1
    else
        echo "New leader established: $NEW_LEADER"
    fi
    
    # Verify all other nodes are followers and voters
    PEERS=$(echo "$RAFT_INFO" | jq -r '.Configuration.Servers[] | select(.Leader == false) | "\(.Address) is a \(.Suffrage)"')
    echo "Verifying followers and voters..."
    echo "$PEERS"
    
    # Count the number of voters that are not leaders
    VOTER_COUNT=$(echo "$PEERS" | grep -c "voter")
    if [ "$VOTER_COUNT" -lt 2 ]; then  # Expecting at least 2 followers as voters in a 3-node cluster
        echo "Insufficient number of followers marked as voters."
        exit 1
    else
        echo "Raft configuration appears correct with all nodes as followers and voters."
    fi
}

# Remove protection from leader and scale in
cleanup() {
    aws autoscaling set-instance-protection --instance-ids ${LEADER_ID} \
    --auto-scaling-group-name ${ASG_NAME} --no-protected-from-scale-in
    aws autoscaling update-auto-scaling-group --auto-scaling-group-name ${ASG_NAME} \
    --desired-capacity ${CURRENT_CAPACITY}
    echo "Cleanup done. Scaled in ASG to ${CURRENT_CAPACITY} and removed instance protection."
}

# Execute all steps
retrieve_consul_acl_from_vault
retrieve_elb_name_from_asg
protect_leader_instance
scale_out_asg
wait_for_new_node_join
start_asg_refresh
monitor_asg_refresh_and_elb
transfer_consul_leadership
verify_consul_raft_peers
cleanup
