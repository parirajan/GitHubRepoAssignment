# Dockerfile.prepare-certs
FROM registry.access.redhat.com/ubi9/ubi-minimal

# microdnf is available on ubi-minimal; on full UBI9 use `dnf -y install ...`
RUN microdnf -y install openssl java-17-openjdk-headless ca-certificates \
 && microdnf -y clean all

# Make sure the trust bundle exists/enabled (not strictly required for our PKI)
RUN update-ca-trust force-enable || true

WORKDIR /scripts
COPY generate-certs.sh /scripts/generate-certs.sh
RUN chmod +x /scripts/generate-certs.sh

# OUT is where we will write the artifacts (mounted named volume)
ENV OUT=/out
ENTRYPOINT ["/scripts/generate-certs.sh"]


version: "3.9"

volumes:
  pki-data: {}

services:
  prepare-certs:
    build:
      context: .
      dockerfile: Dockerfile.prepare-certs
    environment:
      OUT: /out
      QM_NAMES: "FNQM1 FNQM2 FNQM3"
      CLIENT_CNS: "app-prod app-batch"
      CA_KEY_BITS: "8192"
      QM_KEY_BITS: "4096"
      CLIENT_KEY_BITS: "4096"
      P12_PASS: "changeit"
      TRUST_PASS: "changeit"
    volumes:
      - pki-data:/out:Z
    restart: "no"

  mq1:
    image: ibmcom/mq:9.3.5.0-r1
    depends_on: [prepare-certs]
    environment:
      - LICENSE=accept
      - MQ_QMGR_NAME=FNQM1
    volumes:
      - pki-data:/etc/mqm/pki:ro,Z

  mq2:
    image: ibmcom/mq:9.3.5.0-r1
    depends_on: [prepare-certs]
    environment:
      - LICENSE=accept
      - MQ_QMGR_NAME=FNQM2
    volumes:
      - pki-data:/etc/mqm/pki:ro,Z

  mq3:
    image: ibmcom/mq:9.3.5.0-r1
    depends_on: [prepare-certs]
    environment:
      - LICENSE=accept
      - MQ_QMGR_NAME=FNQM3
    volumes:
      - pki-data:/etc/mqm/pki:ro,Z

  consumer:
    image: your/mq-consumer:latest
    depends_on: [prepare-certs]
    volumes:
      - pki-data:/etc/mqm/pki:ro,Z
      - ./application.yml:/config/application.yml:ro,Z
    environment:
      - SPRING_CONFIG_LOCATION=file:/config/application.yml




#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-/out}"
QM_NAMES="${QM_NAMES:-FNQM1 FNQM2 FNQM3}"
CLIENT_CNS="${CLIENT_CNS:-app-prod}"
CA_KEY_BITS="${CA_KEY_BITS:-8192}"
QM_KEY_BITS="${QM_KEY_BITS:-4096}"
CLIENT_KEY_BITS="${CLIENT_KEY_BITS:-4096}"
ORG="${ORG:-FNUNI}"
COUNTRY="${COUNTRY:-US}"
QM_OU="${QM_OU:-MQ}"
CLIENT_OU="${CLIENT_OU:-Apps}"
CA_SUBJ="${CA_SUBJ:-/C=${COUNTRY}/O=${ORG}/OU=CA/CN=${ORG}-LOCAL-CA}"
P12_PASS="${P12_PASS:-changeit}"
TRUST_PASS="${TRUST_PASS:-changeit}"

mkdir -p "$OUT/ca" "$OUT/trust" "$OUT/qmgr" "$OUT/client"

echo ">>> Generating CA (${CA_KEY_BITS}-bit)"
openssl genrsa -out "$OUT/ca/ca.key" "$CA_KEY_BITS"
openssl req -x509 -new -key "$OUT/ca/ca.key" -sha256 -days 3650 \
  -subj "$CA_SUBJ" -out "$OUT/ca/ca.crt"

# Java PKCS12 truststore for clients
if command -v keytool >/dev/null 2>&1; then
  rm -f "$OUT/trust/trust.p12"
  keytool -importcert -noprompt \
    -alias local-ca \
    -file "$OUT/ca/ca.crt" \
    -keystore "$OUT/trust/trust.p12" -storetype PKCS12 -storepass "$TRUST_PASS"
  echo ">>> Wrote JVM truststore $OUT/trust/trust.p12"
else
  echo ">>> keytool not found; skipping trust.p12 (clients can use ca.crt)"
fi

# Per-QM server certs
for QM in $QM_NAMES; do
  QM_DIR="$OUT/qmgr/$QM"
  mkdir -p "$QM_DIR"
  echo ">>> Generating server key/cert for $QM (${QM_KEY_BITS}-bit)"
  openssl genrsa -out "$QM_DIR/qmgr.key" "$QM_KEY_BITS"
  openssl req -new -key "$QM_DIR/qmgr.key" \
    -subj "/C=$COUNTRY/O=$ORG/OU=$QM_OU/CN=$QM" \
    -out "$QM_DIR/qmgr.csr"
  openssl x509 -req -in "$QM_DIR/qmgr.csr" -CA "$OUT/ca/ca.crt" -CAkey "$OUT/ca/ca.key" \
    -CAcreateserial -out "$QM_DIR/qmgr.crt" -days 1825 -sha256

  LABEL="qmgr-cert-$QM"
  openssl pkcs12 -export \
    -inkey "$QM_DIR/qmgr.key" \
    -in "$QM_DIR/qmgr.crt" \
    -certfile "$OUT/ca/ca.crt" \
    -name "$LABEL" \
    -out "$QM_DIR/qmgr.p12" \
    -password pass:"$P12_PASS"
  echo ">>> $QM: PKCS12 ready -> $QM_DIR/qmgr.p12 (label=$LABEL)"
done

# Per-client certs
for CN in $CLIENT_CNS; do
  C_DIR="$OUT/client/$CN"
  mkdir -p "$C_DIR"
  echo ">>> Generating client key/cert CN=$CN (${CLIENT_KEY_BITS}-bit)"
  openssl genrsa -out "$C_DIR/client.key" "$CLIENT_KEY_BITS"
  openssl req -new -key "$C_DIR/client.key" \
    -subj "/C=$COUNTRY/O=$ORG/OU=$CLIENT_OU/CN=$CN" \
    -out "$C_DIR/client.csr"
  openssl x509 -req -in "$C_DIR/client.csr" -CA "$OUT/ca/ca.crt" -CAkey "$OUT/ca/ca.key" \
    -CAcreateserial -out "$C_DIR/client.crt" -days 1825 -sha256

  openssl pkcs12 -export \
    -inkey "$C_DIR/client.key" \
    -in "$C_DIR/client.crt" \
    -certfile "$OUT/ca/ca.crt" \
    -name "client-cert-$CN" \
    -out "$C_DIR/client.p12" \
    -password pass:"$P12_PASS"

  # Convenience: copy JVM truststore next to each client set
  [ -f "$OUT/trust/trust.p12" ] && cp "$OUT/trust/trust.p12" "$C_DIR/trust.p12" || true
  echo ">>> client CN=$CN ready -> $C_DIR"
done

echo ">>> All certs generated under $OUT"
