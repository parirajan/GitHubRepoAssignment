#!/bin/bash

# Configuration Variables
ASG_NAME="your-asg-name"
CONSUL_HTTP_ADDR="http://your-consul-address:8500"
AWS_REGION="your-aws-region"
TARGET_GROUP_ARN="your-target-group-arn" # For ELBv2 (ALB/NLB). For ELB, use ELB name instead.

# Helper Functions

# Function to get the health status of instances from the target group
get_target_group_health() {
    aws elbv2 describe-target-health --target-group-arn "$TARGET_GROUP_ARN" \
        --query 'TargetHealthDescriptions[].TargetHealth.State' --output text
}

# Function to start the ASG instance refresh and return the refresh ID
start_asg_refresh() {
    aws autoscaling start-instance-refresh --auto-scaling-group-name "$ASG_NAME" \
        --query 'InstanceRefreshId' --output text
}

# Function to check the refresh status of a given refresh ID
check_refresh_status() {
    local refresh_id=$1
    aws autoscaling describe-instance-refreshes --auto-scaling-group-name "$ASG_NAME" \
        --instance-refresh-ids "$refresh_id" \
        --query 'InstanceRefreshes[].Status' --output text
}

# Function to unprotect the Consul leader instance
unprotect_leader() {
    # Assuming leader protection logic and leader IP fetching is implemented here
    local leader_instance_id="leader-instance-id" # Placeholder for leader instance ID
    aws autoscaling set-instance-protection --instance-ids "$leader_instance_id" \
        --auto-scaling-group-name "$ASG_NAME" --no-protected-from-scale-in
}

# Main Monitoring Function
monitor_and_unprotect_leader() {
    local refresh_id=$(start_asg_refresh)
    echo "Started ASG instance refresh with ID: $refresh_id"

    while :; do
        local refresh_status=$(check_refresh_status "$refresh_id")
        echo "Refresh Status: $refresh_status"

        if [[ "$refresh_status" == "InProgress" ]]; then
            local all_healthy="true"
            local target_health_states=$(get_target_group_health)
            for state in $target_health_states; do
                if [[ "$state" != "healthy" ]]; then
                    all_healthy="false"
                    break
                fi
            done

            if [[ "$all_healthy" == "true" ]]; then
                echo "All instances are healthy in the target group. Proceeding to unprotect the leader."
                unprotect_leader
                # Optionally break here if you want to stop monitoring once the leader is unprotected
                # break
            else
                echo "Waiting for all instances to become healthy..."
            fi
        elif [[ "$refresh_status" == "Successful" ]]; then
            echo "ASG instance refresh completed successfully."
            break
        elif [[ "$refresh_status" == "Failed" || "$refresh_status" == "Cancelled" ]]; then
            echo "ASG instance refresh did not complete successfully. Status: $refresh_status"
            break
        fi
        sleep 30
    done
}

# Execute the monitoring function
monitor_and_unprotect_leader
