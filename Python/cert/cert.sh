package org.frb.fednow.consumer;

import com.ibm.mq.jms.MQConnectionFactory;
import com.ibm.msg.client.wmq.WMQConstants;
import javax.jms.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import jakarta.annotation.PostConstruct;

@Component
public class MqListener {

    @Value("${ibm.mq.queue-manager}") private String qmgr;
    @Value("${ibm.mq.channel}") private String channel;
    @Value("${ibm.mq.conn-name}") private String connName;
    @Value("${ibm.mq.request-queue}") private String queueName;
    @Value("${ibm.mq.interval-ms:2000}") private long intervalMs;

    // --- SSL config (read from application.yml)
    @Value("${ibm.mq.ssl.keyStore}") private String keyStore;
    @Value("${ibm.mq.ssl.keyStorePassword}") private String keyStorePassword;
    @Value("${ibm.mq.ssl.trustStore}") private String trustStore;
    @Value("${ibm.mq.ssl.trustStorePassword}") private String trustStorePassword;
    @Value("${ibm.mq.sslCipherSuite:TLS_AES_256_GCM_SHA384}") private String sslCipherSuite;

    @PostConstruct
    public void applySslProps() {
        System.setProperty("javax.net.ssl.keyStore", keyStore);
        System.setProperty("javax.net.ssl.keyStorePassword", keyStorePassword);
        System.setProperty("javax.net.ssl.keyStoreType", "PKCS12");
        System.setProperty("javax.net.ssl.trustStore", trustStore);
        System.setProperty("javax.net.ssl.trustStorePassword", trustStorePassword);
        System.setProperty("javax.net.ssl.trustStoreType", "PKCS12");
        System.out.println("[MQ SSL] Properties applied from application.yml");
    }

    public void startAsync() {
        System.out.println("MqListener starting thread...");
        Thread t = new Thread(this::runLoop, "mq-consumer-loop");
        t.setDaemon(false);
        t.start();
    }

    private void runLoop() {
        int attempt = 0;
        while (true) {
            MQConnectionFactory f = new MQConnectionFactory();
            try {
                f.setTransportType(WMQConstants.WMQ_CM_CLIENT);
                f.setConnectionNameList(connName);
                f.setChannel(channel);
                f.setQueueManager(qmgr);

                // --- TLS / mTLS only ---
                f.setSSLCipherSuite(sslCipherSuite);
                f.setBooleanProperty(WMQConstants.USER_AUTHENTICATION_MQCSP, false);

                Connection connection = f.createConnection(); // no user/pwd
                Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
                Queue inq = session.createQueue("queue:///" + queueName);
                MessageConsumer consumer = session.createConsumer(inq);

                connection.start();
                System.out.println("[CONSUMER] Connected to MQ; listening on " + queueName + " ...");

                attempt = 0;
                while (true) {
                    Message m = consumer.receive(intervalMs);
                    if (m == null) continue;

                    if (m instanceof TextMessage tm)
                        System.out.println("[CONSUMER] Received: " + tm.getText());
                    else
                        System.out.println("[CONSUMER] Non-text message: " + m.getClass().getSimpleName());
                }

            } catch (Exception e) {
                attempt++;
                long backoffMs = Math.min(30000, 1000L * attempt);
                System.err.println("[CONSUMER] MQ failure (attempt " + attempt + "): " + e.getMessage());
                try { Thread.sleep(backoffMs); } catch (InterruptedException ignored) {}
            }
        }
    }
}

* ========= Common MQSC template for FNUNI cluster (2 FR, 1 PR) =========

* ----- Listener -----
DEFINE LISTENER(L1414) TRPTYPE(TCP) PORT(1414) CONTROL(QMGR) REPLACE
START LISTENER(L1414)

* ----- TLS / Keystore (PKCS12) -----
ALTER QMGR KEYSTORETYPE(PKCS12)
ALTER QMGR SSLKEYR('/etc/mqm/pki/{{SELF_QM}}/qmgr') CERTLABL('qmgr-cert-{{SELF_QM}}')

