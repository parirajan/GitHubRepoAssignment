function check_consul_cluster_health() {
    local max_wait_seconds=300 # Maximum time to wait for healthy instances
    local start_time=$(date +%s)

    echo "Waiting for a minimum of 3 healthy instances in the ASG..."

    # Wait for ASG to have at least 3 healthy instances
    while : ; do
        now=$(date +%s)
        if [[ $((now - start_time)) -gt max_wait_seconds ]]; then
            echo "Timeout waiting for ASG to have 3 healthy instances."
            return 1
        fi

        instances=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
                    --query 'AutoScalingGroups[].Instances[?LifecycleState==`InService`].[InstanceId]' --output text)
        healthy_count=$(echo "$instances" | awk '{print NF}') # Number of healthy instances

        if [[ "$healthy_count" -ge 3 ]]; then
            echo "ASG has $healthy_count healthy instances."
            break
        else
            echo "Waiting for more instances to become healthy..."
            sleep 30
        fi
    done

    # Check ELB Target Group health
    echo "Checking ELB Target Group health..."
    for instance_id in $instances; do
        health_status=$(aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
                          --query "TargetHealthDescriptions[?Target.Id=='$instance_id'].TargetHealth.State" --output text)
        if [[ "$health_status" != "healthy" ]]; then
            echo "Instance $instance_id is not healthy in the target group."
            return 1
        fi
    done

    # Check Consul cluster health
    echo "Checking Consul cluster health..."
    consul_info=$(curl -s --header "X-Consul-Token: $CONSUL_ACL_TOKEN" "$CONSUL_HTTP_ADDR/v1/operator/raft/configuration" | jq .)
    leader=$(echo "$consul_info" | jq -r '.Configuration.Leader')
    if [[ -z "$leader" || "$leader" == "null" ]]; then
        echo "Consul cluster has no leader."
        return 1
    fi

    # Check for at least 2 followers that are voters
    voter_count=$(echo "$consul_info" | jq '[.Configuration.Servers[] | select(.Suffrage=="Voter" and .Leader==false)] | length')
    if [[ "$voter_count" -lt 2 ]]; then
        echo "Consul cluster does not have at least 2 followers that are voters."
        return 1
    fi

    echo "Consul cluster is healthy with 1 leader and at least 2 voting followers."
}

# Usage example:
# check_consul_cluster_health "my-consul-asg" "arn:aws:elasticloadbalancing:region:account-id:targetgroup/my-target-group" "http://127.0.0.1:8500"
