* =========================================================
* Common MQSC template for FNUNI cluster (2 FR, 1 PR)
* =========================================================

* ----- Listener -----
DEFINE LISTENER(L1414) TRPTYPE(TCP) PORT(1414) CONTROL(QMGR) REPLACE
START LISTENER(L1414)

* ----- Application channel (DEV) -----
* DEV convenience: run channel as 'app' MCAUSER and (optionally) relax CHLAUTH.
DEFINE CHANNEL('DEV.APP.SVRCONN') CHLTYPE(SVRCONN) TRPTYPE(TCP) +
  MCAUSER('{{APP_PRINCIPAL}}') REPLACE
ALTER QMGR CHLAUTH(DISABLED)  * <-- DEV ONLY. REMOVE FOR PROD.

* ----- Cluster receiver for THIS queue manager -----
DEFINE CHANNEL('FNUNI.TO.{{SELF_QM}}') CHLTYPE(CLUSRCVR) TRPTYPE(TCP) +
  CONNAME('{{SELF_HOST}}(1414)') CLUSTER('FNUNI') REPLACE

* ----- Cluster senders to seed QMs -----
DEFINE CHANNEL('FNUNI.TO.{{PEER1_QM}}') CHLTYPE(CLUSSDR) TRPTYPE(TCP) +
  CONNAME('{{PEER1_HOST}}(1414)') CLUSTER('FNUNI') REPLACE
DEFINE CHANNEL('FNUNI.TO.{{PEER2_QM}}') CHLTYPE(CLUSSDR) TRPTYPE(TCP) +
  CONNAME('{{PEER2_HOST}}(1414)') CLUSTER('FNUNI') REPLACE

* ----- Clustered queues -----
DEFINE QLOCAL('{{QUEUE_PREFIX}}.REQUEST')  CLUSTER('FNUNI') +
  DEFBIND(NOTFIXED) CLWLUSEQ(ANY) REPLACE
DEFINE QLOCAL('{{QUEUE_PREFIX}}.RESPONSE') CLUSTER('FNUNI') +
  DEFBIND(NOTFIXED) CLWLUSEQ(ANY) REPLACE

* ----- Dead letter queue -----
DEFINE QLOCAL('{{QUEUE_PREFIX}}.DLQ') REPLACE
ALTER  QMGR  DEADQ('{{QUEUE_PREFIX}}.DLQ')

* ----- Workload balancing -----
ALTER QMGR CLWLMRUC(999999999)
ALTER QMGR CLWLUSEQ(ANY)

* ----- App authorizations (grant rights to MCAUSER) -----
* Put/inq on REQUEST; get/inq/browse on RESPONSE. Adjust to your needs.
SET AUTHREC PROFILE('{{QUEUE_PREFIX}}.REQUEST')  OBJTYPE(QUEUE) +
  PRINCIPAL('{{APP_PRINCIPAL}}') AUTHADD(PUT,INQ)
SET AUTHREC PROFILE('{{QUEUE_PREFIX}}.RESPONSE') OBJTYPE(QUEUE) +
  PRINCIPAL('{{APP_PRINCIPAL}}') AUTHADD(GET,INQ,BROWSE)

* Optionally grant DLQ browse/inq for ops tools
* SET AUTHREC PROFILE('{{QUEUE_PREFIX}}.DLQ') OBJTYPE(QUEUE) +
*   PRINCIPAL('{{APP_PRINCIPAL}}') AUTHADD(BROWSE,INQ)

* Ensure security changes are live
REFRESH SECURITY TYPE(AUTHSERV)

* ----- FR/PR role is appended by render-mqsc.sh -----
