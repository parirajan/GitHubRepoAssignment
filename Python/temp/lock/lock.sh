#!/bin/bash

# Endpoint for the Consul server
CONSUL_SERVER="consul-server:8500"

# Load the session ID
SESSION_ID=$(cat /tmp/session_id)
LOCK_KEY="my-service/lock"
LOCK_DATA="Attempted lock by $(hostname)"

# Function to perform leader-specific tasks
execute_leader_tasks() {
    echo "Running tasks as the leader..."
    echo "Hostname of the leader: $(hostname)"
    # Additional leader tasks can be placed here
}

# Try to acquire the lock
LOCK_ACQUIRED=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/$LOCK_KEY?acquire=$SESSION_ID" -d "$LOCK_DATA" | jq -r '.')

if [ "$LOCK_ACQUIRED" = "true" ]; then
    echo "$(date): Lock successfully acquired. $(hostname) is now the leader."
    execute_leader_tasks
else
    echo "$(date): Failed to acquire lock. $(hostname) continues as a follower."
fi
