def oddeven(x):
    count=0
    for i in range(x):
      if i % 2 == 0:
        count+=1
        print "Number is:",count,"- This is odd number."
      elif i % 2 == 1:
        count+=1
        print "Number is:",count,"- This is even number."

oddeven(2000)
print "_________________________________________________"



def multiply(arr,num):
    for x in range(len(arr)):
        arr[x] *= num
    return arr
a = [2,4,10,16]
b = multiply(a,5)
print b
print "_________________________________________________"


def layered_multiples(arr):
    print arr
    new_array = []
    for x in arr:
        val_arr = []
        for i in range(0,x):
            val_arr.append(1)
        new_array.append(val_arr)
    return new_array
x = layered_multiples(multiply([2,4,5],3))
print x
print "_________________________________________________"
