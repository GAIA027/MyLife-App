# Finance tracker for MyLife app
import json
from pathlib import Path
from typing import Any

from app.modules.MyLife_Tracker import *


finance_database = Path(__file__).resolve().parents[2] / "data" / "finance.json"


def load_finance_database() -> dict[str, list[dict[str, Any]]]:
    if not finance_database.exists():
        return {
            "accounts": [],
            "categories": [],
            "transactions": [],
        }

    with open(finance_database, "r") as finance_file:
        return json.load(finance_file)


def save_finance_database(finance_data: dict[str, list[dict[str, Any]]]) -> None:
    with open(finance_database, "w") as finance_file:
        json.dump(finance_data, finance_file, indent=4)


def get_user_record(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None

    data_loader = load_database()
    current_id = str(current_user.get("id"))
    user = next(
        (u for u in data_loader.get("users", []) if str(u.get("id")) == current_id),
        None,
    )
    if not user:
        print("User not found")
        return None
    return user


def _finance_record_belongs_to_user(record: dict[str, Any], current_user_id: str) -> bool:
    record_user_id = record.get("user_id")
    return record_user_id is None or str(record_user_id) == current_user_id


def get_user_finance_records(current_user: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]] | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None

    finance_data = load_finance_database()
    current_id = str(current_user.get("id"))

    return {
        "accounts": [
            account for account in finance_data.get("accounts", [])
            if _finance_record_belongs_to_user(account, current_id)
        ],
        "categories": [
            category for category in finance_data.get("categories", [])
            if _finance_record_belongs_to_user(category, current_id)
        ],
        "transactions": [
            transaction for transaction in finance_data.get("transactions", [])
            if _finance_record_belongs_to_user(transaction, current_id)
        ],
    }


def Myfinance_dashboard_menu(current_user: dict[str, Any] | None):
    current_user = ensure_current_user(current_user)
    if not current_user:
        print("Current user not found")
        return

    while True:
        user = get_user_record(current_user)
        finance_records = get_user_finance_records(current_user)
        if not user or finance_records is None:
            print("User not found")
            return

        print("\n=== MyFinance ===")
        print(f"User: {user.get('username', 'Unknown')}")
        print(f"Accounts: {len(finance_records.get('accounts', []))}")
        print(f"Transactions: {len(finance_records.get('transactions', []))}")
        print("1. Income")
        print("2. Expenses")
        print("3. View finance summary")
        print("4. Back")

        choice = input("\nChoose an option: ").strip()
        if choice == "1":
            print("Income flow coming next.")
        elif choice == "2":
            print("Expense flow coming next.")
        elif choice == "3":
            print(f"Accounts: {finance_records.get('accounts', [])}")
            print(f"Transactions: {finance_records.get('transactions', [])}")
        elif choice == "4":
            return
        else:
            print("Invalid option")


class IncomeFlowSystem:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver

    def log_income_statement(self):
        pass

    def update_income_statemnet(self):
        pass

    def view_income_statement(self, current_user: dict[str, Any] | None) -> list[dict[str, Any]]:
        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []
        return [
            transaction for transaction in finance_records.get("transactions", [])
            if transaction.get("txn_type") == "income"
        ]

    def edit_income_statement(self):
        pass

    def calculate_total_income_by_month(self):
        pass

    def calculate_total_income_by_year(self):
        pass


class ExpenseFlowSystem:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver

    def log_expense_statement(self):
        pass

    def update_expense_statement(self):
        pass

    def view_expense_statement(self, current_user: dict[str, Any] | None) -> list[dict[str, Any]]:
        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []
        return [
            transaction for transaction in finance_records.get("transactions", [])
            if transaction.get("txn_type") == "expense"
        ]

    def edit_expense_statement(self):
        pass


# Features to be implemented in MyFinance:
# 1. Edit and delete finance entries.
# 2. Monthly budgets with category limits and alerts.
# 3. Recurring income and recurring expense support.
# 4. Export finance statements to CSV/PDF.
