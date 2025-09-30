#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d%H%M%S)"
REPORT_FILE="/tmp/system_inventory_${TS}.txt"
VERSIONS_FILE="/tmp/system_inventory_versions_${TS}.txt"

# Capture both outputs
exec > >(tee -a "$REPORT_FILE") 2>&1

echo "===== System Inventory Report ====="
echo "Generated: $(date)"
echo "Report: $REPORT_FILE"
echo "Versions: $VERSIONS_FILE"
echo

# Clear versions file
: > "$VERSIONS_FILE"

# -------- OS Release --------
echo "===== OS Release ====="
if [ -f /etc/redhat-release ]; then
  cat /etc/redhat-release
fi
echo

# -------- RPM Packages --------
echo "===== RPM Packages ====="
if command -v rpm >/dev/null 2>&1; then
  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n' | sort | tee -a "$VERSIONS_FILE"
else
  echo "rpm not available on this system"
fi
echo

# -------- Non-RPM Binaries --------
echo "===== Non-RPM Binaries ====="
for bin in /usr/local/bin/* /opt/*/bin/*; do
  [[ -x "$bin" && ! -d "$bin" ]] || continue
  if ! rpm -qf "$bin" &>/dev/null; then
    ver="$("$bin" --version 2>/dev/null || "$bin" -v 2>/dev/null || true)"
    ver_clean=$(echo "$ver" | head -n1 | awk '{print $NF}')
    echo "$(basename "$bin") ${ver_clean:-unknown}"
    echo "$(basename "$bin") ${ver_clean:-unknown}" >> "$VERSIONS_FILE"
  fi
done
echo

# -------- Python --------
echo "===== Python (pip3) ====="
if command -v pip3 >/dev/null 2>&1; then
  pip3 list | awk 'NR>2{print $1, $2}' | tee -a "$VERSIONS_FILE"
else
  echo "pip3 not found"
fi
echo

# -------- Node --------
echo "===== Node (npm) ====="
if command -v npm >/dev/null 2>&1; then
  npm list -g --depth=0 | grep '──' | sed 's/.*── //' | sed 's/@/ /' | tee -a "$VERSIONS_FILE"
else
  echo "npm not found"
fi
echo

# -------- Docker --------
echo "===== Docker Images ====="
if command -v docker >/dev/null 2>&1; then
  docker images --format '{{.Repository}} {{.Tag}}' | tee -a "$VERSIONS_FILE"
else
  echo "docker not found"
fi
echo

# -------- JAR Metadata --------
JAR_SEARCH_BASE="${JAR_SEARCH_BASE:-/opt/something}"
echo "===== JAR Metadata (under $JAR_SEARCH_BASE) ====="
if [ -d "$JAR_SEARCH_BASE" ]; then
  while IFS= read -r -d '' jar; do
    echo "-- $jar --"
    impl_title=$(unzip -p "$jar" META-INF/MANIFEST.MF 2>/dev/null | grep Implementation-Title | head -n1 | cut -d: -f2- | xargs || true)
    impl_version=$(unzip -p "$jar" META-INF/MANIFEST.MF 2>/dev/null | grep Implementation-Version | head -n1 | cut -d: -f2- | xargs || true)
    if [[ -n "$impl_title" && -n "$impl_version" ]]; then
      echo "$impl_title $impl_version"
      echo "$impl_title $impl_version" >> "$VERSIONS_FILE"
    fi
    unzip -l "$jar" "BOOT-INF/lib/*" 2>/dev/null | awk '{print $4}' | grep '\.jar$' | while read -r lib; do
      base=$(basename "$lib")
      if [[ "$base" =~ ^([A-Za-z0-9_.+-]+)-([0-9][0-9A-Za-z.+:-]*)\.jar$ ]]; then
        echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
        echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}" >> "$VERSIONS_FILE"
      fi
    done
    echo
  done < <(find "$JAR_SEARCH_BASE" -type f -name '*.jar' -print0 2>/dev/null)
else
  echo "Base path not found: $JAR_SEARCH_BASE"
fi
echo

# -------- Envoy --------
echo "===== Envoy ====="
if command -v envoy >/dev/null 2>&1; then
  ver=$(envoy --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
  echo "envoy ${ver:-unknown}"
  echo "envoy ${ver:-unknown}" >> "$VERSIONS_FILE"
else
  echo "envoy not found"
fi
echo

# -------- Nginx --------
echo "===== Nginx ====="
if command -v nginx >/dev/null 2>&1; then
  ver=$(nginx -v 2>&1 | grep -o '[0-9.]\+')
  echo "nginx ${ver:-unknown}"
  echo "nginx ${ver:-unknown}" >> "$VERSIONS_FILE"
else
  echo "nginx not found"
fi
echo

# -------- Java --------
echo "===== Java ====="
if command -v java >/dev/null 2>&1; then
  ver=$(java -version 2>&1 | head -n1 | grep -o '[0-9._]\+')
  echo "java ${ver:-unknown}"
  echo "java ${ver:-unknown}" >> "$VERSIONS_FILE"
else
  echo "java not found"
fi
echo

echo "===== Report Complete ====="
echo "Detailed report: $REPORT_FILE"
echo "Versions-only list: $VERSIONS_FILE"
