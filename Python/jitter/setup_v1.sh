#!/bin/bash

# === mq_blackhole_setup.sh ===
# Set up routing + marking only for one target MQ IP in a cluster

# Configurable Variables
TABLE_ID=99
TABLE_NAME="mq_blackhole"
PORT=1414
CHAIN_NAME="MQDROP"
MQ_TARGET_IP="10.0.1.102"  # Change this to the target MQ node IP to simulate failure

# Step 1: Add custom routing table (if not exists)
grep -q "$TABLE_NAME" /etc/iproute2/rt_tables || echo "$TABLE_ID $TABLE_NAME" | sudo tee -a /etc/iproute2/rt_tables

# Step 2: Add blackhole route and ip rule
sudo ip route add blackhole 0.0.0.0/0 table $TABLE_NAME 2>/dev/null || true
sudo ip rule add fwmark $TABLE_ID table $TABLE_NAME 2>/dev/null || true

# Step 3: Create custom mangle chain
sudo iptables -t mangle -N $CHAIN_NAME 2>/dev/null || true

# Step 4: Add MARK rule targeting specific MQ server IP
sudo iptables -t mangle -C $CHAIN_NAME -p tcp -d $MQ_TARGET_IP --dport $PORT -j MARK --set-mark $TABLE_ID 2>/dev/null || \
sudo iptables -t mangle -A $CHAIN_NAME -p tcp -d $MQ_TARGET_IP --dport $PORT -j MARK --set-mark $TABLE_ID

# Step 5: Hook the chain into OUTPUT (if not already hooked)
sudo iptables -t mangle -C OUTPUT -j $CHAIN_NAME 2>/dev/null || \
sudo iptables -t mangle -A OUTPUT -j $CHAIN_NAME

echo "[OK] MQ blackhole simulation setup complete for $MQ_TARGET_IP."
