#!/bin/bash

TABLE_ID=99
TABLE_NAME="mq_blackhole"
PORT=1414
CHAIN_NAME="MQDROP"

echo "[CLEANUP] Removing MQ blackhole simulation setup..."

# Remove chain hook
sudo iptables -t mangle -D OUTPUT -j $CHAIN_NAME 2>/dev/null || true

# Flush and delete custom chain
sudo iptables -t mangle -F $CHAIN_NAME 2>/dev/null || true
sudo iptables -t mangle -X $CHAIN_NAME 2>/dev/null || true

# Remove ip rule and flush routing table
sudo ip rule del fwmark $TABLE_ID table $TABLE_NAME 2>/dev/null || true
sudo ip route flush table $TABLE_NAME 2>/dev/null || true

# Remove from rt_tables
sudo sed -i "/^$TABLE_ID[[:space:]]\+$TABLE_NAME$/d" /etc/iproute2/rt_tables

echo "[OK] Cleanup complete."