* ----- Client channel with mTLS -----
DEFINE CHANNEL('DEV.APP.SVRCONN') CHLTYPE(SVRCONN) TRPTYPE(TCP) +
  SSLCIPH('TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384') +
  SSLCAUTH(REQUIRED) REPLACE

* ----- CHLAUTH cert mapping -----
ALTER QMGR CHLAUTH(ENABLED)
SET CHLAUTH('DEV.APP.SVRCONN') TYPE(SSLPEERMAP) +
  SSLPEER('CN=app-producer,OU=Apps,O=FNUNI,*') +
  USERSRC(MAP) MCAUSER('app-prod') ACTION(REPLACE)
SET CHLAUTH('DEV.APP.SVRCONN') TYPE(SSLPEERMAP) +
  SSLPEER('CN=app-consumer,OU=Apps,O=FNUNI,*') +
  USERSRC(MAP) MCAUSER('app-cons') ACTION(REPLACE)

* ----- Cluster receiver for THIS queue manager -----
DEFINE CHANNEL('FNUNI.TO.{{SELF_QM}}') CHLTYPE(CLUSRCVR) TRPTYPE(TCP) +
  CONNAME('{{SELF_HOST}}(1414)') CLUSTER('FNUNI') REPLACE

* ----- Cluster senders to seed QMs -----
DEFINE CHANNEL('FNUNI.TO.{{PEER1_QM}}') CHLTYPE(CLUSSDR) TRPTYPE(TCP) +
  CONNAME('{{PEER1_HOST}}(1414)') CLUSTER('FNUNI') REPLACE
DEFINE CHANNEL('FNUNI.TO.{{PEER2_QM}}') CHLTYPE(CLUSSDR) TRPTYPE(TCP) +
  CONNAME('{{PEER2_HOST}}(1414)') CLUSTER('FNUNI') REPLACE

* ----- Clustered queues -----
DEFINE QLOCAL('PAYMENT.REQUEST')  CLUSTER('FNUNI') DEFBIND(NOTFIXED) CLWLUSEQ(ANY) REPLACE
DEFINE QLOCAL('PAYMENT.RESPONSE') CLUSTER('FNUNI') DEFBIND(NOTFIXED) CLWLUSEQ(ANY) REPLACE

* ----- Dead letter queue -----
DEFINE QLOCAL('PAYMENT.DLQ') REPLACE
ALTER QMGR DEADQ('PAYMENT.DLQ')

* ----- Workload balancing -----
ALTER QMGR CLWLMRUC(999999999)
ALTER QMGR CLWLUSEQ(ANY)

* ----- OAM for MCAUSERs -----
SET AUTHREC PROFILE('PAYMENT.REQUEST')  OBJTYPE(QUEUE) PRINCIPAL('app-prod') AUTHADD(GET,INQ)
SET AUTHREC PROFILE('PAYMENT.RESPONSE') OBJTYPE(QUEUE) PRINCIPAL('app-prod') AUTHADD(PUT,INQ)

SET AUTHREC PROFILE('PAYMENT.REQUEST')  OBJTYPE(QUEUE) PRINCIPAL('app-cons') AUTHADD(GET,INQ)
SET AUTHREC PROFILE('PAYMENT.RESPONSE') OBJTYPE(QUEUE) PRINCIPAL('app-cons') AUTHADD(PUT,INQ)

* ----- Activate changes -----
REFRESH SECURITY TYPE(SSL)
REFRESH SECURITY TYPE(CONNAUTH)
REFRESH SECURITY TYPE(OAM)

* ----- FR/PR role appended by render script -----



#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-FNUNI}"
SELF_QM="${MQ_QMGR_NAME:-$(echo FNQM1/FNQM2/FNQM3)}"
SELF_HOST="${SELF_HOST:-$HOSTNAME}"

