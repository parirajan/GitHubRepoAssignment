#!/bin/bash

# Configuration
ASG_NAME="your-asg-name"
REFRESH_ID="your-refresh-id"
TARGET_GROUP_ARN="your-target-group-arn"
AWS_REGION="your-aws-region"

# Function to check the health of instances in the target group
check_instance_health() {
    echo "Checking health of instances in the target group..."
    aws elbv2 describe-target-health --target-group-arn "$TARGET_GROUP_ARN" --region "$AWS_REGION" | jq -r '.TargetHealthDescriptions[] | "\(.Target.Id) is \(.TargetHealth.State)"'
}

# Monitor the ASG refresh status
while :; do
    # Get the status of the ASG refresh
    refresh_status=$(aws autoscaling describe-instance-refreshes --auto-scaling-group-name "$ASG_NAME" --instance-refresh-ids "$REFRESH_ID" --region "$AWS_REGION" --query 'InstanceRefreshes[0].Status' --output text)
    echo "Refresh Status: $refresh_status"

    # If the refresh is in progress, check the instance health
    if [[ "$refresh_status" == "InProgress" ]]; then
        check_instance_health
    elif [[ "$refresh_status" == "Successful" ]]; then
        echo "ASG refresh completed successfully."
        check_instance_health  # Final health check
        break
    elif [[ "$refresh_status" == "Failed" || "$refresh_status" == "Cancelled" ]]; then
        echo "ASG refresh did not complete successfully. Status: $refresh_status"
        exit 1
    fi

    sleep 30  # Wait before checking again
done
