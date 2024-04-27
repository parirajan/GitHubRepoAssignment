#!/bin/bash

# Configuration variables
CONSUL_SERVER="consul-server:8500"
SESSION_NAME="service_leader_election"
LOCK_KEY="service/leader"
TTL="15s"  # Time-To-Live for the session

# Create a session in Consul
create_session() {
    local session_id=$(curl --request PUT --data "{\"Name\": \"$SESSION_NAME\", \"TTL\": \"$TTL\", \"Behavior\": \"delete\"}" http://$CONSUL_SERVER/v1/session/create | jq -r '.ID')
    echo $session_id
}

# Renew the session
renew_session() {
    local session_id=$1
    while true; do
        curl --request PUT http://$CONSUL_SERVER/v1/session/renew/$session_id
        sleep 10  # Renew every 10 seconds, half of the TTL
    done
}

# Acquire the lock
acquire_lock() {
    local session_id=$1
    while true; do
        local result=$(curl --request PUT --data "{\"acquire\": \"$session_id\"}" http://$CONSUL_SERVER/v1/kv/$LOCK_KEY | jq -r '.')
        if [[ "$result" == "true" ]]; then
            echo "Lock acquired, node is leader"
            break
        fi
        sleep 5  # Check every 5 seconds if the lock can be acquired
    done
}

# Leader tasks
perform_leader_tasks() {
    echo "Performing leader tasks"
    # Simulate long-running leader task
    while true; do
        echo "Leader is active"
        sleep 5
    done
}

# Main logic
session_id=$(create_session)
if [[ -z "$session_id" || "$session_id" == "null" ]]; then
    echo "Failed to create session"
    exit 1
fi
echo "Session created with ID: $session_id"

# Start session renewal in the background
renew_session $session_id &
renew_pid=$!

# Attempt to acquire the lock and perform tasks if successful
acquire_lock $session_id
perform_leader_tasks

# Cleanup when the node shuts down
trap "curl --request PUT http://$CONSUL_SERVER/v1/session/destroy/$session_id; kill $renew_pid" EXIT
