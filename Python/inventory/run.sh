#!/usr/bin/env bash
set -euo pipefail

# ---------- CONFIG ----------
OUT="${OUT:-/tmp/software_inventory.txt}"
JAR_SEARCH_DIRS=(${JAR_SEARCH_DIRS:-/opt /srv /usr/local /var /home})
EXTRA_BIN_DIRS=(${EXTRA_BIN_DIRS:-/usr/local/bin /usr/bin /bin /sbin /usr/sbin /opt/*/bin})
# Explicit non-RPM tools to check (name -> command)
declare -A EXPLICIT_CMDS=(
  [nginx]="nginx"
  [envoy]="envoy"
  [java]="java"
  [python3]="python3"
  [python]="python"
  [node]="node"
  [npm]="npm"
  [docker]="docker"
  [git]="git"
  [go]="go"
  [openssl]="openssl"
)
# Version regex (generic fallback)
VERSION_RX='([0-9]+([.:-][0-9A-Za-z]+)+)'

# ---------- HELPERS ----------
print_kv(){ # name version
  local name="$1" ver="$2"
  [ -n "$name" ] && [ -n "$ver" ] && printf '%s %s\n' "$name" "$ver"
}

try_cmd_version(){ # cmd -> "version" (best effort)
  local cmd="$1" out=""
  # try common flags; suppress noise
  for args in "--version" "-version" "version" "-v"; do
    if out="$("$cmd" $args 2>&1 | head -n 3)"; then
      if [[ "$out" =~ $VERSION_RX ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
      fi
    fi || true
  done
  # openssl special (prints structured)
  if [[ "$cmd" == "openssl" ]]; then
    out="$(openssl version 2>/dev/null || true)"
    [[ "$out" =~ $VERSION_RX ]] && echo "${BASH_REMATCH[1]}" && return 0
  fi
  # envoy special (prints long line)
  if [[ "$cmd" == "envoy" ]]; then
    out="$(envoy --version 2>/dev/null || true)"
    [[ "$out" =~ /([0-9]+\.[0-9]+(\.[0-9]+)?) ]] && echo "${BASH_REMATCH[1]}" && return 0
  fi
  return 1
}

jar_manifest_version(){ # jarfile -> "title version" OR "basename version"
  local jar="$1" title="" ver="" out=""
  # MANIFEST.MF Implementation-*:
  out="$(unzip -p "$jar" META-INF/MANIFEST.MF 2>/dev/null || true)"
  [[ "$out" =~ ^Implementation-Title:\ *(.*)$ ]] && title="${BASH_REMATCH[1]}"
  [[ "$out" =~ ^Implementation-Version:\ *(.*)$ ]] && ver="${BASH_REMATCH[1]}"
  if [ -z "$ver" ]; then
    # pom.properties version
    out="$(unzip -p "$jar" 'META-INF/maven/*/*/pom.properties' 2>/dev/null || true)"
    [[ "$out" =~ ^version=(.*)$ ]] && ver="${BASH_REMATCH[1]}"
    [[ "$out" =~ ^artifactId=(.*)$ ]] && [ -z "$title" ] && title="${BASH_REMATCH[1]}"
  fi
  # fallback: from filename my-lib-1.2.3.jar
  if [ -z "$ver" ]; then
    local base; base="$(basename "$jar")"
    if [[ "$base" =~ -([0-9][0-9A-Za-z.+:-]*)\.jar$ ]]; then ver="${BASH_REMATCH[1]}"; fi
    [ -z "$title" ] && title="${base%.jar}"
  fi
  title="${title:-$(basename "$jar" .jar)}"
  [ -n "$ver" ] && echo "$title $ver"
}

list_boot_inf_libs(){ # jarfile -> prints "libname version"
  local jar="$1" line base ver
  # list jars under BOOT-INF/lib
  while IFS= read -r line; do
    base="$(basename "$line")"
    # version from filename artifact-1.2.3.jar
    if [[ "$base" =~ ^([A-Za-z0-9_.+-]+)-([0-9][0-9A-Za-z.+:-]*)\.jar$ ]]; then
      print_kv "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    else
      # if no clear version, print name with unknown
      print_kv "${base%.jar}" "unknown"
    fi
  done < <(unzip -l "$jar" 'BOOT-INF/lib/*.jar' 2>/dev/null | awk '{print $4}' | grep '^BOOT-INF/lib/' || true)
}

dedup_sorted(){ awk '!seen[$0]++' | sort -u; }

# ---------- START ----------
: > "$OUT"

# (A) RPM packages
if command -v rpm >/dev/null 2>&1; then
  rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n' 2>/dev/null | dedup_sorted >> "$OUT" || true
fi

# (B1) Explicit non-RPM tools (reliable)
for name in "${!EXPLICIT_CMDS[@]}"; do
  cmd="${EXPLICIT_CMDS[$name]}"
  if command -v "$cmd" >/dev/null 2>&1; then
    if ver="$(try_cmd_version "$cmd")"; then
      print_kv "$name" "$ver" >> "$OUT"
    fi
  fi
done

# (B2) Other executables in common bin dirs (best effort; skip ones already printed)
declare -A already=()
while read -r nm _; do already["$nm"]=1; done < <(awk '{print $1}' "$OUT" 2>/dev/null | awk '{print $1" x"}')
BIN_SET=()
for d in "${EXTRA_BIN_DIRS[@]}"; do BIN_SET+=($(compgen -G "$d" 2>/dev/null || true)); done
PATH_SCAN=$(IFS=:; echo "$PATH")
for d in $PATH_SCAN "${BIN_SET[@]}"; do
  [ -d "$d" ] || continue
  while IFS= read -r f; do
    nm="$(basename "$f")"
    [[ -n "${already[$nm]:-}" ]] && continue
    [[ -x "$f" && ! -d "$f" ]] || continue
    if ver="$(try_cmd_version "$f")"; then
      print_kv "$nm" "$ver" >> "$OUT"
      already["$nm"]=1
    fi
  done < <(find "$d" -maxdepth 1 -type f -perm -111 2>/dev/null)
done

# (C) JARs: manifest + BOOT-INF/lib jars
for root in "${JAR_SEARCH_DIRS[@]}"; do
  [ -d "$root" ] || continue
  while IFS= read -r jar; do
    if info="$(jar_manifest_version "$jar")"; then
      echo "$info" >> "$OUT"
    fi
    list_boot_inf_libs "$jar" >> "$OUT"
  done < <(find "$root" -type f -name '*.jar' 2>/dev/null | head -n 2000)
done

# (D) If Envoy admin or Nginx expose versions via HTTP (optional quick probes)
# curl -s http://127.0.0.1:9901/server_info | jq -r '.version' 2>/dev/null | sed 's#.*/\([0-9.]\+\).*#envoy \1#' >> "$OUT" || true
# curl -sI http://127.0.0.1 2>/dev/null | grep -i '^server:' | sed -E 's/Server: *([^/]+)\/?([0-9.]+)?.*/\1 \2/' >> "$OUT" || true

# Final output (unique, sorted)
dedup_sorted < "$OUT" > "${OUT}.uniq"
mv "${OUT}.uniq" "$OUT"

echo "Wrote inventory to $OUT"
