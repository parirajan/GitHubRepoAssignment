#!/bin/bash

# Exit on error
set -e

# Prompt for output directory (or use default)
read -p "Enter the directory where you want to save the keystore/truststore (default: /tmp/keystore): " OUTPUT_DIR
OUTPUT_DIR=${OUTPUT_DIR:-/tmp/keystore}

# Ensure the directory exists
mkdir -p "$OUTPUT_DIR"
echo "Keystore and truststore will be created in: $OUTPUT_DIR"

# Define file paths
CERT_FILE="certificate.pem"        # Replace with actual certificate file
KEY_FILE="private-key.pem"         # Replace with actual private key file
CA_CERT_FILE="ca-certificate.pem"  # Replace with actual CA certificate file

P12_FILE="$OUTPUT_DIR/keystore.p12"
JKS_KEYSTORE="$OUTPUT_DIR/keystore.jks"
JKS_TRUSTSTORE="$OUTPUT_DIR/truststore.jks"

# Define store passwords
STORE_PASS="changeit"   # Change this for production use
KEY_PASS="changeit"     # Change this for production use

# Convert the private key and certificate to PKCS12 format
echo "Creating PKCS12 file..."
openssl pkcs12 -export -inkey "$KEY_FILE" -in "$CERT_FILE" -name mykey -out "$P12_FILE" -password pass:$STORE_PASS

# Convert PKCS12 to Java KeyStore (JKS)
echo "Importing PKCS12 into Java KeyStore..."
keytool -importkeystore -srckeystore "$P12_FILE" -srcstoretype PKCS12 \
  -destkeystore "$JKS_KEYSTORE" -deststoretype JKS \
  -srcstorepass "$STORE_PASS" -deststorepass "$STORE_PASS" -noprompt

# Import the CA certificate into a new TrustStore
echo "Creating Java TrustStore and importing CA certificate..."
keytool -import -trustcacerts -alias myca -file "$CA_CERT_FILE" \
  -keystore "$JKS_TRUSTSTORE" -storepass "$STORE_PASS" -noprompt

# Print generated file locations
echo "✅ Java KeyStore created: $JKS_KEYSTORE"
echo "✅ Java TrustStore created: $JKS_TRUSTSTORE"
