#!/bin/bash

CHAIN_NAME="MQDROP"
PORT=1414
MAX_INTERVAL=20   # seconds
DURATION=120      # total run time in seconds

echo "[INFO] Starting jitter simulation for $DURATION seconds (interval max: $MAX_INTERVAL)..."

END=$((SECONDS + DURATION))
while [ $SECONDS -lt $END ]; do
    if (( RANDOM % 2 )); then
        echo "[DROP] Enabling MQ blackhole..."
        sudo iptables -t mangle -C OUTPUT -j $CHAIN_NAME 2>/dev/null || \
        sudo iptables -t mangle -A OUTPUT -j $CHAIN_NAME
    else
        echo "[PASS] Disabling MQ blackhole..."
        sudo iptables -t mangle -D OUTPUT -j $CHAIN_NAME 2>/dev/null || true
    fi
    sleep $((RANDOM % MAX_INTERVAL + 5))
done

echo "[INFO] Jitter test finished."
