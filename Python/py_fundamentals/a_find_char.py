word_list = ['hello','world','my','name','is','Anna']
char = 'o'

new_list = []
index = 0
for text in word_list:
    if char in text:
        new_list.insert(index, text)
        index += 1
        
print "new_list = ", new_list
