First_list_one = [1,2,5,6,2]
First_list_two = [1,2,5,6,2]

Second_list_one = [1,2,5,6,5]
Second_list_two = [1,2,5,6,5,3]

Third_list_one = [1,2,5,6,5,16]
Third_list_two = [1,2,5,6,5]

Fourth_list_one = ['celery','carrots','bread','milk']
Fourth_list_two = ['celery','carrots','bread','cream']

cmplist = raw_input("Select the one of the item - l1, l2, l3, l4 - ")
print "Your Selection is - ", cmplist

if cmplist == 'l1':
  list_one = First_list_one[:]
  list_two = First_list_two[:]
  if cmp(list_one, list_two) == 0:
    print "Identical List"
  else:
    print "Non-Identical List"

elif cmplist == 'l2':
  list_one = Second_list_one[:]
  list_two = Second_list_two[:]
  if cmp(list_one, list_two) == 0:
    print "Identical List"
  else:
    print "Non-Identical List"


elif cmplist == 'l3':
  list_one = Third_list_one[:]
  list_two = Third_list_two[:]
  if cmp(list_one, list_two) == 0:
    print "Identical List"
  else:
    print "Non-Identical List"


elif cmplist == 'l4':
  list_one = Fourth_list_one[:]
  list_two = Fourth_list_two[:]
  if cmp(list_one, list_two) == 0:
    print "Identical List"
  else:
    print "Non-Identical List"

else:
  print "Not a valid Selection"
