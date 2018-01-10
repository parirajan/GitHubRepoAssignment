cols = 8
rows = 8

b = ' ' 
r = '*'

for num in range(rows):
    marker = ''
    if num %2 == 0:
        even = r
	odd = b
    else:
	even = b
	odd = r
    for inum in range(cols):
	if inum %2 == 0:
	    marker += even
	else:
	    marker += odd
    print marker
    

