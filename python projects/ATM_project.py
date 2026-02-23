def ATM_UI ():
    print("n/ Loading....")
    print("Welcome to G.A.I.A banking services. How may we be of service to you")

User_credntial = []
account_balance = 0

def create_pin ():
    global User_credntial
    new_pin = int(input(f"create a new four digit *pin*"))
    print("Pin created successfully")
    User_credntial.append(new_pin)

def Login ():
    global User_credntial
    login_attempts = 3

    while login_attempts > 0:
        user_login = int(input("Enter your pin to access your bank account"))
        if user_login in User_credntial:
            print("hello Mr****")
            show_menu ()
        else:
            login_attempts -= 1
            print("Attempts: ",login_attempts,"left")
    if login_attempts == 0:
        print("Account locked. You have exceeded the pin access limit")

def show_menu ():
    while True:
        print("G.A.I.A banking srvices")
        print("1. Check balance ")
        print("2. Deposit money")
        print("3. Withdraw money")
        print("4. Logout")
        print("Press '1' to check your available balace '2' to deposit funds '3' to withdraw money")
        user_pick = int(input())
        if user_pick == 1:
            account_check ()
            break
        elif user_pick == 2:
            money_deposit ()
            break
        elif user_pick == 3:
            money_withdrawal ()
            break
        elif user_pick ==  4:
            logout ()
            break
        else:
            print("Invalid input. Try again")   
        
def money_deposit ():

    global account_balance
    new_deposit = int(input("Type amount of deposit"))
    print("Account balance updated. Thank you MR*** for choosing G.A.I.A banking services")
    account_balance += new_deposit
    print("Account balance =", account_balance,)
    menu_redirect ()
    

def account_check ():
    global account_balance
    print("Bank account =", account_balance,)
    menu_redirect

def money_withdrawal ():
    global account_balance
    print(account_balance)
    withdrawal = int(input("Type in amount to withdraw"))
    account_balance -= withdrawal
    print("Your current account balance is ", account_balance,)
    account_check ()
    menu_redirect
    

def callback ():
    request = input("G.A.I.A: What would you like to do next")
    show_menu ()
    if request == 1:
        account_check()
    elif request == 2:
        money_deposit ()
    elif request == 3:
        money_withdrawal ()
    elif request ==  4:
        logout ()
    else:
        print("Invalid input. Try again")


def logout ():
    print("Logged out. Goodbye")

    print("Showing UI")

def menu_redirect ():
    while True:
        user_confirmation = int(input("Enter '0' to go back to menu"))
        if user_confirmation == 0:
            show_menu ()
        elif user_confirmation != 0:
            print("Number must be 0. Try again")
        else:
            print("Enter '0' to access menu")

create_pin ()
Login ()