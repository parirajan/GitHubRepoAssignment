#!/bin/bash

NAMESPACE="your_namespace"
SET="your_set"
LOGFILE="/var/log/aerospike/aerospike_truncate.log"
MAX_RUNTIME_SEC=$((60 * 60))         # 1 hour
SUB_CHUNKS_PER_DAY=4                 # 6-hr slices per day
SLICE_SECONDS=$((86400 / SUB_CHUNKS_PER_DAY))
START_DAY=30                         # Start from 30 days old
END_DAY=7                            # Stop at 7 days old

# Optional: Vault/Consul integration to toggle decision
# decision="enabled" or "disabled"
# update_lut=7 (default to 7 if not found)

echo "$(date) Starting Aerospike Truncation Script" | tee -a "$LOGFILE"
START_TS=$(date +%s)

for (( d=START_DAY; d>=END_DAY; d-- )); do
  for (( s=0; s<SUB_CHUNKS_PER_DAY; s++ )); do
    NOW=$(date +%s)
    RUNTIME=$((NOW - START_TS))
    if (( RUNTIME > MAX_RUNTIME_SEC )); then
      echo "$(date) Max run window (1hr) reached. Exiting." | tee -a "$LOGFILE"
      exit 0
    fi

    # Compute LUT (nanoseconds) for the start of the slice
    OFFSET_SEC=$(( (d * 86400) - (s * SLICE_SECONDS) ))
    LUT=$(date -u -d "@$((NOW - OFFSET_SEC))" +%s%N)
    echo "$(date) Targeting LUT=$LUT (age > ${d}.${s}d)" | tee -a "$LOGFILE"

    # Get stats
    STATS=$(asadm -e "asinfo -v 'get-stats:context=namespace;id=$NAMESPACE'" 2>/dev/null)
    DEFRAG_Q=$(echo "$STATS" | grep -Po 'defrag_q=\K\d+')
    AVAIL_PCT=$(echo "$STATS" | grep -Po 'available_pct=\K\d+')
    STOP_WRITES=$(echo "$STATS" | grep -Po 'stop_writes=\K\w+')

    if [[ "$STOP_WRITES" == "true" ]] || (( DEFRAG_Q > 1000 )) || (( AVAIL_PCT < 20 )); then
      echo "$(date) Skipping: stop_writes=$STOP_WRITES, defrag_q=$DEFRAG_Q, available=$AVAIL_PCT%" | tee -a "$LOGFILE"
      sleep 60
      continue
    fi

    # Issue Truncate
    echo "$(date) Executing: truncate lut=$LUT" | tee -a "$LOGFILE"
    asadm -e "asinfo -v 'truncate:namespace=$NAMESPACE;set=$SET;lut=$LUT'" >> "$LOGFILE" 2>&1

    # Sleep between chunks
    sleep 10
  done
done

echo "$(date) Truncation script completed in $(( $(date +%s) - START_TS )) seconds." | tee -a "$LOGFILE"
