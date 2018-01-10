#word_list = ['hello','world','my','name','is','Anna']
#char = 'o'

word_list = []
wl = 0

el = raw_input("Enter the Number of Elements in the Word_List: ")
while wl != int(el):
  li = raw_input("Enter the Element to the Word_list: ")
  word_list.append(li)
  wl = wl + 1
    
print "word_list = ", word_list

char = raw_input("Enter the character to find in the elements in word_list: ")

print "char = ", char

new_list = []
index = 0
for text in word_list:
    if char in text:
        new_list.insert(index, text)
        index += 1
        
print "new_list = ", new_list
