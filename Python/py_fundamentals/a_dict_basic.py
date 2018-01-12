import itertools
cancel = False
#personal_info = []
personal_info = {}

while (True):
  initials = raw_input("Please enter the Initials:")
  name = raw_input("Please enter the Name:")
  age = raw_input("Please enter the Age:")
  country = raw_input("Please enter the country of Birth:")
  language = raw_input("Please enter your Favorite Language:")

  personal_info.update({
    "Initials": initials,
    "Name": name,
    "Age": int(age),
    "Country": country,
    "Language": language,
  })
  break;
#  cont = raw_input("Do you want to add another entry? (Y/N)")
#  if cont == "N":
#    break;

print(personal_info)

for key,data in personal_info.iteritems():
  if key == "Name":
    print "My name is", data
  elif key == "Age":
    print "My age is", data
  elif key == "Country":
    print "My country of birth is", data
  elif key == "Language":
    print "My favorite language is", data

