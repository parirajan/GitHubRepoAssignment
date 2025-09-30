#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || ! -f "$1" ]]; then
  echo "Usage: $0 /path/to/system_inventory_REPORT.txt" >&2
  exit 1
fi

REPORT_FILE="$1"
OUT="/tmp/system_inventory_versions_$(date +%Y%m%d%H%M%S).txt"
: > "$OUT"

# --- 1) RPM packages (already 'name version-release') ---
grep -E '^[A-Za-z0-9._+-]+ [0-9]' "$REPORT_FILE" >> "$OUT" || true

# --- 2) pip3 list (table 'name version') ---
awk '/^===== Python \(pip3\) =====/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | awk 'NR>2 && NF>=2 {print $1, $2}' >> "$OUT" || true

# --- 3) npm globals (lines like "├── pkg@1.2.3") ---
awk '/^===== Node \(npm\) =====/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | sed -n 's/.*── //p' | sed 's/@/ /' >> "$OUT" || true

# --- 4) Docker images (repo tag) ---
awk '/^===== Docker Images =====/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | awk '/^[^ ]+ +[^ ]+$/ {print $1, $2}' >> "$OUT" || true

# --- 5) Envoy / Nginx / Java ---
# envoy: "... /1.29.11/ ..."
grep -E '^envoy[[:space:]]+version:' "$REPORT_FILE" \
 | sed -E 's#.* /([0-9.]+)/.*#envoy \1#' >> "$OUT" || true

# nginx: "nginx version: nginx/1.26.3"
grep -E '^nginx version:' "$REPORT_FILE" \
 | sed -E 's#^nginx version: nginx/([0-9.]+).*#nginx \1#' >> "$OUT" || true

# java: 'openjdk version "21.0.8"' or 'java version "17.0.9"'
grep -E '^(openjdk|java) version "' "$REPORT_FILE" \
 | sed -E 's/.* version "([0-9.]+)".*/java \1/' >> "$OUT" || true

# --- 6) Non-RPM binaries blocks ---
# Lines printed after "---- /path/to/bin ----" often contain "tool v1.2.3" or "tool 1.2.3" or "tool/1.2.3"
# Extract those three shapes.
awk '/^===== Non-RPM Binaries/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | grep -Eo '^[A-Za-z0-9._-]+ v[0-9]+([._-][0-9A-Za-z]+)*|^[A-Za-z0-9._-]+ [0-9]+([._-][0-9A-Za-z]+)*' \
 >> "$OUT" || true
awk '/^===== Non-RPM Binaries/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | grep -Eo '[A-Za-z0-9._-]+/[0-9]+([._-][0-9A-Za-z]+)*' \
 | sed 's#/# #' >> "$OUT" || true

# --- 7) JAR manifests: pair Implementation-Title with Implementation-Version ---
awk '
  /^-- .*\.jar --$/   { title=""; ver=""; next }
  /^Implementation-Title:/   { sub(/^Implementation-Title:[ ]*/, "", $0); title=$0; next }
  /^Implementation-Version:/ { sub(/^Implementation-Version:[ ]*/, "", $0); ver=$0;
                               if (title != "" && ver != "") print title " " ver }
' "$REPORT_FILE" >> "$OUT" || true

# --- 8) Spring Boot BOOT-INF/lib jars: artifact-version.jar -> "artifact version" ---
grep 'BOOT-INF/lib/.*\.jar' "$REPORT_FILE" \
 | sed -nE 's#.*/([A-Za-z0-9_.+-]+)-([0-9][0-9A-Za-z.+:-]*)\.jar#\1 \2#p' \
 >> "$OUT" || true

# --- 9) Clean up: dedupe + sort, strip empties ---
sed -i '/^[[:space:]]*$/d' "$OUT"
sort -u "$OUT" -o "$OUT"

echo "Versions-only list saved to: $OUT"
