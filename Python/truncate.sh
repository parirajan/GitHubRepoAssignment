#!/bin/bash

# === CONFIG ===
NAMESPACE="your_namespace"
SET="your_set"
LOGFILE="/var/log/aerospike/truncate_log.log"
LAST_RUN_FILE="/var/log/aerospike/truncate_last_day.txt"
MAX_RUNTIME_SEC=$((60 * 60))
SUB_CHUNKS_PER_DAY=4
SLICE_SECONDS=$((86400 / SUB_CHUNKS_PER_DAY))
END_DAY=7
DRY_RUN=true
CHECK_INTERVAL=60  # Adjustable sleep window for counter delta capture

SCRIPT_START=$(date +%s)

# Load last successful START_DAY from file or default to 30
if [ -f "$LAST_RUN_FILE" ]; then
  START_DAY=$(cat "$LAST_RUN_FILE")
else
  START_DAY=30
fi

log_plain() {
  local timestamp action reason metrics
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  action="$1"
  reason="$2"
  metrics="$3"
  echo "[$timestamp] [$action] Reason: $reason | Metrics: $metrics" >> "$LOGFILE"
}

check_client_counters() {
  local -A initial final delta
  local metrics=("client_tsvc_timeout" "client_write_timeout" "client_write_error" "client_proxy_timeout")
  declare -A threshold=( [client_tsvc_timeout]=50 [client_write_timeout]=50 [client_write_error]=20 [client_proxy_timeout]=20 )
  local breach="false"

  for m in "${metrics[@]}"; do
    initial[$m]=$(asadm -e "show statistics like $m" | awk -v k="$m" '$0 ~ k { for (i = 2; i <= NF; i++) { gsub(/ /, "", $i); if ($i ~ /^[0-9]+$/) sum += $i }; print sum; exit }')
  done

  sleep "$CHECK_INTERVAL"

  for m in "${metrics[@]}"; do
    final[$m]=$(asadm -e "show statistics like $m" | awk -v k="$m" '$0 ~ k { for (i = 2; i <= NF; i++) { gsub(/ /, "", $i); if ($i ~ /^[0-9]+$/) sum += $i }; print sum; exit }')
    delta[$m]=$(( ${final[$m]:-0} - ${initial[$m]:-0} ))
  done

  local metrics_text=""
  for m in "${metrics[@]}"; do
    metrics_text+="$m_delta=${delta[$m]} "
    if (( ${delta[$m]} > ${threshold[$m]} )); then
      breach="true"
      reason="$m exceeded threshold"
    fi
  done

  if [ "$breach" = "true" ]; then
    log_plain "skipped" "$reason" "$metrics_text"
    return 1
  fi

  log_plain "proceeding" "all counters within limits" "$metrics_text"
  return 0
}

check_cluster_gauges() {
  local breach="false"
  local defrag_q=($(asadm -e "show statistics like defrag_q" | awk -F '|' 'NR>1 {for (i=2; i<=NF; i++) { gsub(/ /,"",$i); print $i }}'))
  local write_q=($(asadm -e "show statistics like write_q" | awk -F '|' 'NR>1 {for (i=2; i<=NF; i++) { gsub(/ /,"",$i); print $i }}'))
  local shadow_q=($(asadm -e "show statistics like shadow_write_q" | awk -F '|' 'NR>1 {for (i=2; i<=NF; i++) { gsub(/ /,"",$i); print $i }}'))

  local metrics_text=""

  for val in "${defrag_q[@]}"; do
    metrics_text+="defrag_q=$val "
    if (( val > 1000 )); then
      breach="true"
      reason="defrag_q above threshold"
    fi
  done

  for val in "${write_q[@]}"; do
    metrics_text+="write_q=$val "
    if (( val > 200 )); then
      breach="true"
      reason="write_q above threshold"
    fi
  done

  for val in "${shadow_q[@]}"; do
    metrics_text+="shadow_write_q=$val "
    if (( val > 200 )); then
      breach="true"
      reason="shadow_write_q above threshold"
    fi
  done

  if [ "$breach" = "true" ]; then
    log_plain "skipped" "$reason" "$metrics_text"
    return 1
  fi

  log_plain "proceeding" "all gauges within limits" "$metrics_text"
  return 0
}

# === MAIN ===
for (( d=START_DAY; d>=END_DAY; d-- )); do
  for (( s=0; s<SUB_CHUNKS_PER_DAY; s++ )); do
    NOW=$(date +%s)
    RUNTIME=$((NOW - SCRIPT_START))
    if (( RUNTIME > MAX_RUNTIME_SEC )); then
      echo "$(date) Max runtime exceeded." | tee -a "$LOGFILE"
      exit 0
    fi

    OFFSET_SEC=$(( (d * 86400) - (s * SLICE_SECONDS) ))
    LUT=$(date -u -d "@$((NOW - OFFSET_SEC))" +%s%N)
    CMD="asinfo -v 'truncate:namespace=$NAMESPACE;set=$SET;lut=$LUT'"

    echo "$(date) === Slice: ${d}.${s} ===" | tee -a "$LOGFILE"
    echo "$(date) LUT: $LUT" | tee -a "$LOGFILE"

    if ! check_cluster_gauges || ! check_client_counters; then
      echo "$(date) Skipping due to system pressure" | tee -a "$LOGFILE"
      continue
    fi

    if [ "$DRY_RUN" = true ]; then
      echo "$(date) Dry Run: $CMD" | tee -a "$LOGFILE"
    else
      echo "$(date) Executing: $CMD" | tee -a "$LOGFILE"
      asadm -e "$CMD" >> "$LOGFILE" 2>&1
      echo "$d" > "$LAST_RUN_FILE"
    fi

    sleep 10
  done
done
