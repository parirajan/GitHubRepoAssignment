#!/bin/sh
set -euo pipefail

# ===== Config via env (with sensible defaults) =====
OUT=${OUT:-/out}

# Space-separated lists
QM_NAMES=${QM_NAMES:-"FNQM1 FNQM2 FNQM3"}
CLIENT_CNS=${CLIENT_CNS:-"app-prod"}

# Key sizes (you can set 8192/4096 etc.)
CA_KEY_BITS=${CA_KEY_BITS:-8192}
QM_KEY_BITS=${QM_KEY_BITS:-4096}
CLIENT_KEY_BITS=${CLIENT_KEY_BITS:-4096}

# Distinguished Name stems
CA_SUBJ=${CA_SUBJ:-"/C=US/O=FNUNI/OU=CA/CN=FNUNI-LOCAL-CA"}
QM_OU=${QM_OU:-"MQ"}
CLIENT_OU=${CLIENT_OU:-"Apps"}
ORG=${ORG:-"FNUNI"}
COUNTRY=${COUNTRY:-"US"}

# Passwords
P12_PASS=${P12_PASS:-changeit}
TRUST_PASS=${TRUST_PASS:-changeit}

# Optional: install keytool if we want to produce a Java PKCS12 truststore
# (Assumes Alpine base; adjust if different)
if command -v apk >/dev/null 2>&1; then
  apk add --no-cache openssl openjdk17-jre-headless >/dev/null
fi

mkdir -p "$OUT/ca" "$OUT/trust"
echo ">>> Generating CA ($CA_KEY_BITS-bit) ..."
openssl genrsa -out "$OUT/ca/ca.key" "$CA_KEY_BITS"
openssl req -x509 -new -key "$OUT/ca/ca.key" -sha256 -days 3650 \
  -subj "$CA_SUBJ" -out "$OUT/ca/ca.crt"

# Build a Java PKCS12 truststore containing this CA (for clients)
if command -v keytool >/dev/null 2>&1; then
  rm -f "$OUT/trust/trust.p12"
  keytool -importcert -noprompt \
    -alias local-ca \
    -file "$OUT/ca/ca.crt" \
    -keystore "$OUT/trust/trust.p12" -storetype PKCS12 -storepass "$TRUST_PASS"
  echo ">>> Wrote Java truststore: $OUT/trust/trust.p12"
else
  echo ">>> keytool not found, skipping trust.p12 (clients can import $OUT/ca/ca.crt themselves)."
fi

# ===== Per-QM server certs =====
for QM in $QM_NAMES; do
  QM_DIR="$OUT/qmgr/$QM"
  mkdir -p "$QM_DIR"
  echo ">>> Generating server key/cert for $QM ($QM_KEY_BITS-bit) ..."
  openssl genrsa -out "$QM_DIR/qmgr.key" "$QM_KEY_BITS"
  openssl req -new -key "$QM_DIR/qmgr.key" \
    -subj "/C=$COUNTRY/O=$ORG/OU=$QM_OU/CN=$QM" \
    -out "$QM_DIR/qmgr.csr"
  openssl x509 -req -in "$QM_DIR/qmgr.csr" -CA "$OUT/ca/ca.crt" -CAkey "$OUT/ca/ca.key" \
    -CAcreateserial -out "$QM_DIR/qmgr.crt" -days 1825 -sha256

  # Bundle as PKCS12 for MQ (include CA so MQ trusts client chain)
  # Label must match what you'll put in CERTLABL for that QM
  LABEL="qmgr-cert-$QM"
  openssl pkcs12 -export \
    -inkey "$QM_DIR/qmgr.key" \
    -in "$QM_DIR/qmgr.crt" \
    -certfile "$OUT/ca/ca.crt" \
    -name "$LABEL" \
    -out "$QM_DIR/qmgr.p12" \
    -password pass:"$P12_PASS"

  echo ">>> $QM done -> $QM_DIR (label: $LABEL)"
done

# ===== Per-client certs =====
for CN in $CLIENT_CNS; do
  C_DIR="$OUT/client/$CN"
  mkdir -p "$C_DIR"
  echo ">>> Generating client key/cert for CN=$CN ($CLIENT_KEY_BITS-bit) ..."
  openssl genrsa -out "$C_DIR/client.key" "$CLIENT_KEY_BITS"
  openssl req -new -key "$C_DIR/client.key" \
    -subj "/C=$COUNTRY/O=$ORG/OU=$CLIENT_OU/CN=$CN" \
    -out "$C_DIR/client.csr"
  openssl x509 -req -in "$C_DIR/client.csr" -CA "$OUT/ca/ca.crt" -CAkey "$OUT/ca/ca.key" \
    -CAcreateserial -out "$C_DIR/client.crt" -days 1825 -sha256

  # Client PKCS12 (for javax.net.ssl.keyStore)
  openssl pkcs12 -export \
    -inkey "$C_DIR/client.key" \
    -in "$C_DIR/client.crt" \
    -certfile "$OUT/ca/ca.crt" \
    -name "client-cert-$CN" \
    -out "$C_DIR/client.p12" \
    -password pass:"$P12_PASS"

  # Optionally copy the trust.p12 alongside client assets for convenience
  if [ -f "$OUT/trust/trust.p12" ]; then
    cp "$OUT/trust/trust.p12" "$C_DIR/trust.p12"
  fi

  echo ">>> client CN=$CN done -> $C_DIR"
done

echo ">>> All certs generated under $OUT"
