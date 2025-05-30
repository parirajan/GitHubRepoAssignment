#!/bin/bash

# Usage:
# ./filter_by_streamtypes.sh message loadFileJob mandator input.json > filtered.json

input_file="${@: -1}"                    # last argument is input file
stream_types=("${@:1:$#-1}")             # all except last arg

# Pass each stream type as a separate -v var
awk_args=""
for i in "${!stream_types[@]}"; do
  awk_args+=" -v s$i=\"${stream_types[$i]}\""
done

awk $awk_args '
BEGIN {
  # Initialize valid streamType list
  for (i = 0; i < 100; i++) {
    if (("s" i) in ENVIRON) {
      valid_streams[ENVIRON["s" i]] = 1
    } else {
      break
    }
  }
}

/"streamType"/ && /"uid"/ {
  match($0, /"streamType"[[:space:]]*:[[:space:]]*"[^"]+"/, st)
  match($0, /"uid"[[:space:]]*:[[:space:]]*[0-9]+/, uidmatch)

  if (st[0] != "" && uidmatch[0] != "") {
    split(st[0], a, ":")
    gsub(/"/, "", a[2])
    stream = gensub(/^[ \t]+/, "", "g", a[2])

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

  print
}
' "$input_file"
