asadm -e "show statistics like defrag_q" | awk -v ns="test" '
  $0 ~ "Namespace "ns" Statistics" { found=1; next }
  found && /defrag_q/ {
    print $NF
    found=0
  }'



asadm -e "show statistics like defrag_q" | awk -v ns="your_namespace" '$0 ~ "Namespace "ns" Statistics" { f=1; next } f && /defrag_q/ { print $NF; f=0 }'
