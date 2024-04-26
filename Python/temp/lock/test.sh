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
    LOCK_ACQUIRED=$(curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/${LOCK_KEY}?acquire=${SESSION_ID}" -d "Locked by $(hostname)")
    echo "$LOCK_ACQUIRED"
}

# Renew the session periodically
function renew_session {
    while true; do
        curl -s -X PUT "http://$CONSUL_SERVER/v1/session/renew/${SESSION_ID}"
        sleep 10
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

# Attempt to acquire the lock immediately
if [ "$(try_acquire_lock)" = "true" ]; then
    perform_leader_tasks &
    leader_task_pid=$!
    renew_session &
else
    echo "This node is a follower. Monitoring the lock..."
    while true; do
        if [ "$(try_acquire_lock)" = "true" ]; then
            perform_leader_tasks &
            leader_task_pid=$!
            renew_session &
            break
        fi
        echo "Still a follower..."
        sleep 5
    done
fi

# Cleanup function to ensure lock release and session destruction
function cleanup {
    kill $leader_task_pid
    curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/${LOCK_KEY}?release=${SESSION_ID}"
    curl -s -X PUT "http://$CONSUL_SERVER/v1/session/destroy/${SESSION_ID}"
    exit 0
}

trap cleanup EXIT
