# Finance tracker for MyLife app
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass

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


def build_finance_dashboard_context(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None

    user = get_user_record(current_user)
    finance_records = get_user_finance_records(current_user)
    if not user or finance_records is None:
        return None

    summary_service = FinanceSummaryService()
    return {
        "user": {
            "id": str(current_user.get("id")),
            "username": user.get("username"),
        },
        "accounts": finance_records.get("accounts", []),
        "categories": finance_records.get("categories", []),
        "transactions": finance_records.get("transactions", []),
        "summary": summary_service.build_finance_summary(current_user),
    }


def Myfinance_dashboard_menu(current_user: dict[str, Any] | None):
    return build_finance_dashboard_context(current_user)

class AccountService:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver

    def create_account(self, current_user, account_name : str, account_type : str, currency : str, opening_balance : int):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        current_id = str(current_user.get("id"))
        finance_data = self.load_finance_data()
        
        validator = VerifyAccountInputs()
        account_name = validator.verify_account_name(account_name, current_user)
        account_type = validator.verify_account_type(account_type)
        currency = validator.verify_currency(currency)
        opening_balance = validator.verify_opening_balance(opening_balance)

        account = {
            "id" : generate_id(),
            "user_id" : current_id,
            "account_name" : account_name,
            "account_type" : account_type,
            "currency" : currency,
            "opening_balance" : opening_balance,
            "current_balance" : opening_balance,
            "created_at" : now_dubai(),
            "updated_at" : now_dubai()
        }
        finance_data.setdefault("accounts", []).append(account)
        self.save_finance_data(finance_data)
        return account

    def list_accounts(self, current_user):
        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []
        
        return finance_records.get("accounts", [])

    def find_account(self, current_user, account_choice):
        accounts = self.list_accounts(current_user)

        if account_choice.isdigit():
            account_index = int(account_choice) - 1
            if 0 <= account_index < len(accounts):
                return accounts[account_index]
            
        for account in accounts:
            if account.get("account_name", "").strip().lower() == account_choice.strip().lower():
                return account
            
        return None
    
    def get_account_by_id(self, current_user, account_id):
        accounts = self.list_accounts(current_user)

        for account in accounts:
            if str(account.get("id")).strip().lower() == account_id.strip().lower():
                return account
        
        return None

    def update_account_balance(self, current_user, account_id, amount, txn_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        
        finance_data = self.load_finance_data()
        current_id  = str(current_user.get("id"))

        for account in finance_data.get("accounts", []):
            if str(account.get("user_id")) != current_id:
                continue
            if str(account.get("id")) != str(account_id):
                continue

            if txn_type == "income":
                account["current_balance"] += amount
            elif txn_type == "expense":
                account["current_balance"] -= amount
            else:
                raise ValueError("Invalid transaction type")
            
            account["updated_at"] = now_dubai()
            self.save_finance_data(finance_data)
            return account
        
        return None
        

    def edit_account(self, current_user, account_id, updated_name, updated_type, updated_currency):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        
        finance_data = self.load_finance_data()
        current_id = str(current_user.get("id"))

        for account in finance_data.get("accounts", []):
            if str(account.get("user_id")) != current_id:
                continue

            if str(account.get("id")) != str(account_id):
                continue

            for existing_account in finance_data.get("accounts", []):
                if str(existing_account.get("user_id")) != current_id:
                    continue

                if str(existing_account.get("id")) == str(account_id):
                    continue

                if existing_account.get("account_name", "").strip().lower() == updated_name.strip().lower():
                    raise ValueError("An account with this name already exists")

            account["account_name"] = updated_name
            account["account_type"] = updated_type
            account["currency"] = updated_currency
            account["updated_at"] = now_dubai()
        
        

            self.save_finance_data(finance_data)
            return account
        
        return None
    
    def delete_account(self, current_user, account_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        finance_data = self.load_finance_data()
        current_id = str(current_user.get("id"))

        updated_accounts = [
            account for account in finance_data.get("accounts",[])
            if not(
                str(account.get("user_id")).strip().lower() == current_id.strip().lower() and
                str(account.get("id")).strip().lower() == account_id.strip().lower()
            )
        ]
        if len(updated_accounts) == len(finance_data.get("accounts", [])):
            return False
        
        finance_data["accounts"] = updated_accounts
        self.save_finance_data(finance_data)
        return True
class CategoryService:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver

    def create_category(self, current_user, name, category_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None

        current_id = str(current_user.get("id"))
        finance_data = self.load_finance_data()

        for category in finance_data.get("categories", []):
            if str(category.get("user_id")) != current_id:
                continue

            if (
                category.get("name", "").strip().lower() == name.strip().lower()
                and str(category.get("type", "")).strip().lower() == str(category_type).strip().lower()
            ):
                raise ValueError("A category with this name already exists")

        category = {
            "id": generate_id(),
            "user_id": current_id,
            "name": name,
            "type": category_type,
            "created_at": now_dubai(),
        }
        finance_data.setdefault("categories", []).append(category)
        self.save_finance_data(finance_data)
        return category

    def list_categories(self, current_user, category_type=None):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []

        categories = finance_records.get("categories", [])
        if category_type:
            categories = [
                category for category in categories
                if str(category.get("type", "")).strip().lower() == str(category_type).strip().lower()
            ]

        return categories

    def find_category(self, current_user, category_choice, category_type=None):
        categories = self.list_categories(current_user, category_type)

        if category_choice.isdigit():
            category_index = int(category_choice) - 1
            if 0 <= category_index < len(categories):
                return categories[category_index]

        for category in categories:
            if category.get("name", "").strip().lower() == category_choice.strip().lower():
                return category

        return None

    def get_category_by_id(self, current_user, category_id):
        categories = self.list_categories(current_user)

        for category in categories:
            if str(category.get("id")).strip().lower() == category_id.strip().lower():
                return category

        return None

    def edit_category(self, current_user, category_id, updated_name, updated_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None

        finance_data = self.load_finance_data()
        current_id = str(current_user.get("id"))

        for category in finance_data.get("categories", []):
            if str(category.get("user_id")) != current_id:
                continue

            if str(category.get("id")) != str(category_id):
                continue

            for existing_category in finance_data.get("categories", []):
                if str(existing_category.get("user_id")) != current_id:
                    continue

                if str(existing_category.get("id")) == str(category_id):
                    continue

                if (
                    existing_category.get("name", "").strip().lower() == updated_name.strip().lower()
                    and str(existing_category.get("type", "")).strip().lower() == str(updated_type).strip().lower()
                ):
                    raise ValueError("A category with this name already exists")

            category["name"] = updated_name
            category["type"] = updated_type
            self.save_finance_data(finance_data)
            return category

        return None

    def delete_category(self, current_user, category_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        finance_data = self.load_finance_data()
        current_id = str(current_user.get("id"))

        updated_categories = [
            category for category in finance_data.get("categories", [])
            if not (
                str(category.get("user_id")).strip().lower() == current_id.strip().lower()
                and str(category.get("id")).strip().lower() == category_id.strip().lower()
            )
        ]
        if len(updated_categories) == len(finance_data.get("categories", [])):
            return False

        finance_data["categories"] = updated_categories
        self.save_finance_data(finance_data)
        return True

class TransactionService:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver

    def create_transaction(self,
                           current_user,
                           account_id,
                           category_id,
                           txn_type,
                           amount,
                           txn_date,
                           description=""
                           ):
        
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        
        current_id = str(current_user.get("id"))
        finance_data = self.load_finance_data()


        transaction = {
            "id" : generate_id(),
            "user_id" : current_id,
            "account_id" : account_id,
            "category_id" : category_id,
            "txn_type" : txn_type,
            "amount" : float(amount),
            "txn_date" : txn_date,
            "description" : description
        }
        finance_data.setdefault("transactions", []).append(transaction)
        self.save_finance_data(finance_data)
        return transaction

    def list_transactions(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        
        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []
        
        return finance_records.get("transactions", [])

    def list_transactions_by_type(self, current_user, txn_type):
        transactions = self.list_transactions(current_user)

        return[
            transaction for transaction in transactions
            if transaction.get("txn_type", "").strip().lower() == txn_type.strip().lower()
        ]

    def find_transaction(self, current_user, transaction_choice):
        transactions = self.list_transactions(current_user)

        if transaction_choice.isdigit():
            transaction_index = int(transaction_choice) - 1
            if 0 <= transaction_index < len(transactions):
                return transactions[transaction_index]
        
        for transaction in transactions:
            if str(transaction.get("id", "")).strip().lower() == transaction_choice.strip().lower():
                return transaction
        
        return None
        
    def get_transaction_by_id(self, current_user, transaction_id):
        transactions = self.list_transactions(current_user)

        for transaction in transactions:
            if transaction.get("id").strip().lower() == transaction_id.strip().lower():
                return transaction
        
        return None
    
    def edit_transaction(self, current_user, transaction_id, updated_account_id, updated_category_id, updated_amount, updated_txn_date, updated_description):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        
        finance_data = self.load_finance_data()
        current_id = str(current_user.get("id"))

        for transaction in finance_data.get("transactions", []):
            if str(transaction.get("user_id")) != current_id:
                continue

            if str(transaction.get("id")) != transaction_id:
                continue

            transaction["account_id"] = updated_account_id
            transaction["category_id"] = updated_category_id
            transaction["amount"] = updated_amount
            transaction["txn_date"] = updated_txn_date
            transaction["description"] = updated_description

            self.save_finance_data(finance_data)
            return transaction
        
        return None
    
    def delete_transaction(self, current_user, transaction_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        
        finance_data = self.load_finance_data()
        current_id = str(current_user.get("id"))

        updated_transactions = [
            transaction for transaction in finance_data.get("transactions", [])
            if not (
                str(transaction.get("user_id")).strip().lower() == current_id.strip().lower() and
                str(transaction.get("id")).strip().lower() == transaction_id.strip().lower()
            )
        ]
        if len(updated_transactions) == len(finance_data.get("transactions", [])):
            return False
        
        finance_data["transactions"] = updated_transactions
        self.save_finance_data(finance_data)
        return True

    def list_transactions_by_account(self, current_user, account_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        
        account_service = AccountService()
        account = account_service.get_account_by_id(current_user, account_id)
        if not account:
            return []
        
        transactions = self.list_transactions(current_user)

        return [
            transaction for transaction in transactions
            if str(transaction.get("account_id")) == str(account.get("id"))
        ]


    def list_transactions_by_category(self, current_user, category_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        
        category_service = CategoryService()
        category = category_service.get_category_by_id(current_user, category_id)
        if not category:
            return []

        transactions = self.list_transactions(current_user)

        return [
            transaction for transaction in transactions
            if str(transaction.get("category_id")) == str(category.get("id"))
        ]

    def list_transactions_by_date(self, current_user, target_date):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        
        if not target_date:
            return []
    
        transactions = self.list_transactions(current_user)

        return[
            transaction for transaction in transactions
            if str(transaction.get("txn_date")).split("T")[0] == target_date
        ]

class FinanceSummaryService:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver
        self.transaction_service = TransactionService(data_loader, data_saver)
        self.account_service = AccountService(data_loader, data_saver)

    def calculate_total_income(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        income_transactions = self.transaction_service.list_transactions_by_type(current_user, "income")

        total_income = 0
        for transaction in income_transactions:
            total_income += float(transaction.get("amount", 0))

        return total_income

    def calculate_total_expenses(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        expense_transactions = self.transaction_service.list_transactions_by_type(current_user, "expense")

        total_expense = 0
        for transaction in expense_transactions:
            total_expense += float(transaction.get("amount", 0))

        return total_expense

    def calculate_net_balance(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        total_income = self.calculate_total_income(current_user)
        total_expense = self.calculate_total_expenses(current_user)
        return total_income - total_expense

    def calculate_account_balances(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        accounts = self.account_service.list_accounts(current_user)
        if not accounts:
            return []

        return [
            {
                "account_name": account.get("account_name"),
                "account_type": account.get("account_type"),
                "currency": account.get("currency"),
                "current_balance": account.get("current_balance"),
            }
            for account in accounts
        ]

    def calculate_total_income_by_month(self, current_user, year, month):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        income_transactions = self.transaction_service.list_transactions_by_type(current_user, "income")

        total_income = 0
        for transaction in income_transactions:
            txn_date = str(transaction.get("txn_date", "")).split("T")[0]
            parts = txn_date.split("-")
            if len(parts) != 3:
                continue

            txn_year = int(parts[0])
            txn_month = int(parts[1])
            if txn_year == year and txn_month == month:
                total_income += float(transaction.get("amount", 0))

        return total_income

    def calculate_total_expenses_by_month(self, current_user, year, month):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        expense_transactions = self.transaction_service.list_transactions_by_type(current_user, "expense")

        total_expense = 0
        for transaction in expense_transactions:
            txn_date = str(transaction.get("txn_date", "")).split("T")[0]
            parts = txn_date.split("-")
            if len(parts) != 3:
                continue

            txn_year = int(parts[0])
            txn_month = int(parts[1])
            if txn_year == year and txn_month == month:
                total_expense += float(transaction.get("amount", 0))

        return total_expense

    def calculate_total_income_by_year(self, current_user, year):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        income_transactions = self.transaction_service.list_transactions_by_type(current_user, "income")

        total_income = 0
        for transaction in income_transactions:
            txn_date = str(transaction.get("txn_date", "")).split("T")[0]
            parts = txn_date.split("-")
            if len(parts) != 3:
                continue

            txn_year = int(parts[0])
            if txn_year == year:
                total_income += float(transaction.get("amount", 0))

        return total_income

    def calculate_total_expenses_by_year(self, current_user, year):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0

        expense_transactions = self.transaction_service.list_transactions_by_type(current_user, "expense")

        total_expense = 0
        for transaction in expense_transactions:
            txn_date = str(transaction.get("txn_date", "")).split("T")[0]
            parts = txn_date.split("-")
            if len(parts) != 3:
                continue

            txn_year = int(parts[0])
            if txn_year == year:
                total_expense += float(transaction.get("amount", 0))

        return total_expense

    def build_finance_summary(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return {}

        total_income = self.calculate_total_income(current_user)
        total_expenses = self.calculate_total_expenses(current_user)
        net_balance = self.calculate_net_balance(current_user)
        account_balances = self.calculate_account_balances(current_user)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": net_balance,
            "account_balances": account_balances,
        }

class IncomeFlowSystem:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver
        self.transaction_service = TransactionService(data_loader, data_saver)
        self.account_service = AccountService(data_loader, data_saver)
        self.category_service = CategoryService(data_loader, data_saver)

    def log_income_statement(self, current_user, account_id, category_id, amount, txn_date, description=""):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        
        account_service = AccountService()
        category_service = CategoryService()
        transaction_service = TransactionService()

        account = account_service.get_account_by_id(current_user, account_id)
        if not account:
            raise ValueError("Not found")
        
        category = category_service.get_category_by_id(current_user, category_id)
        if not category:
            raise ValueError("Not found")
        
        if str(category.get("type", "")).strip().lower() != "income":
            raise ValueError("Selected category must be an income category")
        
        if float(amount) <= 0:
            raise ValueError("Amount must be greater than zero")
        
        transaction = transaction_service.create_transaction(
            current_user=current_user,
            account_id=account_id,
            category_id=category_id,
            txn_type="income",
            amount=float(amount),
            txn_date=txn_date,
            description=description
        )

        account_service.update_account_balance(
            current_user=current_user,
            account_id=account_id,
            amount=float(amount),
            txn_type="income"
        )
        
        return transaction

    def view_income_statement(self, current_user: dict[str, Any] | None) -> list[dict[str, Any]]:
        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []
        return [
            transaction for transaction in finance_records.get("transactions", [])
            if transaction.get("txn_type", "").strip().lower() == "income"
        ]

    def edit_income_statement(self, 
                              current_user,
                              transaction_id,
                              updated_account_id,
                              updated_category_id,
                              updated_amount,
                              updated_txn_date,
                              updated_description=""
                               ):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        
        transaction = self.transaction_service.get_transaction_by_id(current_user, transaction_id)
        if not transaction:
            raise ValueError
        
        account = self.account_service.get_account_by_id(current_user,  updated_account_id)
        if not account:
            return None
        
        category = self.category_service.get_category_by_id(current_user, updated_category_id)
        if not category:
            raise ValueError
        
        if str(category.get("type", "")).strip().lower() != "income":
            raise ValueError("Selected category must be an income category")
        
        old_account_id = transaction.get("account_id")
        old_amount = float(transaction.get("amount", 0))

        self.account_service.update_account_balance(current_user, old_account_id, old_amount, "expense")

        updated_transaction = self.transaction_service.edit_transaction(
            current_user=current_user,
            transaction_id=transaction_id,
            updated_account_id=updated_account_id,
            updated_category_id=updated_category_id,
            updated_amount=updated_amount,
            updated_txn_date=updated_txn_date,
            updated_description=updated_description
        )
        
        self.account_service.update_account_balance(current_user, updated_account_id, float(updated_amount), "income")

        return updated_transaction
class ExpenseFlowSystem:
    def __init__(self, data_loader=load_finance_database, data_saver=save_finance_database):
        self.load_finance_data = data_loader
        self.save_finance_data = data_saver
        self.transaction_service = TransactionService(data_loader, data_saver)
        self.account_service = AccountService(data_loader, data_saver)
        self.category_service = CategoryService(data_loader, data_saver)
    

    def log_expense_statement(self, current_user, account_id, category_id, amount, txn_date, description=""):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        
        account_service = AccountService()
        category_service = CategoryService()
        transaction_service = TransactionService()

        account = account_service.get_account_by_id(current_user, account_id)
        if not account:
            raise ValueError("Not found")
        
        category = category_service.get_category_by_id(current_user, category_id)
        if not category:
            raise ValueError("Not found")
        
        if str(category.get("type", "")).strip().lower() != "expense":
            raise ValueError("Selected category must be an expense category")
        
        if float(amount) <= 0:
            raise ValueError("Amount must be greater than zero")
        
        transaction = transaction_service.create_transaction(
            current_user=current_user,
            account_id=account_id,
            category_id=category_id,
            txn_type="expense",
            amount=float(amount),
            txn_date=txn_date,
            description=description
        )

        account_service.update_account_balance(
            current_user=current_user,
            account_id=account_id,
            amount=float(amount),
            txn_type="expense"
        )

        return transaction
        
    def view_expense_statement(self, current_user: dict[str, Any] | None) -> list[dict[str, Any]]:
        finance_records = get_user_finance_records(current_user)
        if not finance_records:
            return []
        return [
            transaction for transaction in finance_records.get("transactions", [])
            if str(transaction.get("txn_type", "")).strip().lower() == "expense"
        ]

    def edit_expense_statement(self,
                              current_user,
                              transaction_id,
                              updated_account_id,
                              updated_category_id,
                              updated_amount,
                              updated_txn_date,
                              updated_description=""
                               ):
            current_user = ensure_current_user(current_user)
            if not current_user:
                return None

            transaction = self.transaction_service.get_transaction_by_id(current_user, transaction_id)
            if not transaction:
                raise ValueError
        
            account = self.account_service.get_account_by_id(current_user,  updated_account_id)
            if not account:
                return None
        
            category = self.category_service.get_category_by_id(current_user, updated_category_id)
            if not category:
                raise ValueError
        
            if str(category.get("type", "")).strip().lower() != "expense":
                raise ValueError("Selected category must be an expense category")
        
            old_account_id = transaction.get("account_id")
            old_amount = float(transaction.get("amount", 0))

            self.account_service.update_account_balance(current_user, old_account_id, old_amount, "income")

            updated_transaction = self.transaction_service.edit_transaction(
            current_user=current_user,
            transaction_id=transaction_id,
            updated_account_id=updated_account_id,
            updated_category_id=updated_category_id,
            updated_amount=updated_amount,
            updated_txn_date=updated_txn_date,
            updated_description=updated_description
        )
        
            self.account_service.update_account_balance(current_user, updated_account_id, float(updated_amount), "expense")

            return updated_transaction

class VerifyAccountInputs:
    ACCOUNT_TYPES = ["cash", "bank", "savings", "ewallet"]

    @staticmethod
    def verify_account_name(account_name: str, current_user: dict[str, Any] | None = None) -> str:
        cleaned_name = str(account_name or "").strip()
        if not cleaned_name:
            raise ValueError("Account name is required")

        if current_user:
            account_service = AccountService()
            accounts = account_service.list_accounts(current_user)
            for account in accounts:
                if account.get("account_name", "").strip().lower() == cleaned_name.lower():
                    raise ValueError("An account with this name already exists")

        return cleaned_name

    @classmethod
    def verify_account_type(cls, account_type: str) -> str:
        cleaned_type = str(account_type or "").strip().lower()
        if not cleaned_type:
            raise ValueError("Account type is required")
        if cleaned_type not in cls.ACCOUNT_TYPES:
            raise ValueError(f"Account type must be one of: {cls.ACCOUNT_TYPES}")
        return cleaned_type

    @staticmethod
    def verify_currency(currency: str) -> str:
        cleaned_currency = str(currency or "").strip().upper()
        if not cleaned_currency:
            raise ValueError("Currency is required")
        return cleaned_currency

    @staticmethod
    def verify_opening_balance(opening_balance: int | float | str) -> float:
        try:
            normalized_balance = float(opening_balance)
        except (TypeError, ValueError):
            raise ValueError("Opening balance must be a number")

        if normalized_balance < 0:
            raise ValueError("Opening balance cannot be negative")
        return normalized_balance

def _current_user_id(current_user : dict | None) -> str | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None
    return str(current_user.get("id"))

def _get_user_accounts(current_user):
    finance_records = get_user_finance_records(current_user)
    if not finance_records:
        return []
    return finance_records.get("accounts", [])

def _get_user_categories(current_user, category_type : str | None = None):
    finance_records = get_user_finance_records(current_user)
    if not finance_records:
        return []
    
    categories = finance_records.get("categories", [])
    if category_type:
        catagories = [
            category for category in categories
            if category.get("type") == category_type
        ]
    return categories

def _get_user_transactions(current_user):
    finance_records = get_user_finance_records(current_user)
    if not finance_records:
        return []
    return finance_records.get("transactions", [])

def _find_account(current_user, account_choice):
    pass

def _find_category(current_user, category_choice, category_type = None):
    pass

def _is_valid_amount(value : str) -> bool:
    try:
        return float(value) > 0
    except ValueError:
        return False
    
def _prompt_valid_amount(prompt_text):
    pass

def _update_account_balance(account: dict, amount: float, txn_type: str):
    if txn_type == "income":
        account["current_balance"] += amount
    elif txn_type == "expense":
        account["current_balance"] -= amount
    account["updated_at"] = now_dubai()

@dataclass
class ValidateIdentification:
    current_id : str
    account_id : str
    transaction_id : str

    def vailidate_current_id(self, current_user):
        accounts = AccountService.list_accounts(current_user)
        self.current_id = str(current_user.get("user_id"))

        for account in accounts:
            if str(account.get("user_id")).strip().lower() != self.current_id.strip().lower():
                continue
    

    def validate_account_id(self, current_user):
        accounts = AccountService.list_accounts(current_user)

        for account in accounts:
            if str(account.get("id")).strip().lower() != self.account_id.strip().lower():
                continue
        
    

