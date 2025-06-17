Aerospike Truncation Script - Detailed Explanation

This document explains the structure and logic of the Aerospike truncation script used to safely delete records older than a certain age, while minimizing impact on cluster performance.

1. Purpose of the Script

To perform time-based truncation on multiple sets in Aerospike by:

Truncating records older than a rolling window (default: 30 to 7 days).

Spreading truncation across multiple time slices per day.

Running truncations per set in parallel.

Pre-checking cluster health (gauges and counters) to avoid impacting read/write operations.

Logging events and resuming from the last successful day.

2. Configuration Parameters

Variable

Description

NAMESPACE

Aerospike namespace where truncation occurs.

SETS

Associative array holding set names to be truncated.

LOGFILE

Path for writing operation logs.

LAST_RUN_FILE

File for storing the last successfully truncated day.

MAX_RUNTIME_SEC

Upper bound on script run time. Defaults to 1 hour.

SUB_CHUNKS_PER_DAY

Number of slices per day (default: 4 means 6hr slices).

SLICE_SECONDS

Duration of each chunk in seconds (calculated).

END_DAY

Truncation stops once this day is reached.

DRY_RUN

Enables safe logging without executing truncation.

CHECK_INTERVAL

Interval between metric collection for delta counters.

CMD_TIMEOUT

Timeout per truncate command (e.g. 300s).

3. Function: log_plain()

Logs actions with timestamp in plain text:

log_plain "skipped" "defrag_q above threshold" "defrag_q=1234"

4. Function: check_client_counters()

Captures client-side error deltas for key metrics over $CHECK_INTERVAL seconds.

Metrics Monitored:

client_tsvc_timeout

client_write_timeout

client_write_error

client_proxy_timeout

If delta exceeds predefined threshold, the slice is skipped.

5. Function: check_cluster_gauges()

Monitors cluster pressure by checking gauge metrics:

defrag_q

write_q

shadow_write_q

Dual Threshold Logic:

Per-disk value check: skips if any individual disk exceeds limit (e.g. >1000).

Cluster-wide sum check: skips if total exceeds threshold * number of disks.

6. Main Truncation Loop

Structure:

for day in START_DAY ... END_DAY
  for chunk in SUB_CHUNKS_PER_DAY
    check metrics
    build LUT for time window
    truncate each set in parallel
    track PIDs and retry failed ones
    update LAST_RUN_FILE with d-1

Parallel Truncation:

Each set is truncated via background process using timeout for control. If any PID fails, it is retried once. Both success and failure are logged.

Command Correction:

To avoid extra escaping issues in dry run vs live execution, the correct usage should be:

CMD="truncate:namespace=$NAMESPACE;set=$SET_NAME;lut=$LUT"
asadm -e "$CMD"

Rather than embedding too many layers of quotes and backslashes.

7. Log Format

[2025-06-12T12:34:56Z] [skipped] Reason: defrag_q above threshold | Metrics: defrag_q=1234 write_q=12 shadow_write_q=10

8. Recovery and Continuation

Each successful day reduces the START_DAY and saves progress in LAST_RUN_FILE.

Next script run resumes from the last completed START_DAY.

9. Future Enhancements (optional)

Add alerting if N consecutive days are skipped.

Integrate EBS/CloudWatch latency metrics.

Time-of-day throttling (e.g. skip daytime truncations).

Enhanced retry backoff logic.
