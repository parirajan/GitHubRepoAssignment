#!/bin/bash

# Endpoint for the Consul server
CONSUL_SERVER="consul-server:8500"

# Create a session with TTL (for lock expiration on failure)
SESSION_DATA='{"Name": "myServiceLock", "TTL": "15s", "Behavior": "delete"}'
SESSION_ID=$(curl -s -X PUT -d "$SESSION_DATA" "http://$CONSUL_SERVER/v1/session/create" | jq -r '.ID')
echo "Session created with ID: $SESSION_ID"

# Key to lock on
LOCK_KEY="service/lock"

# Try to acquire the lock
function try_acquire_lock {
    LOCK_ACQUIRED=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/${LOCK_KEY}?acquire=${SESSION_ID}" | jq -r '.')
    echo "$LOCK_ACQUIRED"
}

# Renew the session periodically
function renew_session {
    while true; do
        curl -s -X PUT "http://$CONSUL_SERVER/v1/session/renew/${SESSION_ID}" > /dev/null
        sleep 10  # Sleep less than the TTL to ensure the session keeps alive
    done
}

# Function to perform leader tasks
function perform_leader_tasks {
    echo "This node is the leader. Running tasks..."
    # Place leader-specific workload here
    while true; do
        echo "Performing leader tasks..."
        sleep 5  # Simulate work
    done
}

# Monitor the lock status and attempt to acquire it if free
function monitor_lock {
    while true; do
        if [ "$(try_acquire_lock)" = "true" ]; then
            echo "Acquired lock, becoming the leader."
            perform_leader_tasks &
            leader_task_pid=$!
            renew_session &
            wait $leader_task_pid  # Wait for the leader task to finish
            exit 0
        fi
        echo "Lock is not available. Retrying..."
        sleep 5
    done
}

# Start monitoring the lock
monitor_lock
