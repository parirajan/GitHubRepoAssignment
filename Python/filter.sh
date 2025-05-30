#!/bin/bash

# Usage: ./filter_by_streamtypes.sh message loadFileJob mandator input.json > filtered.json

# Collect stream types from all args except last (input file)
input_file="${@: -1}"                    # last argument is the input file
stream_types=("${@:1:$#-1}")             # everything but the last argument

# Build AWK array initializer from stream_types
awk_array_init=""

for stream in "${stream_types[@]}"; do
  awk_array_init+="valid_streams[\"$stream\"] = 1; "
done

awk -v array_init="$awk_array_init" '
BEGIN {
  eval(array_init);  # Initialize valid_streams array from shell
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

    # Extract UID
    split(uidmatch[0], b, ":")
    uid = gensub(/^[ \t]+/, "", "g", b[2]) + 0

    # Check against streamType list
    key = stream "_" uid

    if (stream in valid_streams) {
      if (!(key in seen)) {
        seen[key] = 1
        print
      }
      next  # suppress repeated streamType+uid pairs
    }
  }

  print  # lines that don’t match or are outside target streamTypes
}
' "$input_file"
