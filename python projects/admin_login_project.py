Admin_login_credentials = []
User_1_login_credentials = []
user_2_login_credentials = []

print(" New operaying system loadinng....")


print("1. Admin")
print("2. User 1")
print("3. User 2")
user_pick = int(input("Select user? '1' '2' '3' "))


if user_pick == 1:
    Admin_create_password = input("Create a new password for admin")
    Admin_login_credentials.append(Admin_create_password)
    
    Admin_attempts = 3

    while Admin_attempts > 0:
        Admin_Login_Password = input("Enter your password to access")
        if Admin_Login_Password in Admin_login_credentials:
            print("Hello Admin")
            if user_pick == 1 and Admin_Login_Password == True:
                print("Showing Administrator panel")
            else:
                print("showing UI only")
            break
        else:
            Admin_attempts -= 1
            print("Incorrect password. You have", Admin_attempts,"attempts left")
    if Admin_attempts == 0:
        print("Account locked due to many password attempts")
elif user_pick == 2:
    User_1_create_password = input("Create a new password for user 1 ")
    User_1_login_credentials.append(User_1_create_password)

    user_1_attempts = 3
    while user_1_attempts > 0:
        
        User_1_Login_Password = input("Enter your password to access")
        if user_pick == 2 and User_1_Login_Password == True:
            print("Hello User 1")
            break
        elif user_pick != 1:
            print("Special access not granted. Must be admin to access panel ") 
        else:
            user_1_attempts -= 1
            print("Incorrect password. You have", user_1_attempts,"attempts left")
    if user_1_attempts == 0:
        print("Account locked due to many password attempts")
elif user_pick == 3:
    User_2_create_password = input("Create a new password for user 2")
    user_2_login_credentials.append(User_2_create_password)

    User_2_attempts = 3

    while User_2_attempts > 0:
        User_2_Login_password = input("Enter your password to access")
        if user_pick == 2 and User_2_Login_password == True:
            print("Hello User 2 ")
            break
        elif user_pick != 1:
            print("Special access not granted. Must be admin to access panel")
        else:
            User_2_attempts -= 1
            print("Wrong password. You have", User_2_attempts,"attempts remaining")
    if User_2_attempts == 0:
        print("Account locked due to too many attempts")


