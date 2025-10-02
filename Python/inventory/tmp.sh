jq -r '
  ([["Name","Version"]] +
   (.components | map(select(.version != null and .version != "") | [ .name, .version ]))
  )
  | .[]
  | @tsv
' bom.json \
| column -t -s$'\t' \
| sed '1s/^/| /; 1s/$/ |/; 2,$s/^/| /; 2,$s/$/ |/' \
| sed '2i|---|---|'
