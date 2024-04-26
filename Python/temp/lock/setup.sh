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
    # Release the lock associated with the session, don't delete the key
    if curl -s -X PUT "http://$CONSUL_SERVER/v1/kv/$LOCK_KEY?release=$SESSION_ID" -d "$LOCK_DATA"; then
        echo "Lock released."
    else
        echo "Failed to release lock."
    fi

    # Destroy the session
    if curl -s -X PUT "http://$CONSUL_SERVER/v1/session/destroy/$SESSION_ID"; then
        echo "Session destroyed."
    else
        echo "Failed to destroy session."
    fi

    exit 0
}

# Trap script exit for cleanup
trap cleanup EXIT

# Start session renewal in the background
renew_session &


# Use consul watch only if the agent is configured and running
# Initial attempt to acquire the lock
#chmod +x handle_lock_change.sh
#./handle_lock_change.sh

# Start a watch on the key
#consul watch -type=key -key=my-service/lock ./handle_lock_change.sh

# Polling loop to check key status and attempt to acquire lock
while true; do
    echo "Checking lock status..."
    LOCK_STATUS=$(curl -s -w "%{http_code}" -o temp.txt "http://$CONSUL_SERVER/v1/kv/$LOCK_KEY?raw")
    HTTP_CODE=$(tail -n1 temp.txt)
    LOCK_STATUS=$(head -n -1 temp.txt)
    if [ "$HTTP_CODE" != "200" ]; then
        echo "Failed to retrieve key with HTTP status: $HTTP_CODE"
        # Handle error or retry
    elif [[ -z "$LOCK_STATUS" ]]; then
        echo "No lock found or lock is available."
        ./handle_lock_change.sh
    else
        # Process with jq as before
        LOCK_STATUS=$(echo "$LOCK_STATUS" | jq -r '.')
        if [ "$LOCK_STATUS" == "null" ]; then
            echo "Lock is available. Attempting to acquire..."
            ./handle_lock_change.sh
        fi
    fi
    sleep 10  # Check every 10 seconds
done
