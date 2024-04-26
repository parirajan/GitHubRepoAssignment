#!/bin/bash

# Consul server endpoint
CONSUL_SERVER="consul-server:8500"

# Session and lock key configuration
SESSION_DATA='{"Name": "myServiceLock", "TTL": "15s", "Behavior": "release"}'
LOCK_KEY="service/lock"

# Create a new session in Consul
create_session() {
    echo "Creating new session..."
    SESSION_ID=$(curl -s -X PUT -d "$SESSION_DATA" "http://$CONSUL_SERVER/v1/session/create" | jq -r '.ID')
    if [[ -z "$SESSION_ID" ]]; then
        echo "Failed to create session, retrying..."
        sleep 5
        create_session
    else
        echo "Session created with ID: $SESSION_ID"
    fi
}

create_session

# Function to attempt to acquire the lock
acquire_lock() {
    LOCK_ACQUIRED=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/${LOCK_KEY}?acquire=${SESSION_ID}")
    if [[ "$LOCK_ACQUIRED" == "true" ]]; then
        echo "Lock acquired successfully by $(hostname)."
        return 0
    else
        echo "Failed to acquire lock."
        return 1
    fi
}

# Function to perform leader tasks
perform_leader_tasks() {
    echo "$(hostname) is now the leader. Performing leader tasks..."
    while true; do
        echo "Leader is active..."
        sleep 5
    done
}

# Function to renew the session periodically
renew_session() {
    while true; do
        echo "Renewing session..."
        response=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/session/renew/$SESSION_ID")
        if [[ "$(echo $response | jq -r '.[] | select(.ID == null)')" != "" ]]; then
            echo "Session renewal failed or session expired, creating new session..."
            create_session
        else
            echo "Session renewed successfully."
        fi
        sleep 10
    done
}

# Monitor and try to acquire the lock
monitor_and_acquire_lock() {
    while true; do
        if acquire_lock; then
            perform_leader_tasks &
            renew_session &
            wait $!  # Wait for leader tasks to complete before exiting
            break
        else
            echo "Retrying to acquire lock..."
            sleep 5
        fi
    done
}

# Cleanup function to release the lock and destroy the session
cleanup() {
    echo "Cleaning up..."
    curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/${LOCK_KEY}?release=${SESSION_ID}"
    curl -s -X PUT "http://$CONSUL_SERVER/v1/session/destroy/${SESSION_ID}"
    echo "Resources released."
}

# Setup trap for cleanup on script exit
trap cleanup EXIT

# Start monitoring and lock acquisition
monitor_and_acquire_lock
