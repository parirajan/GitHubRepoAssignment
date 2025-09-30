#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d%H%M%S)"
REPORT_FILE="/tmp/system_inventory_${TS}.txt"
VERSIONS_FILE="/tmp/system_inventory_versions_${TS}.txt"

# JAR search base (recursive)
JAR_SEARCH_BASE="${JAR_SEARCH_BASE:-/opt/something}"

# Regex for version tokens
VERSION_RX='[0-9]+([._-][0-9A-Za-z]+)+'

# start fresh
: > "$REPORT_FILE"
: > "$VERSIONS_FILE"

# tee everything to the report
exec > >(tee -a "$REPORT_FILE") 2>&1

# -------- report collection --------
echo "===== System Inventory Report ====="
echo "Generated: $(date)"
echo "Report:    $REPORT_FILE"
echo "Versions:  $VERSIONS_FILE"
echo

echo "===== OS Release ====="
cat /etc/redhat-release 2>/dev/null || echo "/etc/redhat-release not found"
echo

echo "===== RPM Packages ====="
if command -v rpm >/dev/null 2>&1; then
  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n' | sort
else
  echo "rpm not available"
fi
echo

echo "===== Non-RPM Binaries (/usr/local/bin, /opt/*/bin) ====="
shopt -s nullglob
for bin in /usr/local/bin/* /opt/*/bin/*; do
  [[ -x "$bin" && ! -d "$bin" ]] || continue
  if command -v rpm >/dev/null 2>&1 && rpm -qf "$bin" &>/dev/null; then
    continue
  fi
  echo "---- $bin ----"
  timeout 5s "$bin" --version 2>&1 || true
  timeout 5s "$bin" -version 2>&1 || true
  timeout 5s "$bin" version 2>&1 || true
  timeout 5s "$bin" -v 2>&1 || true
done
shopt -u nullglob
echo

echo "===== Python (pip3) ====="
if command -v pip3 >/dev/null 2>&1; then
  pip3 list
else
  echo "pip3 not found"
fi
echo

echo "===== Node (npm) ====="
if command -v npm >/dev/null 2>&1; then
  npm list -g --depth=0
else
  echo "npm not found"
fi
echo

echo "===== Docker Images ====="
if command -v docker >/dev/null 2>&1; then
  docker images
else
  echo "docker not found"
fi
echo

echo "===== JAR Metadata (recursive under $JAR_SEARCH_BASE) ====="
if [[ -d "$JAR_SEARCH_BASE" ]]; then
  find "$JAR_SEARCH_BASE" -xdev \
    \( -path /proc -o -path /sys -o -path /dev -o -path /run -o -path /var/lib/docker -o -path /tmp \) -prune -o \
    -type f -name '*.jar' -print0 2>/dev/null \
  | while IFS= read -r -d '' jar; do
      echo "-- $jar --"

      # verify it’s a valid zip/JAR
      if ! unzip -tq "$jar" >/dev/null 2>&1; then
        echo "   (invalid/corrupt JAR, skipped)"
        continue
      fi

      echo "   Manifest:"
      unzip -p "$jar" META-INF/MANIFEST.MF 2>/dev/null | \
        grep -E '^(Implementation|Bundle)-' || echo "      (none)"

      echo "   BOOT-INF/lib jars:"
      unzip -l "$jar" "BOOT-INF/lib/*.jar" 2>/dev/null | \
        awk '{print $4}' | grep '\.jar$' | sed 's#^#      #' || echo "      (none)"

      echo
    done
else
  echo "Base path not found: $JAR_SEARCH_BASE"
fi
echo


echo "===== Envoy ====="
if command -v envoy >/dev/null 2>&1; then
  envoy --version 2>&1
else
  echo "envoy not found"
fi
echo

echo "===== Nginx ====="
if command -v nginx >/dev/null 2>&1; then
  nginx -v 2>&1
else
  echo "nginx not found"
fi
echo

echo "===== Java ====="
if command -v java >/dev/null 2>&1; then
  java -version 2>&1
else
  echo "java not found"
fi
echo

echo "===== Report Complete ====="
echo "Detailed report: $REPORT_FILE"
echo

# -------- post-process into versions list --------
echo "Extracting versions into $VERSIONS_FILE ..."
grep -Eo '[A-Za-z0-9._-]+/[0-9]+([._-][0-9A-Za-z]+)*' "$REPORT_FILE" \
  | sed 's#/# #' >> "$VERSIONS_FILE"

grep -Eo '[A-Za-z0-9._-]+ v[0-9]+([._-][0-9A-Za-z]+)*' "$REPORT_FILE" \
  >> "$VERSIONS_FILE"

awk '{if ($1 ~ /^[A-Za-z0-9._-]+$/ && $2 ~ /^[0-9]/) print $1, $2}' "$REPORT_FILE" \
  >> "$VERSIONS_FILE"

sort -u "$VERSIONS_FILE" -o "$VERSIONS_FILE"

echo "Versions-only:  $VERSIONS_FILE"
