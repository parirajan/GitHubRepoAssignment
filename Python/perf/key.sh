#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

# === Prompt for output directory ===
read -rp "Enter the directory to store keystore/truststore (default: /data/keystore): " OUTPUT_DIR
OUTPUT_DIR="${OUTPUT_DIR:-/data/keystore}"
mkdir -p "$OUTPUT_DIR"
echo "Output directory: $OUTPUT_DIR"

# === Define cert and key input files ===
CERT_FILE="/etc/consul.d/admin.crt"      # Replace with actual client cert
KEY_FILE="/etc/consul.d/admin.key"       # Replace with actual private key
CA_CERT_FILE="/etc/consul.d/trust.crt"   # Replace with CA certificate

# === Define output files ===
P12_FILE="$OUTPUT_DIR/keystore.p12"
JKS_KEYSTORE="$OUTPUT_DIR/keystore.jks"
JKS_TRUSTSTORE="$OUTPUT_DIR/truststore.jks"

# === Passwords ===
STORE_PASS="changeit"   # Keystore/truststore password
KEY_ALIAS="aerospike-client"

echo ""
echo "=== [1/4] Creating PKCS12 keystore (.p12) ==="
openssl pkcs12 -export \
  -inkey "$KEY_FILE" \
  -in "$CERT_FILE" \
  -name "$KEY_ALIAS" \
  -out "$P12_FILE" \
  -passout pass:"$STORE_PASS"

echo ""
echo "=== [2/4] Converting .p12 to Java Keystore (.jks) ==="
keytool -importkeystore \
  -srckeystore "$P12_FILE" \
  -srcstoretype PKCS12 \
  -srcstorepass "$STORE_PASS" \
  -destkeystore "$JKS_KEYSTORE" \
  -deststoretype JKS \
  -deststorepass "$STORE_PASS" \
  -noprompt

echo ""
echo "=== [3/4] Creating Truststore and importing CA cert ==="
keytool -importcert \
  -alias aerospike-ca \
  -file "$CA_CERT_FILE" \
  -keystore "$JKS_TRUSTSTORE" \
  -storepass "$STORE_PASS" \
  -noprompt

echo ""
echo "=== [4/4] Verifying Keystore and Truststore ==="
echo "Keystore Contents:"
keytool -list -keystore "$JKS_KEYSTORE" -storepass "$STORE_PASS"

echo ""
echo "Truststore Contents:"
keytool -list -keystore "$JKS_TRUSTSTORE" -storepass "$STORE_PASS"

echo ""
echo "✅ Java Keystore created at:     $JKS_KEYSTORE"
echo "✅ Java Truststore created at:   $JKS_TRUSTSTORE"
