#!/bin/bash

# === CONFIGURABLE ===
NAMESPACE="your_namespace"
SET="your_set"
LOGFILE="/var/log/aerospike/aerospike_truncate.log"
MAX_RUNTIME_SEC=$((60 * 60))           # 1 hour max
SUB_CHUNKS_PER_DAY=4                   # 1-day split into 6hr chunks
SLICE_SECONDS=$((86400 / SUB_CHUNKS_PER_DAY))
START_DAY=30                           # Begin at 30 days old
END_DAY=7                              # Stop at 7 days old
DRY_RUN=true                           # Set false to execute truncation

# === LOG START ===
echo -e "\n\n$(date) Starting Aerospike Truncation Script" | tee -a "$LOGFILE"
SCRIPT_START=$(date +%s)

# === Function: Check defrag_q cluster-wide ===
check_defrag_q_threshold() {
  local ns="$1"
  local threshold=1000
  local defrag_values=()
  local total=0

  while read -r val; do
    defrag_values+=("$val")
    total=$((total + val))
  done < <(asadm -e "show statistics like defrag_q" | awk -v ns="$ns" '
    $0 ~ "Namespace "ns" Statistics" { found=1; next }
    found && /defrag_q/ {
      print $NF
      found=0
    }')

  local count=${#defrag_values[@]}
  local threshold_sum=$((threshold * count))

  for v in "${defrag_values[@]}"; do
    if (( v > threshold )); then
      echo "$(date) High defrag_q detected: $v > $threshold" | tee -a "$LOGFILE"
      return 1
    fi
  done

  if (( total > threshold_sum )); then
    echo "$(date) Cluster-wide defrag_q too high: $total > $threshold_sum" | tee -a "$LOGFILE"
    return 1
  fi

  return 0
}

# === Truncation Loop ===
for (( d=START_DAY; d>=END_DAY; d-- )); do
  for (( s=0; s<SUB_CHUNKS_PER_DAY; s++ )); do
    # Stop if runtime exceeded
    NOW=$(date +%s)
    RUNTIME=$((NOW - SCRIPT_START))
    if (( RUNTIME > MAX_RUNTIME_SEC )); then
      echo "$(date) Max runtime (1 hour) reached. Exiting." | tee -a "$LOGFILE"
      exit 0
    fi

    # Compute target LUT (Last Update Time)
    OFFSET_SEC=$(( (d * 86400) - (s * SLICE_SECONDS) ))
    LUT=$(date -u -d "@$((NOW - OFFSET_SEC))" +%s%N)
    echo "$(date) Target LUT: $LUT for age ${d}.${s} days" | tee -a "$LOGFILE"

    # Check defrag_q thresholds
    if ! check_defrag_q_threshold "$NAMESPACE"; then
      echo "$(date) Skipping this slice due to high defrag pressure" | tee -a "$LOGFILE"
      sleep 60
      continue
    fi

    # Run truncate (dry-run first)
    CMD="asinfo -v 'truncate:namespace=$NAMESPACE;set=$SET;lut=$LUT'"
    if [ "$DRY_RUN" = true ]; then
      echo "$(date) Dry Run: $CMD" | tee -a "$LOGFILE"
    else
      echo "$(date) Executing: $CMD" | tee -a "$LOGFILE"
      asadm -e "$CMD" >> "$LOGFILE" 2>&1
    fi

    sleep 10
  done
done

echo "$(date) Truncation script completed in $(( $(date +%s) - SCRIPT_START )) seconds." | tee -a "$LOGFILE"
