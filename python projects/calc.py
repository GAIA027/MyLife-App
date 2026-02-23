#Calculator program that can add, subtract, multipy, and divide

def addition(a, b):
    return a + b

def subtraction(a, b):
    return a - b

def multiplication(a, b):
    return a * b

def division(a, b):
    if b == 0:
        return False, f"Cannot divide by zero."
    else:
        return a / b


def calc_menu():
    print("\n===Calculator===")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Exit")
    user_select = int(input())
    if user_select == 1:
        add_calc()
    elif user_select == 2:
        subtract_calc()
    elif user_select == 3:
        multiply_calc()
    elif user_select == 4:
        divide_calc()
    elif user_select == 5:
        exit()
    else:
        print("Enter a valid number")

def add_calc():
    print("==Addition==")
    print("Enter '/' to go back to menu")
    num_1 = int(input("Enter first number"))
    num_2 = int(input("Enter second number"))
    print(addition(num_1, num_2))
    calc_menu()

def subtract_calc():
    num_1 = int(input("Enter first number"))
    num_2 = int(input("Enter second number"))
    print(subtraction(num_1, num_2))
    calc_menu()

def multiply_calc():
    num_1 = int(input("Enter first number"))
    num_2 = int(input("Enter second number"))
    print(multiplication(num_1, num_2))
    calc_menu()

def divide_calc():
    num_1 = int(input("Enter first number"))
    num_2 = int(input("Enter second number"))
    print(division(num_1, num_2))
    calc_menu()

def exit():
    print("\n===Exit===")
    user_pick = input("\nAre you sure you wnat to exit")
    print("1. Yes")
    print("2. Go back")
    if user_pick == 1:
        print("Exiting..Bye")
    elif user_pick == 2:
        calc_menu()
    else:
        print("Enter a valid number")

calc_menu()