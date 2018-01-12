my_dict = {}

while (True):
  name = raw_input("Please enter the Name:")
  phone = raw_input("Please enter the Contact Phone Number:")

  Name = name
  Phone = phone


  def my_dict_fn(name,phone):
    my_dict.update({
      name:phone
    })

  my_dict_fn(name,phone)

  cont = raw_input("Do you want to add another entry? (Y/N)")
  if cont == "N":
    break;


print my_dict
print my_dict.items()

