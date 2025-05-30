#!/bin/bash

# Usage:
# ./dedupe_json_by_uid_stream.sh input.json message loadFileJob mandator > filtered.json

input_file="$1"
shift
stream_types=("$@")

# Convert stream types to a comma-separated list
stream_list=$(IFS=, ; echo "${stream_types[*]}")

awk -v streams="$stream_list" '
BEGIN {
  # Parse the input list of stream types into an associative array
  n = split(streams, sArr, ",")
  for (i = 1; i <= n; i++) {
    target_streams[sArr[i]] = 1
  }
}

{
  # Match the streamType and uid from each line
  match($0, /"streamType"[[:space:]]*:[[:space:]]*"[^"]+"/, st)
  match($0, /"uid"[[:space:]]*:[[:space:]]*[0-9]+/, uidmatch)

  if (st[0] != "" && uidmatch[0] != "") {
    split(st[0], a, ":")
    gsub(/"/, "", a[2])
    stream = gensub(/^[ \t]+/, "", "g", a[2])

    split(uidmatch[0], b, ":")
    uid = gensub(/^[ \t]+/, "", "g", b[2]) + 0

    key = stream "_" uid

    if (stream in target_streams) {
      if (!(key in seen)) {
        seen[key] = 1
        print
      }
      next  # Skip duplicate for targeted streamTypes
    }
  }

  # Print all lines that do not match targeted streamTypes
  print
}
' "$input_file"
