users_db = {}
budgets = []

def show_UI(users_db):
    print("\nLunapay...")
    print("1. Sign Up")
    print("2. Log In")
    print("3. Exit")
    user_choice = int(input(""))
    if user_choice == 1:
        user_create_account(users_db)
    elif user_choice == 2:
        user_Login_account(users_db)
    elif user_choice == 3:
        exit_app()

def user_create_account(users_db):
    print("\nCreate Account")
    user_email = input("Email: ").strip() .lower()
    if user_email in users_db:
        print("This email is already linked to an existing account")
        return False
    
    while True:
        user_password = input("Password: ")
        confirm_password = input("Confirm password: ")
        if confirm_password != user_password:
            print("Password do not match! Try again")
            continue
        user = {
            "First_name": input("First name :"),
            "Last_name": input("Last name: "),
            "Email": user_email,
            "password": user_password
        }
        users_db[user_email] = user
        print("Account created successfully! Welcome to Lunapay ")
        user_Login_account(users_db)
        return True

def user_Login_account (users_db):
        print("\nLogin to your Lunapay")
        while True:
            user_Login_email = input("Email: ").strip() .lower()
            if user_Login_email not in users_db:
                print("User not found!")
                continue
            user_password_attempt_left = 3
            while user_password_attempt_left > 0:
                user_login_password = input("password: ")
        
                user_stored_password = users_db[user_Login_email]["password"]

                if user_login_password == user_stored_password:
                    print("Login successful!")
                    account = User_Bank_Account()
                    dashboard(account)
                    return True
                else:
                    user_password_attempt_left -= 1
                    print(f"Password incorrect! You have", user_password_attempt_left,"left")
            print("Number of attempts exceeded! Try again later")
            return False
def exit_app():
    print("\nAre you sure you  want to log out?")
    print("1. Yes")
    print("2. No")
    user_choice = int(input())
    if user_choice == 1:
        print("Logged out...See you next time")
    elif user_choice == 2:
        show_UI()
    else:
        print("Choose a number")

def dashboard(account):
    print("\n Menu Dashboard")
    print("1. View Acocunt balance") #View current Bank Account/Deposit funds/Withdraw deposit
    print("2. Income") # Add/Record/view Income
    print("3. Expense")# Add/Record/view Expenses
    print("4. Budgets") #Create/Edit/View Budget
    print("5. Reports") #create Reports
    print("6. Logout") # Logout
    user_choice = int(input())
    if user_choice == 1:
        view_balance(account)
        dashboard(account)
    elif user_choice == 2:
        income_menu(account)
    elif user_choice == 3:
        expense_menu(account)
    elif user_choice == 4:
        budget_menu()
    elif user_choice == 5:
        pass
    elif user_choice == 6:
        exit_app()
    else:
        print("Enter one of the numbers")
class User_Bank_Account:    
    def __init__(self):
        self.balance = 0
        self.incomes = []
        self.expenses = []
    
    def add_income(self,source_of_income, amount, date, notes): 
        self.incomes.append ({
            "source":source_of_income,
            "amount":amount,
            "date":date,
            "notes": notes
        })
        self.balance += amount
    
    def add_expenses(self,  source_of_expense, amount, date, notes): 
        self.expenses.append ({
        "source": source_of_expense,
        "amount": amount,
        "date": date,
        "notes": notes
        })
    def show_incomes(self):
        return self.incomes
    
    def show_expenses(self):
        return self.expenses
    
    def show_balance(self):
        total_income = sum(i["amount"] for i in self.incomes)
        total_expenses = sum(e["amount"] for e in self.expenses)
        self.balance = total_income - total_expenses
        return self.balance

def record_income(account):
    print("\n===Record Income===")
    source_of_income  = input("source: ")
    amount = int(input("Amount: "))
    date_of_income = input("DD/MM//YYYY")
    notes = input("Notes: ")
    account.add_income(source_of_income, amount, date_of_income, notes)
    print("\n===Income Logged successfully===")
    dashboard(account)

def record_expense(account):
    print("\n===Record Expenses====")
    source_of_expense = input("source: ")
    try:
        amount = int(input("Amount: "))
    except ValueError:
        print("amount must be in numbers")

    date_of_expense = input("DD/MM/YYYY")
    notes = input("Notes: ")
    account.add_expenses(source_of_expense, amount, date_of_expense, notes)
    print("\n===Expense Logged Successfully===")
    dashboard(account)

def view_income(account):
    print(account.show_incomes())

def view_expenses(account):
    print(account.show_expenses())

def view_balance(account):
    print(account.show_balance())

def budget_menu():
    print("\n===Budgets===")
    print("1. Create Budget")
    print("2. View Budgets")
    print("3. Edit Budget")
    print("4. Back")
    user_select = int(input())
    if user_select == 1:
        create_budget(budgets)
    elif user_select == 2:
        print(budgets)
    elif user_select == 3:
        pass
    elif user_select == 4:
        budget_menu()

class Budget_flow:
    def __init__(self):
        self.budgets = []

    def create_budget(self, budget_category, budget_limit, budget_time_period, budget_start_date):
        self.budgets.append ({
            "budget_category": budget_category,
            "budget_limit":budget_limit,
            "budget_time_period":budget_time_period,
            "budget_start_date":budget_start_date
        })
        budgets = Budget_flow()
        budget_menu(budgets)
    
    def view_budget(self):
        return self.budgets
    
    def edit_budget(self, category, budget_category, budget_limit, budget_time_period, budget_start_date):
        for budget in self.budgets:
            if budget["budget_category"] == category:
                budget.update({
                    "budget_category" : budget_category,
                    "budget_limit" : budget_limit,
                    "budget_time_period" : budget_time_period,
                    "budget_start_date" : budget_start_date
                })
                return f"budget updated successfully"
            return False, f"budget category not found"
def create_budget(budgets):
    print("\n===Create Budget===")
    category = input("Category: ")
    budget_limit = int(input("Budget Limit: "))
    budget_time_period = int(input("Time period: "))
    if budget_time_period < 7:
        print("Budget cannott be less than a week")
    budget_start_date = int(input("Start date of budget: "))
    budgets.add(category, budget_limit, budget_time_period, budget_start_date)
    print("\n===Budgret created successfully===")
    budgets = Budget_flow()
    budget_menu(budgets)
    return True

def income_menu(account):                   
    print("\n===Income Menu===")
    print("1. Add Income")
    print("2. View Incomes")
    print("0. Go back")
    user_select = int(input())
    if user_select == 1:
        record_income(account)
    elif user_select == 2:
        view_income(account)
    elif user_select == 3:
        dashboard(account)
    else:
        print("Please enter a valid number")




def expense_menu(account):
    print("\n===Expense Menu===")
    print("1 Add Expense")
    print("2. View Expenses")
    print("0. Go back")
    user_select = int(input())
    if user_select == 1:
        record_expense(account)
    elif user_select == 2:
        view_expenses(account)
    elif user_select == 0:
        dashboard(account)
    else:
        print("Please enter a valid number")

show_UI(users_db)




