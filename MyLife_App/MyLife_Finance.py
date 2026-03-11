#Finance tracker for MyLife app
from MyLife_Tracker import *

def get_user_record():
    current_user = ensure_current_user(current_user)
    if not current_user:
        return 
    
    data_loader = load_database()
    current_id = str(current_user)
    user = next((u for u in data_loader.get("users", []) if str(user.get("id")) == str(current_id)), None)
    if not user:
        print("user not found")
        return False
    
def Myfinance_dashboard_menu(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    
    while True:
        user = get_user_record(current_user)
        if not user:
            print("User not found")
            return False
        
        print("\nMyFinance")


# Features to be implemented in MyFinance:
# 1. Edit and delete finance entries.
# 2. Monthly budgets with category limits and alerts.
# 3. Recurring income and recurring expense support.
# 4. Export finance statements to CSV/PDF.
