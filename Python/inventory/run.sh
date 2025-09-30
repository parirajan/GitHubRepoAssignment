#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || ! -f "$1" ]]; then
  echo "Usage: $0 /path/to/system_inventory_REPORT.txt" >&2
  exit 1
fi

REPORT_FILE="$1"
OUT="/tmp/system_inventory_versions_$(date +%Y%m%d%H%M%S).txt"
: > "$OUT"

# -------- 1) RPM (already "name version-release") --------
grep -E '^[A-Za-z0-9._+-]+ [0-9]' "$REPORT_FILE" >> "$OUT" || true

# -------- 2) pip3 list (table) --------
awk '/^===== Python \(pip3\) =====/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | awk 'NR>2 && NF>=2 {print $1, $2}' >> "$OUT" || true

# -------- 3) npm globals --------
awk '/^===== Node \(npm\) =====/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | sed -n 's/.*── //p' | sed 's/@/ /' >> "$OUT" || true

# -------- 4) Docker images (repo tag) --------
awk '/^===== Docker Images =====/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | awk '/^[^ ]+ +[^ ]+$/ {print $1, $2}' >> "$OUT" || true

# -------- 5) Envoy / Nginx / Java --------
grep -E '^envoy[[:space:]]+version:' "$REPORT_FILE" \
 | sed -E 's#.* /([0-9.]+)/.*#envoy \1#' >> "$OUT" || true
grep -E '^nginx version:' "$REPORT_FILE" \
 | sed -E 's#^nginx version: nginx/([0-9.]+).*#nginx \1#' >> "$OUT" || true
grep -E '^(openjdk|java) version "' "$REPORT_FILE" \
 | sed -E 's/.* version "([0-9.]+)".*/java \1/' >> "$OUT" || true

# -------- 6) Non-RPM binaries (simple shapes) --------
awk '/^===== Non-RPM Binaries/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | grep -Eo '^[A-Za-z0-9._-]+ v[0-9]+([._-][0-9A-Za-z]+)*|^[A-Za-z0-9._-]+ [0-9]+([._-][0-9A-Za-z]+)*' \
 >> "$OUT" || true
awk '/^===== Non-RPM Binaries/{f=1;next} /^$/{f=0} f' "$REPORT_FILE" \
 | grep -Eo '[A-Za-z0-9._-]+/[0-9]+([._-][0-9A-Za-z]+)*' \
 | sed 's#/# #' >> "$OUT" || true

# -------- 7) JARs with vendor/app prefix from path --------
# We read each JAR block that looks like:
# -- /opt/<vendor>/.../something.jar --
#   Implementation-Title: X
#   Implementation-Version: Y
#   BOOT-INF/lib/xxx-1.2.3.jar
#
# Output:
#   <vendor> X Y
#   <vendor> xxx 1.2.3
awk '
  function flush_block(   vname,vers,ver_clean) {
    if (prefix != "") {
      if (impl_title != "" && impl_version != "") {
        ver_clean = impl_version
        sub(/[[:space:]].*$/, "", ver_clean)                # keep first token (e.g., "5.8.0" from "5.8.0 (b0)")
        print prefix, impl_title, ver_clean
      } else if (bundle_name != "" && bundle_version != "") {
        ver_clean = bundle_version
        sub(/[[:space:]].*$/, "", ver_clean)
        print prefix, bundle_name, ver_clean
      }
    }
    impl_title=""; impl_version=""; bundle_name=""; bundle_version=""
  }
  # Header line starts a new jar block:
  /^-- .*\.jar --$/ {
    # flush previous
    flush_block()
    prefix=""

    # extract jar path
    jar=$0
    sub(/^--[ ]*/, "", jar)
    sub(/[ ]*--$/, "", jar)

    # vendor/app prefix: if path is under /opt/<vendor>/..., use that <vendor>
    if (match(jar, "^/opt/([^/]+)", m)) prefix=m[1]
    next
  }

  /^Implementation-Title:/   { sub(/^Implementation-Title:[ ]*/, "", $0); impl_title=$0; next }
  /^Implementation-Version:/ { sub(/^Implementation-Version:[ ]*/, "", $0); impl_version=$0; next }

  /^Bundle-Name:/            { sub(/^Bundle-Name:[ ]*/, "", $0); bundle_name=$0; next }
  /^Bundle-Version:/         { sub(/^Bundle-Version:[ ]*/, "", $0); bundle_version=$0; next }

  # Spring Boot nested libs
  /BOOT-INF\/lib\/.*\.jar/ {
    if (prefix != "" && match($0, /BOOT-INF\/lib\/([A-Za-z0-9_.+-]+)-([0-9][0-9A-Za-z.+:-]*)\.jar/, m)) {
      print prefix, m[1], m[2]
    }
    next
  }

  END { flush_block() }
' "$REPORT_FILE" >> "$OUT" || true

# -------- 8) Finalize --------
# trim empties & dedupe
sed -i 's/[[:space:]]\+$//' "$OUT"
sed -i '/^[[:space:]]*$/d' "$OUT"
sort -u "$OUT" -o "$OUT"

echo "Versions-only list saved to: $OUT"
