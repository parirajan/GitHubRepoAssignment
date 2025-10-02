jq -r '
  ([["Name","Version"]] +
   (.components | map(select(.version != null and .version != "") | [ .name, .version ]))
  )
  | .[]
  | @tsv
' bom.json \
| awk 'BEGIN{FS="\t"; OFS=" | "} NR==1{print "| " $1 " | " $2 " |"; print "|---|---|"} NR>1{print "| " $1 " | " $2 " |"}'
