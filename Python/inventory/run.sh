#!/usr/bin/env bash
set -euo pipefail

# ===== Config =====
REPORT_FILE="/tmp/system_inventory_$(date +%Y%m%d%H%M%S).txt"
JAR_SEARCH_BASE="${JAR_SEARCH_BASE:-/opt/something}"   # change or export to override

exec > >(tee -a "$REPORT_FILE") 2>&1

echo "===== System Inventory Report ====="
echo "Generated: $(date)"
echo "Output file: $REPORT_FILE"
echo

echo "===== OS Release ====="
cat /etc/redhat-release 2>/dev/null || echo "/etc/redhat-release not found"
echo

echo "===== RPM Packages ====="
if command -v rpm >/dev/null 2>&1; then
  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n' | sort
else
  echo "rpm not available on this system"
fi
echo

echo "===== Non-RPM Binaries ====="
# Find executables in common custom locations that are not owned by RPM
for bin in /usr/local/bin/* /opt/*/bin/*; do
  [[ -x "$bin" && ! -d "$bin" ]] || continue
  if ! rpm -qf "$bin" &>/dev/null; then
    ver="$("$bin" --version 2>/dev/null || "$bin" -v 2>/dev/null || true)"
    echo "$(basename "$bin") ${ver:-unknown}"
  fi
done
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

echo "===== JAR Metadata (under $JAR_SEARCH_BASE) ====="
if [ -d "$JAR_SEARCH_BASE" ]; then
  # Use -print0 to safely handle spaces; search recursively under /opt/something/*
  while IFS= read -r -d '' jar; do
    echo "-- $jar --"
    unzip -p "$jar" META-INF/MANIFEST.MF 2>/dev/null | grep -E '^(Implementation|Bundle)-' || echo "No manifest info"
    unzip -l "$jar" "BOOT-INF/lib/*" 2>/dev/null | awk '{print $4}' | grep '\.jar$' || echo "No BOOT-INF/lib jars"
    echo
  done < <(find "$JAR_SEARCH_BASE" -type f -name '*.jar' -print0 2>/dev/null)
else
  echo "Base path not found: $JAR_SEARCH_BASE"
fi
echo

echo "===== Envoy ====="
if command -v envoy >/dev/null 2>&1; then
  envoy --version
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
echo "Saved to: $REPORT_FILE"
