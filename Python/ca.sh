#!/bin/bash
set -e

CONFIG_FILE="config.yaml"

# Function to parse YAML (requires yq)
parse_config() {
  DURATION=$(yq e '.cert_duration_days' "$CONFIG_FILE")
  CA_CN=$(yq e '.ca_common_name' "$CONFIG_FILE")
  SERVER_CN=$(yq e '.server_common_name' "$CONFIG_FILE")
  SAN_LIST=$(yq e '.subject_alt_names[]' "$CONFIG_FILE")
}

generate_ca() {
  echo "[*] Generating root CA..."
  openssl genrsa -out ca.key 4096
  openssl req -x509 -new -nodes -key ca.key -sha256 -days "$DURATION" \
    -subj "/CN=$CA_CN" -out ca.crt
}

generate_server_cert() {
  echo "[*] Generating server certificate..."

  # Generate server key and CSR
  openssl genrsa -out vault.key 2048
  openssl req -new -key vault.key -subj "/CN=$SERVER_CN" -out vault.csr

  # Create SAN config
  echo "[req]" > san.cnf
  echo "distinguished_name = req_distinguished_name" >> san.cnf
  echo "req_extensions = v3_req" >> san.cnf
  echo "[req_distinguished_name]" >> san.cnf
  echo "[v3_req]" >> san.cnf
  echo "subjectAltName = @alt_names" >> san.cnf
  echo "[alt_names]" >> san.cnf

  COUNT=1
  for SAN in $SAN_LIST; do
    echo "$SAN" | grep -q "^DNS:" && echo "DNS.$COUNT=${SAN#DNS:}" >> san.cnf
    echo "$SAN" | grep -q "^IP:" && echo "IP.$COUNT=${SAN#IP:}" >> san.cnf
    ((COUNT++))
  done

  # Sign the CSR with the CA
  openssl x509 -req -in vault.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out vault.crt -days "$DURATION" -sha256 -extfile san.cnf -extensions v3_req

  rm -f vault.csr san.cnf
}

# Main
if ! command -v yq &> /dev/null; then
  echo "[!] 'yq' is required. Install via: brew install yq or apt install yq"
  exit 1
fi

parse_config
generate_ca
generate_server_cert

echo "[✔] Certificates generated:"
echo " - ca.crt, ca.key"
echo " - vault.crt, vault.key"