case "$SELF_QM" in
  FNQM1) PEER1_QM=FNQM2; PEER1_HOST=mq2; PEER2_QM=FNQM3; PEER2_HOST=mq3 ;;
  FNQM2) PEER1_QM=FNQM1; PEER1_HOST=mq1; PEER2_QM=FNQM3; PEER2_HOST=mq3 ;;
  FNQM3) PEER1_QM=FNQM1; PEER1_HOST=mq1; PEER2_QM=FNQM2; PEER2_HOST=mq2 ;;
  *) echo "Unknown SELF_QM='$SELF_QM'"; exit 1 ;;
esac

ROLE="${ROLE:-PR}" # set FR on two nodes in compose via env

TPL="/opt/common.mqsc.tpl"
OUT="/etc/mqm/auto.mqsc"

# Render placeholders
sed -e "s/{{SELF_QM}}/${SELF_QM}/g" \
    -e "s/{{SELF_HOST}}/${SELF_HOST}/g" \
    -e "s/{{PEER1_QM}}/${PEER1_QM}/g" \
    -e "s/{{PEER1_HOST}}/${PEER1_HOST}/g" \
    -e "s/{{PEER2_QM}}/${PEER2_QM}/g" \
    -e "s/{{PEER2_HOST}}/${PEER2_HOST}/g" \
    "$TPL" > "$OUT"

# Append FR/PR role
if [ "$ROLE" = "FR" ]; then
  {
    echo "ALTER QMGR REPOS('${CLUSTER_NAME}')"
    echo "ALTER QMGR REPOSNL('${CLUSTER_NAME}')"
  } >> "$OUT"
else
  {
    echo "ALTER QMGR REPOS('')"
    echo "ALTER QMGR REPOSNL('')"
  } >> "$OUT"
fi

echo "Rendered MQSC for $SELF_QM ($SELF_HOST) ROLE=$ROLE -> $OUT"


#!/usr/bin/env bash
set -euo pipefail

CERT_FLAG="${CERT_FLAG:-/etc/mqm/pki/.done}"   # shared volume flag from prepare-certs
HOSTS="${HOSTS:-mq1 mq2 mq3}"                  # space-separated
PORT="${PORT:-1414}"
SLEEP="${SLEEP:-2}"
MAX_WAIT="${MAX_WAIT:-300}"                    # seconds (0 = infinite)

have_nc()      { command -v nc >/dev/null 2>&1; }
have_openssl() { command -v openssl >/dev/null 2>&1; }

echo "[wait] waiting for cert flag $CERT_FLAG ..."
start_ts=$(date +%s)
while [ ! -f "$CERT_FLAG" ]; do
  now=$(date +%s); (( MAX_WAIT == 0 || now - start_ts < MAX_WAIT )) || { echo "[wait] timeout waiting for certs"; exit 1; }
  sleep "$SLEEP"
done
echo "[wait] certs ready."

for h in $HOSTS; do
  echo "[wait] waiting for TCP $h:$PORT ..."
  start_ts=$(date +%s)
  while :; do
    if have_nc && nc -z "$h" "$PORT" 2>/dev/null; then
      echo "[wait] $h:$PORT open (via nc)."
      break
    fi

    # /dev/tcp requires bash — we’re in bash here
    if exec 3<>"/dev/tcp/$h/$PORT" 2>/dev/null; then
      exec 3>&- 3<&-
      echo "[wait] $h:$PORT open (via /dev/tcp)."
      break
    fi

    # Optional TLS probe if openssl exists
    if have_openssl && echo | openssl s_client -connect "$h:$PORT" -servername "$h" -brief >/dev/null 2>&1; then
      echo "[wait] $h:$PORT TLS OK (via openssl)."
      break
    fi

    now=$(date +%s); (( MAX_WAIT == 0 || now - start_ts < MAX_WAIT )) || { echo "[wait] timeout waiting for $h:$PORT"; exit 1; }
    sleep "$SLEEP"
  done
done

echo "[wait] all MQ endpoints are up."
exec "$@"





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
