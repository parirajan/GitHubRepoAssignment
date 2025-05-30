#!/bin/bash

# Usage:
# ./dedupe_json_by_uid_stream.sh input.json message loadFileJob mandator > output.json

input_file="$1"
shift
stream_types=("$@")

# Convert stream types to an awk-readable list
stream_list=$(IFS=, ; echo "${stream_types[*]}")

awk -v streams="$stream_list" '
BEGIN {
  # Split stream type list into an array
  n = split(streams, sArr, /,/)
  for (i = 1; i <= n; i++) {
    valid_streams[sArr[i]] = 1
  }
}

/"streamType"/ && /"uid"/ {
  match($0, /"streamType"[[:space:]]*:[[:space:]]*"[^"]+"/, st)
  match($0, /"uid"[[:space:]]*:[[:space:]]*[0-9]+/, uidmatch)

  if (st[0] != "" && uidmatch[0] != "") {
    # Extract and clean streamType
    split(st[0], a, ":")
    gsub(/"/, "", a[2])
    stream = gensub(/^[ \t]+/, "", "g", a[2])

    # Extract and clean uid
    split(uidmatch[0], b, ":")
    uid = gensub(/^[ \t]+/, "", "g", b[2]) + 0

    key = stream "_" uid

    if (stream in valid_streams) {
      if (!(key in seen)) {
        seen[key] = 1
        print
      }
      next
    }
  }

  # Print all non-target streamType lines
  print
}
' "$input_file"
