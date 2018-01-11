import random

x = 0
y = 1

a = 0
z = 0
o = 0

for i in range(5000):
  coin_toss = random.randint(x,y)
  a = a+1
  if coin_toss == 0:
    z = z+1
    print "Attempt #",a,": Throwing a coin... It's a head! ... Got ",z," head(s) so far and ,",o," tail(s) so far"
  else:
    o = o+1
    print "Attempt #",a,": Throwing a coin... It's a tail! ... Got ",z," head(s) so far and ,",o," tail(s) so far"


