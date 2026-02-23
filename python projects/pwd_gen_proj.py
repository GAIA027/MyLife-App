
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z' ]
numbers = ['0', '1', '2', '3', '4','5', '6', '7', '8', '9']
symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

import random

rand_letts = int(input("Hpw many letters would you like in your password?"))
rand_nums = int(input("How many numbers would you like to add?"))
rand_syms = int(input("and the symbols?"))

pwd_list = []
for char in range(0, rand_letts):
    pwd_list.append(random.choice(letters))
for char in range(0, rand_nums):
    pwd_list.append(random.choice(numbers))
for char in range(0, rand_syms):
    pwd_list.append(random.choice(symbols))

random.shuffle(pwd_list)

password = ""
for char in pwd_list:
    password += char

print("Your new password is", password)