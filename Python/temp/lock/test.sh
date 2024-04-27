#!/bin/bash

# Define the Consul server endpoint
CONSUL_SERVER="consul-server:8500"

# Define the session and lock key configuration
SESSION_NAME="service_leader_election"
LOCK_KEY="service/leader"
TTL="15s"  # Time-To-Live for the session

# Function to create a new session in Consul
create_session() {
    echo "Attempting to create a new session from host ${HOSTNAME}..."
    response=$(curl -s -X PUT --data "{\"Name\": \"$SESSION_NAME\", \"TTL\": \"$TTL\", \"Behavior\": \"delete\"}" "http://${CONSUL_SERVER}/v1/session/create")
    SESSION_ID=$(echo "$response" | jq -r '.ID')
    if [[ -z "$SESSION_ID" || "$SESSION_ID" == "null" ]]; then
        echo "Failed to create session, response was: $response"
        sleep 5
        create_session
    else
        echo "Session created with ID: $SESSION_ID"
    fi
}

# Function to check if the session is still valid
check_session_validity() {
    session_info=$(curl -s "http://${CONSUL_SERVER}/v1/session/info/$SESSION_ID")
    if [[ "$(echo $session_info | jq -r '. | length')" == "0" ]]; then
        echo "Session $SESSION_ID is no longer valid. Creating a new one..."
        create_session
    fi
}

# Function to acquire the lock
acquire_lock() {
    while true; do
        check_session_validity
        result=$(curl -s -X PUT --data "{\"acquire\": \"$SESSION_ID\"}" "http://${CONSUL_SERVER}/v1/kv/${LOCK_KEY}" | jq -r '.')
        if [[ "$result" == "true" ]]; then
            echo "Lock acquired successfully by $(hostname)"
            break
        else
            echo "Failed to acquire lock, retrying..."
            sleep 5
        fi
    done
}

# Function to perform leader tasks
perform_leader_tasks() {
    echo "$(hostname) is now the leader. Performing leader tasks..."
    while true; do
        echo "$(hostname): Leader is active"
        sleep 5  # Echo hostname every 5 seconds
    done
}

# Monitor and try to acquire the lock
monitor_and_acquire_lock() {
    create_session
    acquire_lock
    perform_leader_tasks
}

# Cleanup function to release the lock and destroy the session
cleanup() {
    echo "Cleaning up..."
    curl -s -X PUT "http://${CONSUL_SERVER}/v1/kv/${LOCK_KEY}?release=$SESSION_ID"
    curl -s -X PUT "http://${CONSUL_SERVER}/v1/session/destroy/$SESSION_ID"
    echo "Resources released by $(hostname)."
}

# Setup trap for cleanup on script exit
trap cleanup EXIT

# Start monitoring and lock acquisition
monitor_and_acquire_lock
