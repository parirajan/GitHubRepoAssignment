#!/bin/bash

# -----------------------
# CONFIGURATION (Defaults)
# -----------------------
NAMESPACE="test"
SET="demo"
CHUNK_TARGET=1000000         # How many objects per truncate chunk
AGE_DAYS=7                   # Age cutoff in days (objects older than this)
DEFQ_THRESHOLD=500           # Defrag queue threshold
SLEEP_SEC=5                  # Sleep between truncates
LOG_DIR="./logs"             # Log directory

# Create log dir if needed
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/truncate_${NAMESPACE}_${SET}_$(date +%Y%m%d_%H%M%S).log"

# -----------------------
# LOGGING MODULE
# -----------------------

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

function truncate_run() {
    local BEFORE_NS=$1
    local MODE=$2

    if [[ "$MODE" == "DRY" ]]; then
        log "[DRY RUN] Would truncate before-ns=$BEFORE_NS"
    else
        log "[PROD RUN] Truncating before-ns=$BEFORE_NS"
        asinfo -v "truncate:namespace=$NAMESPACE;set=$SET;before-ns=$BEFORE_NS" >> "$LOG_FILE" 2>&1
    fi
}

# -----------------------
# MAIN LOGIC
# -----------------------

MIN_AGE_SECONDS=$((AGE_DAYS * 24 * 60 * 60))
NOW_NS=$(date +%s%N)

log "==== Starting Truncation ===="
log "Namespace: $NAMESPACE, Set: $SET, Age Cutoff: $AGE_DAYS days, Chunk Size: $CHUNK_TARGET"

# Get histogram
HIST_OUTPUT=$(asinfo -v "hist-dump:namespace=$NAMESPACE;type=object-age")
declare -A HISTOGRAM
IFS=';' read -ra BUCKETS <<< "$HIST_OUTPUT"

for ENTRY in "${BUCKETS[@]}"; do
    if [[ "$ENTRY" =~ ^[0-9]+:[0-9]+$ ]]; then
        BUCKET_INDEX=$(echo "$ENTRY" | cut -d: -f1)
        BUCKET_COUNT=$(echo "$ENTRY" | cut -d: -f2)
        HISTOGRAM[$BUCKET_INDEX]=$BUCKET_COUNT
    fi
done

MIN_BUCKET=$(awk "BEGIN {print int(log($MIN_AGE_SECONDS)/log(2))}")
MAX_BUCKET=$(echo "${!HISTOGRAM[@]}" | tr " " "\n" | sort -nr | head -n1)

log "Processing buckets from $MAX_BUCKET down to $MIN_BUCKET..."

for (( BUCKET=$MAX_BUCKET; BUCKET>=$MIN_BUCKET; BUCKET-- )); do
    COUNT=${HISTOGRAM[$BUCKET]:-0}
    if (( COUNT == 0 )); then
        continue
    fi

    AGE_SEC=$((2 ** BUCKET))
    NEXT_AGE_SEC=$((2 ** (BUCKET + 1)))
    BUCKET_WINDOW_SEC=$((NEXT_AGE_SEC - AGE_SEC))

    log "[Bucket $BUCKET] ~${AGE_SEC} sec old → ${COUNT} objects"

    if (( COUNT <= CHUNK_TARGET )); then
        # Small bucket
        AGE_NS=$((AGE_SEC * 1000000000))
        BEFORE_NS=$((NOW_NS - AGE_NS))

        truncate_run $BEFORE_NS "DRY"
        truncate_run $BEFORE_NS "PROD"

        sleep $SLEEP_SEC
    else
        # Large bucket → split
        SLICES=$((COUNT / CHUNK_TARGET + 1))
        SLICE_WINDOW_SEC=$((BUCKET_WINDOW_SEC / SLICES))

        log " → Large bucket, slicing into $SLICES chunks"

        for (( SLICE=0; SLICE<SLICES; SLICE++ )); do
            SLICE_AGE_SEC=$((AGE_SEC + (SLICE * SLICE_WINDOW_SEC)))
            SLICE_AGE_NS=$((SLICE_AGE_SEC * 1000000000))
            BEFORE_NS=$((NOW_NS - SLICE_AGE_NS))

            log "    [Chunk $((SLICE+1))/$SLICES] before-ns=${BEFORE_NS}"

            truncate_run $BEFORE_NS "DRY"
            truncate_run $BEFORE_NS "PROD"

            # Defrag pressure check
            DEFQ=$(asinfo -v "get-stats:context=namespace;id=$NAMESPACE" | grep -Po 'defrag_q=\K\d+')
            if (( DEFQ > DEFQ_THRESHOLD )); then
                log "    Defrag queue high ($DEFQ) → sleeping extra..."
                sleep $((SLEEP_SEC * 5))
            else
                sleep $SLEEP_SEC
            fi
        done
    fi
done

log "=== Truncation completed ==="
