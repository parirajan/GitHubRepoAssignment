#!/bin/sh
set -eux

OUT=/out
mkdir -p $OUT/ca $OUT/qmgr $OUT/client

# ---- 1. Create CA ----
openssl genrsa -out $OUT/ca/ca.key 4096
openssl req -x509 -new -key $OUT/ca/ca.key -sha256 -days 3650 \
  -subj "/C=US/O=FNUNI/OU=CA/CN=FNUNI-CA" -out $OUT/ca/ca.crt

# ---- 2. QM server cert ----
openssl genrsa -out $OUT/qmgr/qmgr.key 2048
openssl req -new -key $OUT/qmgr/qmgr.key \
  -subj "/C=US/O=FNUNI/OU=MQ/CN=FNQM1" -out $OUT/qmgr/qmgr.csr
openssl x509 -req -in $OUT/qmgr/qmgr.csr -CA $OUT/ca/ca.crt -CAkey $OUT/ca/ca.key \
  -CAcreateserial -out $OUT/qmgr/qmgr.crt -days 1825 -sha256
openssl pkcs12 -export -inkey $OUT/qmgr/qmgr.key -in $OUT/qmgr/qmgr.crt \
  -certfile $OUT/ca/ca.crt -out $OUT/qmgr/qmgr.p12 -password pass:changeit

# ---- 3. Client cert ----
openssl genrsa -out $OUT/client/client.key 2048
openssl req -new -key $OUT/client/client.key \
  -subj "/C=US/O=FNUNI/OU=Apps/CN=app-prod" -out $OUT/client/client.csr
openssl x509 -req -in $OUT/client/client.csr -CA $OUT/ca/ca.crt -CAkey $OUT/ca/ca.key \
  -CAcreateserial -out $OUT/client/client.crt -days 1825 -sha256
openssl pkcs12 -export -inkey $OUT/client/client.key -in $OUT/client/client.crt \
  -certfile $OUT/ca/ca.crt -out $OUT/client/client.p12 -password pass:changeit
