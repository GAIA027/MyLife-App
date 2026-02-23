try:
    from wonderwords import RandomWord

    r = RandomWord()

    randomized_word = r.word(word_min_lengh=5, word_max_length=7).lower()

except:
    import random

    random_word : list[str] = ["Apple", "Hierachy", "Typograpy", "alignment", "Orange"]

    random_word = random.choice(random_word)

#Task 1

def square_number(number : int) -> int:
    return number * number
#Task 2 
def register_username(username : str, email : str, age : int) -> dict:
    if not age >= 13:
        raise ValueError("Age must be above 13")
    return {
        "username" : username,
        "Email" : email,
    }
# Task 3
def get_discount(code : str) -> Optional[int]:
    if code == "SAVE10":
        return f"You have applied 10% discount on your purchase"
    return None, f"Invalid code"
#Task IV
def is_admin(role : str) -> bool:
    if role == "admin":
        return True
    
#Task 5
def calculate_order_total(price: float, quantity : int, tax_rate : float) -> float:
    final_price = price * quantity * (1 + tax_rate)
    return final_price
#Phase one mini project 1
from typing import Optional
import random
import string

class User:
    def __init__(self) -> None:
        self.users_db : list[dict[str, str | int]] = []

    def create_user_id(self, length = 8) -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k = length))
    
    def create_user(self, username : str, password : str, email : str, age : int) -> dict[str, str | int]:
        for user in self.users_db:
            if user["username"] == username:
                raise ValueError("Username already exists")
            
        if len(password) < 5:
            raise ValueError("Password length must be longer than 5 characters")
        
        for user in self.users_db:
            if user["email"] == email:
                return f"Username already exists"
            
        if age < 13:
            raise ValueError("You must be above the age of 13")
        
        new_user = {
            "ID : " : self.create_user_id(),
            "username : " : username,
            "password : " : password,
            "email : " : email,
            "age : " : age
        }
        self.users_db.append(new_user)
        return new_user
    
    def delete_user(self, user_delete_request : str) -> bool:
        for user in self.users_db:
            if user["username"] == user_delete_request:
                self.users_db.remove(user)
                return True
            return None
        
    def get_user_info(self, username_check : str) -> Optional[dict[str, str | int]]:
        for user in self.users_db:
            if user["username"] == username_check:
                return user
            return None

#Collection typing and complex typing

def filter_user(users : list[str]) -> list[str]:
    return [user for user in users if user.startswith("active")]

#Task 1

def get_even_numbers(numbers : list[int]) -> list[int]:
    for number in numbers(range(1, 101)):
        if number % 2 == 0:
            return number

#Task 2

def get_username(user : list[dict[str, str]]) -> list[str]:
    users_db : list[dict[str, str | int]] = []
    for user in users_db:
        return user
    
#Task 3 
from typing import Optional
def find_user(users : list[dict[str, str]], username : str) -> Optional[dict[str, str]]:
    users : list[dict[str, str]] = []
    for user in users:
        if user in users:
            return user
        return None
#Task IV

def calculate_total_price(cart : list[dict[str, int | float]], price : int | float, quantity : str) -> float:
    overall_cart = []
    for cart in overall_cart:
        if cart in overall_cart:
            return price * quantity

#Task 5
def group_users_by_age(users : list[dict[str, str | int]]) -> dict[str, list[dict[str, str | int]]]:
    age_groups = {
        "child" : [],
        "teen" : [],
        "adult" : []
    }
    for user in users:
        if user["age"] < 13:
            age_groups["child"].append(user)
        elif 13 <= user["age"] < 18:
            age_groups["teen"].append(user)
        else:
            age_groups["adult"].append(user)
    return age_groups

# phase one mini project 2 
inventory = []
def create_order(product_name : str, product_price : int | float, product_quantity : int) -> list[dict[str, str | int | float]]:
    new_order = {
        "product_name" : product_name,
        "product_price" : product_price,
        "product_quantity" : product_quantity
    }
    inventory["orders"].append(new_order)
    return new_order

def get_order() -> list[dict[str, str | int | float]]:
    for order in inventory["orders"]:
        if order["product name"]:
            return order
        
from typing import final

def find_expensive_orders(threshold : float) -> list[dict[str, float]]: 
    above_value_price  : final[int] = 5000
    if threshold in inventory["orders"] > above_value_price:
        return threshold

#password hash practice
import hashlib

def hash_password(password : str) -> str:
    return hashlib.sha256(password.encode()).hexidigest()

def verify_password(input_password : str, stored_password : str) -> bool:
    return hash_password(input_password) == stored_password



import random
import string

def generate_id(length = 10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k = length))

print(generate_id())


from typing import Optional

#Task 1 
class ProductRepository:
    def __init__(self, products : list[dict[str, str | int | float]]):
        self.products = products

    def find_by_id(self, product_id : int) -> bool:
        ([product for product in self.products if product["id"] == product_id])

class ServiceLayer:
    def __init__(self, repository : ProductRepository):
        self.repository = repository

    def get_product(self, product_id):
        product = ProductRepository.find_by_id(product_id)

        if product is None:
            raise ValueError("Produc not found")
        
        return float(product["price"])
    

from dataclasses import dataclass

@dataclass
class Order:
    order_id : int
    product_id : int
    quantity : int
    total : float


#Creating an instance in dataclass
order = Order(
    
)