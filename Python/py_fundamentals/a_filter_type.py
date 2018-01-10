#import pdb
#pdb.set_trace()

sI = 45
mI = 100
bI = 455
eI = 0
spI = -23
sS = "Rubber baby buggy bumpers"
mS = "Experience is simply the name we give our mistakes"
bS = "Tell me and I forget. Teach me and I remember. Involve me and I learn."
eS = ""
aL = [1,7,4,21]
mL = [3,5,7,34,3,2,113,65,8,89]
lL = [4,34,22,68,9,13,3,5,7,9,2,12,45,923]
eL = []
spL = ['name','address','phone number','social security number']

#for i in (sI,mI,bI,eI,spI,sS,mS,bS,eS,aL,mL,lL,eL,spL):
name = raw_input("Select the one of the item - sI,mI,bI,eI,spI,sS,mS,bS,eS,aL,mL,lL,eL,spL - ")
print "Your Selection is - ", name

if name == 'sI':
  i=sI
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'mI':
  i=mI
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'bI':
  i=bI
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'eI':
  i=eI
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'spI':
  i=spI
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'sS':
  i=sS
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'mS':
  i=mS
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'bS':
  i=bS
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'eS':
  i=eS
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'aL':
  i=aL
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'mL':
  i=mL
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'lL':
  i=lL
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'eL':
  i=eL
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


elif name == 'spL':
  i=spL
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"


else:
  i=None
  if isinstance(i, (int, float, long, complex)) and (i >= 100):
    print i, "- is a Big Number"
  if isinstance(i, (int, float, long, complex)) and (i < 100):
    print i, "- is a Small Number"

  if isinstance(i, (str,unicode,basestring)) and (len(i) >= 50):
    print i, "- is a Long Sentance"
  if isinstance(i, (str,unicode,basestring)) and (len(i) < 50) and len(i) != 0:
    print i, "- is a Short Sentance"
  if isinstance(i, (str,unicode,basestring)) and len(i) == 0:
    print i, "- Empty String"

  if isinstance(i, list) and (len(i) >= 10):
    print i, "- Big List"
  if isinstance(i, list) and (len(i) < 10) and len(i) != 0:
    print i, "- Short List"
  if isinstance(i, list) and len(i) == 0:
    print i, "- No Elements in the List"

  if i is None:
    print "Selection not Valid"
