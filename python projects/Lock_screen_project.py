user_pwd = []

def set_pwd ():
    global user_pwd
    print("Welcome....")
    new_pwd = input("Set a new password for your device")
    user_pwd.append(new_pwd)
    while True:
        conf_pwd = input("Enter your password again to confirm")
        if conf_pwd in user_pwd:
            print("New password set successfully")
            break
        else:
            print("passwords do not match. Try again")

def acc_devc ():
    global user_pwd
    acc_att = 3
    while acc_att > 0:
            Acc_pwd = input("Enter your password to unlock")
            if Acc_pwd in user_pwd:
                print("Unlocked")
                break
            else:
                acc_att -= 1
            print("Wrong password. You have", acc_att,"left")
    if acc_att == 0:
        print("Device locked for 15 minutes")

def apps_sec ():
    user_pick = input("Enter '1' to enter bank app")
    print("1. Bank App")
    from ATM_project import Login, show_menu, money_deposit, money_withdrawal, callback, logout, menu_redirect, create_pin, account_balance, account_check, User_credntial
    if user_pick == 1:
        create_pin ()
        Login

def app_page ():
    main_pg = input("Enter '0' to Exit app")
    if main_pg == 0:
        app_page ()

set_pwd ()
acc_devc ()
apps_sec ()
