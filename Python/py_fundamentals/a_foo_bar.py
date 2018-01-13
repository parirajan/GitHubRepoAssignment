b = int(input("Enter Starting number: "))
e = int(input("Enter Ending number: "))

def is_perfect_square(n):
    x = n // 2
    y = set([x])
    while x * x != n:
        x = (x + (n // x)) // 2
        if x in y: return False
        y.add(x)
    return True
 
def is_prime_number(n):
  for i in range(2, n):
      if n % i == 0:
          return False
          break
      else: 
          return True


for n in range(b,e):
  for i in range(2,n):
    if is_perfect_square(n) == True:
      print "Number:",n,"- Perfect Square - FOO"
      break
    elif is_prime_number(n) == True:
      print "Number:", n, "- Prime Number - BAR"
      break
    else:
      print "Number:",n," - Not Prime and Not Perfect Square - FOOBAR"
      break
