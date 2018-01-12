name = ["Anna", "Eli", "Pariece", "Brendan", "Amy", "Shane", "Oscar"]
favorite_animal = ["horse", "cat", "spider", "giraffe", "ticks", "dolphins", "llamas"]

def make_dict(list1, list2):
  new_dict = {}
  print "Tuple from the input List"
  tup = zip (list1, list2)
  print tup
  new_dict = dict(tup)
  print "Dictionary from the input List"
  print new_dict

make_dict(name,favorite_animal)
