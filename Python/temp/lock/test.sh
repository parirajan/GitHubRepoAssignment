#!/bin/bash

# Endpoint for the Consul server
CONSUL_SERVER="consul-server:8500"

# Create a session with TTL
SESSION_DATA='{"Name": "myServiceSession", "TTL": "30s", "Behavior": "delete"}'
SESSION_ID=$(curl -s -X PUT -d "$SESSION_DATA" "http://$CONSUL_SERVER/v1/session/create" | jq -r '.ID')
echo "Session created with ID: $SESSION_ID"

# Function to renew the session periodically
renew_session() {
    echo "Starting session renewal loop..."
    while true; do
        echo "Renewing session..."
        response=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/session/renew/$SESSION_ID")
        if [ "$(echo $response | jq -r '.[] | select(.ID == null)')" == "" ]; then
            echo "Session renewed successfully."
        else
            echo "Session renewal failed or session expired. Exiting."
            break
        fi
        sleep 20  # Renew session every 20 seconds, must be less than TTL
    done
    exit 1  # Exit script if session cannot be renewed
}

# Function to clean up on script exit
cleanup() {
    echo "Cleaning up..."
    # Destroy the session
    if curl -s -X PUT "http://$CONSUL_SERVER/v1/session/destroy/$SESSION_ID"; then
        echo "Session destroyed successfully."
    else
        echo "Failed to destroy session."
    fi
}

# Trap script exit for cleanup
trap cleanup EXIT

# Start session renewal in the background
renew_session &

# Simulate container workload here (replace this loop with your actual workload)
while true; do
    echo "Simulating some work..."
    sleep 10
done
