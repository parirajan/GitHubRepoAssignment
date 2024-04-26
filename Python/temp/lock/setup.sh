#!/bin/bash

# Endpoint for the Consul server
CONSUL_SERVER="consul-server:8500"

# Create a session with TTL
SESSION_DATA='{"Name": "myServiceLock", "TTL": "30s"}'
SESSION_ID=$(curl -s -X PUT -d "$SESSION_DATA" "http://$CONSUL_SERVER/v1/session/create" | jq -r '.ID')
echo $SESSION_ID > /tmp/session_id  # Save session ID for use in the handler script
echo "Session created with ID: $SESSION_ID"

# Function to renew the session periodically
renew_session() {
    while true; do
        echo "Renewing session..."
        curl -s -X PUT "http://$CONSUL_SERVER/v1/session/renew/$SESSION_ID" > /dev/null
        if [ $? -ne 0 ]; then
            echo "Session renewal failed, trying to recreate session..."
            SESSION_ID=$(curl -s -X PUT -d "$SESSION_DATA" "http://$CONSUL_SERVER/v1/session/create" | jq -r '.ID')
            echo $SESSION_ID > /tmp/session_id
            echo "New session created with ID: $SESSION_ID"
        fi
        sleep 20  # Renew session every 20 seconds, must be less than TTL
    done
}

# Function to clean up on script exit
cleanup() {
    echo "Cleaning up..."
    # Release the lock
    LOCK_KEY="my-service/lock"
    LOCK_DATA="Releasing lock held by $(hostname)"
    curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/$LOCK_KEY?release=$SESSION_ID" -d "$LOCK_DATA"

    # Destroy the session
    curl -s -X PUT "http://$CONSUL_SERVER/v1/session/destroy/$SESSION_ID"
    echo "Session and lock released."

    exit 0
}

# Trap script exit for cleanup
trap cleanup EXIT

# Start session renewal in the background
renew_session &

# Initial attempt to acquire the lock
chmod +x handle_lock_change.sh
./handle_lock_change.sh

# Start a watch on the key
consul watch -type=key -key=my-service/lock ./handle_lock_change.sh
