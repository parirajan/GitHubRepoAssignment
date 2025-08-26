#!/usr/bin/env bash
set -euo pipefail

# -------- Config --------
ASG_NAME="${ASG_NAME:-MyASG}"
HOOK_NAME="${HOOK_NAME:-GracefulTerminate}"
REGION="${REGION:-us-west-2}"
SERVICE="${SERVICE:-yourapp.service}"
LOGFILE="${LOGFILE:-/var/log/asg_terminate.log}"
HEARTBEAT_INTERVAL="${HEARTBEAT_INTERVAL:-60}"   # seconds
HEARTBEAT_MAX_HOURS="${HEARTBEAT_MAX_HOURS:-48}" # lifecycle cap is 48h

# Optional: ALB/NLB target group ARN(s) (comma-separated) to drain before stop
TARGET_GROUP_ARNS="${TARGET_GROUP_ARNS:-}"       # e.g., "arn:...:tg/abc,arn:...:tg/def"

# -------- Helpers --------
log() { echo "[$(date -Is)] $*" | tee -a "$LOGFILE"; }
retry() { # retry <n> <sleep> <cmd...>
  local n=$1; shift; local s=$1; shift
  local i=1
  until "$@"; do
    if (( i >= n )); then return 1; fi
    sleep "$s"; ((i++))
  done
}

require() { command -v "$1" >/dev/null 2>&1 || { log "Missing binary: $1"; exit 2; }; }

# -------- Sanity checks --------
require aws
require systemctl
INSTANCE_ID="$(curl -fsS --max-time 2 http://169.254.169.254/latest/meta-data/instance-id || true)"
if [[ -z "${INSTANCE_ID:-}" ]]; then
  log "Unable to read instance-id from IMDS"; exit 2
fi

log "Starting graceful termination for $INSTANCE_ID (ASG=$ASG_NAME, hook=$HOOK_NAME, svc=$SERVICE, region=$REGION)"

# -------- Begin draining (optional) --------
if [[ -n "$TARGET_GROUP_ARNS" ]]; then
  IFS=',' read -r -a TGS <<< "$TARGET_GROUP_ARNS"
  for TG in "${TGS[@]}"; do
    log "Deregistering from target group: $TG"
    retry 5 2 \
      aws elbv2 deregister-targets --region "$REGION" \
        --target-group-arn "$TG" --targets "Id=$INSTANCE_ID" >>"$LOGFILE" 2>&1 || {
          log "WARN: deregister-targets failed for $TG (continuing)"
        }
  done
fi

# -------- Heartbeat keeper (background) --------
log "Starting heartbeat loop (every ${HEARTBEAT_INTERVAL}s)"
(
  SECONDS=0
  while true; do
    aws autoscaling record-lifecycle-action-heartbeat \
      --auto-scaling-group-name "$ASG_NAME" \
      --lifecycle-hook-name "$HOOK_NAME" \
      --instance-id "$INSTANCE_ID" \
      --region "$REGION" >>"$LOGFILE" 2>&1 || true
    sleep "$HEARTBEAT_INTERVAL"
    # Safety: don't exceed lifecycle hard cap (48h)
    if (( SECONDS >= HEARTBEAT_MAX_HOURS*3600 )); then
      echo "[$(date -Is)] Reached heartbeat max hours cap (${HEARTBEAT_MAX_HOURS}h); exiting heartbeat" >>"$LOGFILE"
      exit 0
    fi
  done
) &
HEARTBEAT_PID=$!

cleanup() { kill "$HEARTBEAT_PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# -------- Flip readiness immediately (if you have a readiness gate) --------
# Example: touch a file your app watches to go "not-ready", or stop a sidecar, etc.
# log "Flipping readiness to NotReady"
# /usr/local/bin/yourapp-notready.sh >>"$LOGFILE" 2>&1 || true

# -------- Stop service gracefully --------
log "Stopping service: $SERVICE"
systemctl stop "$SERVICE" >>"$LOGFILE" 2>&1 || {
  log "WARN: systemctl stop returned non-zero (continuing to validate)"
}

# Optional: force disk flush if your app doesn’t fsync internally
# log "Syncing disks"
# sync || true

# -------- Wait for LB drain (optional, if TARGET_GROUP_ARNS set) --------
if [[ -n "$TARGET_GROUP_ARNS" ]]; then
  for TG in "${TGS[@]}"; do
    log "Waiting for target state=draining/unused on TG: $TG"
    # Poll until no 'healthy' or 'initial' for this instance
    for _ in {1..180}; do
      TH="$(aws elbv2 describe-target-health --region "$REGION" --target-group-arn "$TG" --targets "Id=$INSTANCE_ID" 2>>"$LOGFILE" | tr -d '\n' || true)"
      if [[ -z "$TH" ]] || [[ "$TH" == *"TargetHealthState\":\"unused\""* ]] || [[ "$TH" == *"TargetHealthState\":\"draining\""* ]]; then
        break
      fi
      sleep 2
    done
  done
fi

# -------- Validate stopped --------
log "Validating service stopped"
if systemctl --quiet is-active "$SERVICE"; then
  log "Service still ACTIVE -> Completing lifecycle with ABANDON (ASG will proceed to kill)"
  retry 5 2 aws autoscaling complete-lifecycle-action \
    --auto-scaling-group-name "$ASG_NAME" \
    --lifecycle-hook-name "$HOOK_NAME" \
    --instance-id "$INSTANCE_ID" \
    --lifecycle-action-result ABANDON \
    --region "$REGION" >>"$LOGFILE" 2>&1 || log "ERROR: complete-lifecycle-action (ABANDON) failed"
  exit 1
fi

# -------- Success: continue termination --------
log "Service is STOPPED -> Completing lifecycle with CONTINUE"
retry 5 2 aws autoscaling complete-lifecycle-action \
  --auto-scaling-group-name "$ASG_NAME" \
  --lifecycle-hook-name "$HOOK_NAME" \
  --instance-id "$INSTANCE_ID" \
  --lifecycle-action-result CONTINUE \
  --region "$REGION" >>"$LOGFILE" 2>&1 || {
    log "ERROR: complete-lifecycle-action (CONTINUE) failed"
    exit 1
  }

log "Done. ASG may now terminate the instance."
