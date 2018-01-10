l1 = ['magical unicorns',19,'hello',98.98,'world']
l2 = [2,3,1,7,4,12]
l3 = ['magical','unicorns']

inlist = raw_input("Select the one of the item - l1, l2, l3 - ")
print "Your Selection is - ", inlist

if inlist == 'l1':
  i=l1
  t = None
  for t in (i):
    if t is None:
      t = type(i)
      print "The list you entered is ", t, "type"
    elif type(i) != t:
      print "The list you entered is of mixed type"
      break
  
  myIntList = [x for x in i if isinstance(x, (int, float, long, complex))]
  print "The Number List - ", myIntList
  Total = sum(myIntList)
  print "The sum of Number List is -", Total
  myStrList = [x for x in i if isinstance(x, (str,unicode,basestring))]
  print "The String List - ", myStrList
  print "The Elements in String List is - ", (' '.join(map(str, myStrList)))

elif inlist == 'l2':
  i=l2
  t = None
  for t in (i):
    if t is None:
      t = type(i)
      print "The list you entered is ", t, "type"
    elif type(i) != t:
      print "The list you entered is of mixed type"
      break

  myIntList = [x for x in i if isinstance(x, (int, float, long, complex))]
  print "The Number List - ", myIntList
  Total = sum(myIntList)
  print "The sum of Number List is -", Total
  myStrList = [x for x in i if isinstance(x, (str,unicode,basestring))]
  print "The String List - ", myStrList
  print "The Elements in String List is - ", (' '.join(map(str, myStrList)))

elif inlist == 'l3':
  i=l3
  t = None
  for t in (i):
    if t is None:
      t = type(i)
      print "The list you entered is ", t, "type"
    elif type(i) != t:
      print "The list you entered is of mixed type"
      break

  myIntList = [x for x in i if isinstance(x, (int, float, long, complex))]
  print "The Number List - ", myIntList
  Total = sum(myIntList)
  print "The sum of Number List is -", Total
  myStrList = [x for x in i if isinstance(x, (str,unicode,basestring))]
  print "The String List - ", myStrList
  print "The Elements in String List is - ", (' '.join(map(str, myStrList)))

else:
  print "Not a Valid Selection"
