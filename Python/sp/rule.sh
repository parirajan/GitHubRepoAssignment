#!/bin/bash

RULES_DIR="/etc/audit/rules.d"
TMPDIR=$(mktemp -d)
SEEN_FILE="$TMPDIR/seen.txt"

# First pass: collect all unique rules (ignoring comments and blanks)
grep -hvE '^\s*#|^\s*$' "$RULES_DIR"/*.rules | \
  awk '!seen[$0]++ { print $0 }' > "$SEEN_FILE"

# Second pass: process each file and comment out duplicates
for file in "$RULES_DIR"/*.rules; do
  echo "Processing $file..."
  tmpfile=$(mktemp)

  awk -v seen_file="$SEEN_FILE" '
    BEGIN {
      while ((getline line < seen_file) > 0) {
        seen[line] = 1
      }
      close(seen_file)
    }
    /^\s*$/ || /^\s*#/ { print; next }
    {
      if (seen[$0]) {
        print $0
        seen[$0] = 0  # Keep only first instance
      } else {
        print "# " $0
      }
    }
  ' "$file" > "$tmpfile"

  cp "$file" "$file.bak"
  mv "$tmpfile" "$file"
done

# Comment out invalid RHEL 9 'exclude' rules
for file in "$RULES_DIR"/*.rules; do
  sed -i 's/^-\(a[[:space:]]\+exclude.*\)$/# -\1/' "$file"
done

# Reload audit rules
echo "Reloading audit rules..."
/usr/sbin/augenrules --load && echo "audit.rules updated."

# Cleanup
rm -rf "$TMPDIR"
