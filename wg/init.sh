#!/bin/bash

# Ensure 'wg' (WireGuard) command is available
if ! command -v wg &> /dev/null; then
    echo "wg could not be found, installing wireguard-tools..."
    sudo dnf install wireguard-tools -y
fi

# Ensure Vault is installed
if ! command -v vault &> /dev/null; then
    echo "Vault CLI could not be found, installing Vault..."
    sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
    sudo dnf install vault -y
fi

# Define where to store the keys locally before copying to Vault
WG_KEY_DIR="/tmp/wgkeys"
mkdir -p "${WG_KEY_DIR}"

# Generate WireGuard private and public key
wg genkey | tee "${WG_KEY_DIR}/privatekey" | wg pubkey > "${WG_KEY_DIR}/publickey"

# Read generated keys
WG_PRIVATE_KEY=$(< "${WG_KEY_DIR}/privatekey")
WG_PUBLIC_KEY=$(< "${WG_KEY_DIR}/publickey")

# Vault path where to store the keys
# Adjust the path according to your Vault setup
VAULT_PATH="secret/data/wireguard"

# Ensure you're logged in to Vault or have a valid token set
# This part might need adjustment based on your auth method
if ! vault token lookup &> /dev/null; then
    echo "Vault authentication failed. Please ensure you're logged in to Vault."
    exit 1
fi

# Store the keys in Vault
vault kv put "${VAULT_PATH}" privatekey="${WG_PRIVATE_KEY}" publickey="${WG_PUBLIC_KEY}"

# Optional: Verify keys are stored
echo "Keys stored in Vault. Verifying..."
vault kv get "${VAULT_PATH}"

# Clean up local keys if desired
rm -rf "${WG_KEY_DIR}"

echo "WireGuard keys generated and stored in Vault successfully."
