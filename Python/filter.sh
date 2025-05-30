#!/bin/bash

# Usage:
# ./dedupe_by_stream_and_uid.sh message loadFileJob mandator input.json > filtered.json

# Extract the input file (last argument)
input_file="${@: -1}"
# All other args are streamTypes
stream_types=("${@:1:$#-1}")

# Generate -v args for each stream type
awk_vars=""
for i in "${!stream_types[@]}"; do
  awk_vars+=" -v st${i}=${stream_types[$i]}"
done

awk $awk_vars '
BEGIN {
  # Load streamTypes into a lookup table
  for (i = 0; i < 100; i++) {
    varname = "st" i
    if (!(varname in ENVIRON)) break
    valid[ENVIRON[varname]] = 1
  }
}

/"streamType"/ && /"uid"/ {
  # Extract streamType
  match($0, /"streamType"[[:space:]]*:[[:space:]]*"[^"]+"/, st)
  match($0, /"uid"[[:space:]]*:[[:space:]]*[0-9]+/, uidmatch)

  if (st[0] != "" && uidmatch[0] != "") {
    # Clean up streamType
    split(st[0], a, ":")
    gsub(/"/, "", a[2])
    stream = gensub(/^[ \t]+/, "", "g", a[2])

    # Clean up uid
    split(uidmatch[0], b, ":")
    uid = gensub(/^[ \t]+/, "", "g", b[2]) + 0

    key = stream "_" uid

    if (stream in valid) {
      if (!(key in seen)) {
        seen[key] = 1
        print
      }
      next  # skip duplicate for same stream+uid
    }
  }

  # For lines without valid streamType match, print as-is
  print
}
' "$input_file"
