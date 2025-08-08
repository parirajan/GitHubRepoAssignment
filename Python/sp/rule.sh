#!/bin/bash
set -euo pipefail

RULES_DIR="/etc/audit/rules.d"

# Safety: ensure there are .rules files to process
shopt -s nullglob
files=( "$RULES_DIR"/*.rules )
if [ ${#files[@]} -eq 0 ]; then
  echo "No .rules files found in $RULES_DIR"
  exit 0
fi

# Process all .rules in one AWK pass and write per-file .tmp outputs
awk '
  BEGIN {
    # nothing
  }
  FNR==1 {
    cur = FILENAME
    out = cur ".tmp"
  }

  # Pass through blank or already-commented lines unchanged
  /^\s*$/ || /^\s*#/ {
    print $0 > out
    next
  }

  {
    line = $0

    # Record the first file (by input order) that ever saw this exact line
    if (!(line in first_file)) {
      first_file[line] = cur
    }

    # Count occurrences of this exact line within this current file
    key = cur SUBSEP line
    occ[key]++

    # Keep rule only if:
    #  - this file is the first file that introduced the line, and
    #  - this is the first occurrence in this file
    if (first_file[line] == cur && occ[key] == 1) {
      print line > out
    } else {
      print "# " line > out
    }
  }
' "${files[@]}"

# Backup originals, replace with .tmp
for f in "${files[@]}"; do
  cp -f -- "$f" "$f.bak"
  mv -f -- "$f.tmp" "$f"
done

# Optional: comment out invalid RHEL9-style exclude rules (safe to keep here)
for f in "${files[@]}"; do
  sed -i 's/^-\(a[[:space:]]\+exclude.*\)$/# -\1/' "$f"
done

# Reload compiled audit rules
if command -v augenrules >/dev/null 2>&1; then
  echo "Reloading audit rules..."
  /usr/sbin/augenrules --load
fi

echo "Cross-file deduplication complete."
