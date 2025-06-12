asadm -e "show statistics like defrag_q" | awk -v ns="test" '
  $0 ~ "Namespace "ns" Statistics" { found=1; next }
  found && /defrag_q/ {
    print $NF
    found=0
  }'



asadm -e "show statistics like defrag_q" | awk -F'|' 'NR>1 { for (i=2; i<=NF; i++) { gsub(/[ \t]+/, "", $i); if ($i ~ /^[0-9]+$/) print $i } }'
