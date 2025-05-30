#!/bin/bash

# Usage:
# ./dedupe_json_by_uid_stream.sh input.json message loadFileJob mandator > filtered.json

input_file="$1"
shift
stream_types=("$@")

# Convert stream types to an awk-readable list
stream_list=$(IFS=, ; echo "${stream_types[*]}")

awk -v streams="$stream_list" '
BEGIN {
  # Load list of streamTypes to deduplicate
  n = split(streams, sArr, /,/)
  for (i = 1; i <= n; i++) {
    target_streams[sArr[i]] = 1
  }
}

/"streamType"/ && /"uid"/ {
  # Extract streamType
  match($0, /"streamType"[[:space:]]*:[[:space:]]*"[^"]+"/, st)
  match($0, /"uid"[[:space:]]*:[[:space:]]*[0-9]+/, uidmatch)

  if (st[0] != "" && uidmatch[0] != "") {
    split(st[0], a, ":")
    gsub(/"/, "", a[2])
    stream = gensub(/^[ \t]+/, "", "g", a[2])

    split(uidmatch[0], b, ":")
    uid = gensub(/^[ \t]+/, "", "g", b[2]) + 0

    key = stream "_" uid

    # If it's a target streamType, deduplicate
    if (stream in target_streams) {
      if (!(key in seen)) {
        seen[key] = 1
        print
      }
      next  # Skip duplicates for streamTypes we’re filtering
    }
  }

  # For all other streamTypes (non-target), always print
  print
}
' "$input_file"
