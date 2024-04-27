#!/bin/bash

# Define the Consul server endpoint
CONSUL_SERVER="consul-server:8500"
COMMON_KEY="service/leader"

# Create or renew a session in Consul using the common key
create_or_renew_session() {
    if [[ -z "$SESSION_ID" || "$SESSION_ID" == "null" ]]; then
        # Create a new session if not already available
        echo "Creating a new session for leadership contention..."
        response=$(curl -s -X PUT --data "{\"Name\": \"$COMMON_KEY\", \"TTL\": \"15s\", \"Behavior\": \"delete\"}" "http://${CONSUL_SERVER}/v1/session/create")
        SESSION_ID=$(echo "$response" | jq -r '.ID')
        echo "Session created with ID: $SESSION_ID"
    else
        # Renew the existing session
        echo "Renewing the existing session..."
        curl -s -X PUT "http://${CONSUL_SERVER}/v1/session/renew/$SESSION_ID" > /dev/null
    fi
}

# Attempt to acquire the lock
acquire_lock() {
    result=$(curl -s -X PUT --data "{\"acquire\": \"$SESSION_ID\"}" "http://${CONSUL_SERVER}/v1/kv/$COMMON_KEY" | jq -r '.')
    if [[ "$result" == "true" ]]; then
        echo "$(hostname) has acquired the lock and is now the leader."
        return 0
    else
        echo "$(hostname) did not acquire the lock and is a follower."
        return 1
    fi
}

# Monitor the lock and attempt to re-acquire if lost
monitor_lock() {
    while true; do
        if acquire_lock; then
            # Perform leader tasks
            perform_leader_tasks
        else
            # Sleep and retry to acquire the lock
            sleep 5
        fi
    done
}

# Leader tasks performed by the instance that holds the lock
perform_leader_tasks() {
    echo "Performing leader tasks..."
    while true; do
        echo "Leader $(hostname) is active..."
        sleep 5
    done
}

# Setup trap for cleanup on script exit
trap cleanup EXIT

cleanup() {
    echo "Releasing the lock and destroying the session..."
    curl -s -X PUT "http://${CONSUL_SERVER}/v1/kv/$COMMON_KEY?release=$SESSION_ID"
    curl -s -X PUT "http://${CONSUL_SERVER}/v1/session/destroy/$SESSION_ID"
    echo "Cleanup completed by $(hostname)."
}

# Main execution flow
create_or_renew_session
monitor_lock
