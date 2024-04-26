#!/bin/bash

# Consul server endpoint
CONSUL_SERVER="consul-server:8500"

# Session and lock key configuration
SESSION_DATA='{"Name": "myServiceLock", "TTL": "15s", "Behavior": "release"}'
LOCK_KEY="service/lock"

# Function to create a new session in Consul
create_session() {
    echo "Attempting to create a new session..."
    SESSION_ID=$(curl -s -X PUT -d "$SESSION_DATA" "http://$CONSUL_SERVER/v1/session/create" | jq -r '.ID')
    if [[ -z "$SESSION_ID" || "$SESSION_ID" == "null" ]]; then
        echo "Failed to create session, retrying..."
        sleep 5
        create_session
    else
        echo "Session created with ID: $SESSION_ID"
    fi
}

create_session

# Function to check if the session is still valid
check_session_validity() {
    local session_info=$(curl -s "http://$CONSUL_SERVER/v1/session/info/$SESSION_ID")
    if [[ "$(echo $session_info | jq -r '. | length')" == "0" ]]; then
        echo "Session $SESSION_ID is no longer valid. Creating a new one..."
        create_session
    fi
}

# Function to attempt to acquire the lock
acquire_lock() {
    check_session_validity
    LOCK_ACQUIRED=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/${LOCK_KEY}?acquire=${SESSION_ID}")
    if [[ "$LOCK_ACQUIRED" == "true" ]]; then
        echo "Lock acquired successfully by $(hostname)."
        return 0
    else
        echo "Failed to acquire lock, session may be invalid."
        return 1
    fi
}

# Function to perform leader tasks
perform_leader_tasks() {
    echo "$(hostname) is now the leader. Performing leader tasks..."
    while true; do
        echo "Leader is active..."
        sleep 5  # Simulate leader activity
    done
}

# Monitor and try to acquire the lock
monitor_and_acquire_lock() {
    while true; do
        if acquire_lock; then
            perform_leader_tasks &
            wait $!  # Wait for the leader tasks to complete before exiting
        else
            echo "Retrying to acquire lock in 5 seconds..."
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
