#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || ! -f "$1" ]]; then
  echo "Usage: $0 /path/to/system_inventory_REPORT.txt" >&2
  exit 1
fi

REPORT="$1"
OUT="/tmp/system_inventory_versions_$(date +%Y%m%d%H%M%S).txt"
: > "$OUT"

# --- 0) OS version (from /etc/redhat-release contents in report) ---
# e.g. "Red Hat Enterprise Linux release 9.3 (Plow)"
os_line="$(grep -m1 -E 'release[[:space:]]+[0-9]' "$REPORT" || true)"
if [[ -n "$os_line" ]]; then
  os_name="$(echo "$os_line" | sed -E 's/[[:space:]]*release[[:space:]].*//' | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')"
  os_ver="$(echo "$os_line" | grep -Eo '[0-9]+([.][0-9]+)*' | head -n1)"
  [[ -n "$os_name" && -n "$os_ver" ]] && echo "$os_name $os_ver" >> "$OUT"
fi

# --- 1) RPM packages (already "name version-release") ---
grep -E '^[A-Za-z0-9._+-]+ [0-9]' "$REPORT" >> "$OUT" || true

# --- 2) pip (pip3 list table) ---
awk '/^===== Python \(pip3\) =====/{flag=1;next} /^$/{if(flag){exit}} flag' "$REPORT" \
  | awk 'NR>2 && NF>=2 {print $1, $2}' >> "$OUT" || true

# --- 3) npm global packages (npm list -g --depth=0) ---
awk '/^===== Node \(npm\) =====/{flag=1;next} /^$/{if(flag){exit}} flag' "$REPORT" \
  | sed -n 's/.*── //p' | sed 's/@/ /' >> "$OUT" || true

# --- 4) Docker images (repo tag) ---
awk '/^===== Docker Images =====/{flag=1;next} /^$/{if(flag){exit}} flag' "$REPORT" \
  | awk '/^[^ ]+ +[^ ]+$/ {print $1, $2}' >> "$OUT" || true

# --- 5) Envoy / Nginx / Java (match anywhere) ---
# envoy line looks like: envoy  version: <sha>/1.29.11/...
grep -E 'envoy[[:space:]]+version:' "$REPORT" \
 | sed -E 's#.* /([0-9.]+)/.*#envoy \1#' >> "$OUT" || true

# nginx: "nginx version: nginx/1.26.3"
grep -E '^nginx version:' "$REPORT" \
 | sed -E 's#^nginx version: nginx/([0-9.]+).*#nginx \1#' >> "$OUT" || true

# java: 'openjdk version "21.0.8"' or 'java version "17.0.9"'
grep -E '^(openjdk|java) version "' "$REPORT" \
 | sed -E 's/.* version "([0-9.]+)".*/java \1/' >> "$OUT" || true

# --- 6) Non-RPM binaries (from raw --version outputs) ---
# Capture shapes:
#   foo/1.2.3      -> "foo 1.2.3"
#   foo v1.2.3     -> "foo v1.2.3"
#   foo 1.2.3      -> "foo 1.2.3"
grep -Eo '[A-Za-z0-9._-]+/[0-9]+([._-][0-9A-Za-z]+)*' "$REPORT" \
  | sed 's#/# #' >> "$OUT" || true

grep -Eo '^[A-Za-z0-9._-]+ v[0-9]+([._-][0-9A-Za-z]+)*' "$REPORT" \
  >> "$OUT" || true

grep -Eo '^[A-Za-z0-9._-]+ [0-9]+([._-][0-9A-Za-z]+)*' "$REPORT" \
  >> "$OUT" || true

# --- 7) JAR manifests: Implementation-Title + Implementation-Version ---
awk '
  /^-- .*\.jar --$/ {have=1; title=""; ver=""; next}
  have && /^Implementation-Title:/   {sub(/^Implementation-Title:[ ]*/, "", $0); title=$0; next}
  have && /^Implementation-Version:/ {sub(/^Implementation-Version:[ ]*/, "", $0); ver=$0;
                                      if (title != "" && ver != "") print title " " ver; next}
' "$REPORT" >> "$OUT" || true

# --- 8) Spring Boot BOOT-INF libs: artifact-version.jar -> "artifact version" ---
grep -E 'BOOT-INF/lib/.*\.jar' "$REPORT" \
 | sed -nE 's#.*/([A-Za-z0-9_.+-]+)-([0-9][0-9A-Za-z.+:-]*)\.jar#\1 \2#p' >> "$OUT" || true

# --- 9) Finalize: drop empties, dedupe, sort ---
sed -i '/^[[:space:]]*$/d' "$OUT"
sort -u "$OUT" -o "$OUT"

echo "Versions-only list saved to: $OUT"
