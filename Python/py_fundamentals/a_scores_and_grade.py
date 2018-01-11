import random
a = 60
b = 100
print "Scores and Grades"
for i in range(10):
  random_num = random.randint(a,b)
  if  60 <= random_num <= 69:
    print "Score:", random_num, "Your Grade is - D"
  elif 70 <= random_num <=79:
    print "Score:", random_num, "Your Grade is - C"
  elif 80 <= random_num <=89:
    print "Score:", random_num, "Your Grade is - B"
  elif 90 <= random_num <=100:
    print "Score:", random_num, "Your Grade is - A"
print "End of the program. Bye!"
  

