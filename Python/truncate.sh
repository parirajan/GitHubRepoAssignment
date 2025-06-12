asadm -e "show statistics like defrag_q" | awk -v ns="test" '
  $0 ~ "Namespace "ns" Statistics" { found=1; next }
  found && /defrag_q/ {
    print $NF
    found=0
  }'
