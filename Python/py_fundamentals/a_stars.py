def draw_stars (a,n):
    b=[]
    for i in a:
        i=i*n
        b.append(i)
    return b
a=[2,4,10,16]
for i in draw_stars(a,'*'):
  print i

print "_________________________________________________________________________________"


x = [4,'Tom',1,'Michael',5,7,'Jimmy Smith']
def draw_stars2(my_list):
    for item in my_list:
        output = ''
        if type(item) is int:
            for i in range(item):
                output += '*'
        elif type(item) is str:
            first_letter = item[0].lower()
            for i in range(len(item)):
                output += first_letter
        print output

draw_stars2(x)

print "_________________________________________________________________________________"

