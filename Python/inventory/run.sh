#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d%H%M%S)"
REPORT_FILE="/tmp/system_inventory_${TS}.txt"
VERSIONS_FILE="/tmp/system_inventory_versions_${TS}.txt"

# Where to search for JARs (recursive)
JAR_SEARCH_BASE="${JAR_SEARCH_BASE:-/opt/something}"

# Regex to pull a single version token
VERSION_RX='[0-9]+([._-][0-9A-Za-z]+)+'

# start fresh
: > "$VERSIONS_FILE"

# tee everything to the report
exec > >(tee -a "$REPORT_FILE") 2>&1

say(){ echo "===== $* ====="; echo; }

# -------- helpers --------
print_name_version() {
  local name="$1" ver="$2"
  [[ -n "$name" && -n "$ver" ]] || return 0
  # normalize to single line token
  ver="$(echo "$ver" | tr -d '\r' | head -n1 | grep -Eo "$VERSION_RX" || true)"
  [[ -n "$ver" ]] || return 0
  echo "$name $ver" | tee -a "$VERSIONS_FILE"
}

jar_manifest_version() { # $1=jar -> echo "name version"
  local jar="$1" mt mv ppv ppa base name ver out
  # MANIFEST
  out="$(unzip -p "$jar" META-INF/MANIFEST.MF 2>/dev/null || true)"
  mt="$(echo "$out" | awk -F': ' '/^Implementation-Title:/{print $2; exit}')"
  mv="$(echo "$out" | awk -F': ' '/^Implementation-Version:/{print $2; exit}')"
  # pom.properties
  if [[ -z "$mv" ]]; then
    out="$(unzip -p "$jar" 'META-INF/maven/*/*/pom.properties' 2>/dev/null || true)"
    ppv="$(echo "$out" | awk -F'=' '/^version=/{print $2; exit}')"
    ppa="$(echo "$out" | awk -F'=' '/^artifactId=/{print $2; exit}')"
    [[ -z "$mt" && -n "$ppa" ]] && mt="$ppa"
    [[ -z "$mv" && -n "$ppv" ]] && mv="$ppv"
  fi
  # filename fallback
  base="$(basename "$jar")"
  [[ -z "$mt" ]] && mt="${base%.jar}"
  if [[ -z "$mv" && "$base" =~ -([0-9][0-9A-Za-z.+:-]*)\.jar$ ]]; then
    mv="${BASH_REMATCH[1]}"
  fi
  [[ -n "$mv" ]] && echo "$mt $mv"
}

list_boot_inf_libs() { # $1=jar -> echo "lib version" lines
  unzip -l "$1" 'BOOT-INF/lib/*.jar' 2>/dev/null \
    | awk '{print $4}' | grep '^BOOT-INF/lib/.*\.jar$' || true
}

# -------- report sections --------
say "System Inventory Report"
echo "Generated: $(date)"
echo "Report:    $REPORT_FILE"
echo "Versions:  $VERSIONS_FILE"
echo

say "OS Release"
cat /etc/redhat-release 2>/dev/null || echo "/etc/redhat-release not found"
echo

say "RPM Packages"
if command -v rpm >/dev/null 2>&1; then
  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n' | sort | tee -a "$VERSIONS_FILE"
else
  echo "rpm not available"
fi
echo

say "Non-RPM Binaries (/usr/local/bin, /opt/*/bin)"
for bin in /usr/local/bin/* /opt/*/bin/*; do
  [[ -x "$bin" && ! -d "$bin" ]] || continue
  if command -v rpm >/dev/null 2>&1 && rpm -qf "$bin" &>/dev/null; then
    continue  # owned by an rpm; already listed above
  fi
  # try typical flags; keep only 1-line version token
  out="$("$bin" --version 2>/dev/null || "$bin" -version 2>/dev/null || "$bin" version 2>/dev/null || "$bin" -v 2>/dev/null || true)"
  print_name_version "$(basename "$bin")" "$out"
done
echo

say "Python (pip3)"
if command -v pip3 >/dev/null 2>&1; then
  pip3 list | awk 'NR>2{print $1, $2}' | tee -a "$VERSIONS_FILE"
else
  echo "pip3 not found"
fi
echo

say "Node (npm)"
if command -v npm >/dev/null 2>&1; then
  npm list -g --depth=0 2>/dev/null \
    | grep '──' | sed 's/.*── //' | sed 's/@/ /' | tee -a "$VERSIONS_FILE"
else
  echo "npm not found"
fi
echo

say "Docker Images"
if command -v docker >/dev/null 2>&1; then
  docker images --format '{{.Repository}} {{.Tag}}' | tee -a "$VERSIONS_FILE"
else
  echo "docker not found"
fi
echo

say "JAR Metadata (recursive under $JAR_SEARCH_BASE)"
if [[ -d "$JAR_SEARCH_BASE" ]]; then
  while IFS= read -r -d '' jar; do
    echo "-- $jar --"
    if info="$(jar_manifest_version "$jar")"; then
      echo "$info"
      print_name_version "${info% *}" "${info##* }" >/dev/null
    else
      echo "No manifest/pom version"
    fi
    # Spring Boot nested libs
    while IFS= read -r lib; do
      base="$(basename "$lib")"
      if [[ "$base" =~ ^([A-Za-z0-9_.+-]+)-([0-9][0-9A-Za-z.+:-]*)\.jar$ ]]; then
        echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
        print_name_version "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" >/dev/null
      fi
    done < <(list_boot_inf_libs "$jar")
    echo
  done < <(find "$JAR_SEARCH_BASE" -type f -name '*.jar' -print0 2>/dev/null)
else
  echo "Base path not found: $JAR_SEARCH_BASE"
fi
echo

say "Envoy"
if command -v envoy >/dev/null 2>&1; then
  out="$(envoy --version 2>/dev/null || true)"
  print_name_version "envoy" "$out"
  echo "$out"
else
  echo "envoy not found"
fi
echo

say "Nginx"
if command -v nginx >/dev/null 2>&1; then
  out="$(nginx -v 2>&1 || true)"
  print_name_version "nginx" "$out"
  echo "$out"
else
  echo "nginx not found"
fi
echo

say "Java"
if command -v java >/dev/null 2>&1; then
  out="$(java -version 2>&1 | head -n1 || true)"
  print_name_version "java" "$out"
  echo "$out"
else
  echo "java not found"
fi
echo

# -------- finalize versions list: dedupe + sort --------
if [[ -s "$VERSIONS_FILE" ]]; then
  sort -u "$VERSIONS_FILE" -o "$VERSIONS_FILE"
fi

say "Report Complete"
echo "Detailed report: $REPORT_FILE"
echo "Versions-only:  $VERSIONS_FILE"
