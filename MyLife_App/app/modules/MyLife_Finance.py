# Finance tracker for MyLife app
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import (
    FinanceAccount as AccountModel,
    FinanceCategory as CategoryModel,
    Transaction as TransactionModel,
    Budget as BudgetModel,
)
from app.modules.MyLife_Tracker import ensure_current_user, generate_id, now_dubai



def _account_to_dict(a: AccountModel) -> dict:
    return {
        "id": a.id,
        "user_id": a.user_id,
        "account_name": a.account_name,
        "account_type": a.account_type,
        "currency": a.currency,
        "opening_balance": a.opening_balance,
        "current_balance": a.current_balance,
        "created_at": a.created_at or "",
        "updated_at": a.updated_at or "",
    }


def _category_to_dict(c: CategoryModel) -> dict:
    return {
        "id": c.id,
        "user_id": c.user_id,
        "name": c.name,
        "type": c.type,
        "created_at": c.created_at or "",
    }


def _transaction_to_dict(t: TransactionModel) -> dict:
    return {
        "id": t.id,
        "user_id": t.user_id,
        "account_id": t.account_id,
        "category_id": t.category_id,
        "budget_id" : t.budget_id or "",
        "txn_type": t.txn_type,
        "amount": t.amount,
        "txn_date": t.txn_date or "",
        "description": t.description or "",
    }

class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def create_account(self, current_user, account_name: str, account_type: str, currency: str, opening_balance: float):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        uid = str(current_user.get("id"))

        exists = self.db.query(AccountModel).filter(
            AccountModel.user_id == uid,
            AccountModel.account_name.ilike(account_name.strip()),
        ).first()
        if exists:
            raise ValueError("An account with this name already exists")

        record = AccountModel(
            id=generate_id(),
            user_id=uid,
            account_name=account_name.strip(),
            account_type=account_type.strip().lower(),
            currency=currency.strip().upper(),
            opening_balance=float(opening_balance),
            current_balance=float(opening_balance),
            created_at=now_dubai(),
            updated_at=now_dubai(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return _account_to_dict(record)

    def list_accounts(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(AccountModel).filter(
            AccountModel.user_id == str(current_user.get("id"))
        ).all()
        return [_account_to_dict(a) for a in records]

    def get_account_by_id(self, current_user, account_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = self.db.query(AccountModel).filter(
            AccountModel.user_id == str(current_user.get("id")),
            AccountModel.id == account_id,
        ).first()
        return _account_to_dict(record) if record else None

    def update_account_balance(self, current_user, account_id, amount, txn_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = self.db.query(AccountModel).filter(
            AccountModel.user_id == str(current_user.get("id")),
            AccountModel.id == account_id,
        ).first()
        if not record:
            return None
        if txn_type == "income":
            record.current_balance += float(amount)
        elif txn_type == "expense":
            record.current_balance -= float(amount)
        else:
            raise ValueError("Invalid transaction type")
        record.updated_at = now_dubai()
        self.db.commit()
        return _account_to_dict(record)

    def edit_account(self, current_user, account_id, updated_name, updated_type, updated_currency):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        uid = str(current_user.get("id"))

        duplicate = self.db.query(AccountModel).filter(
            AccountModel.user_id == uid,
            AccountModel.account_name.ilike(updated_name.strip()),
            AccountModel.id != account_id,
        ).first()
        if duplicate:
            raise ValueError("An account with this name already exists")

        record = self.db.query(AccountModel).filter(
            AccountModel.user_id == uid,
            AccountModel.id == account_id,
        ).first()
        if not record:
            return None

        record.account_name = updated_name
        record.account_type = updated_type
        record.currency = updated_currency
        record.updated_at = now_dubai()
        self.db.commit()
        return _account_to_dict(record)
       
    def set_account_balance(self, current_user, account_id, new_balance):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return
        
        record = self.db.query(AccountModel).filter(
            AccountModel.user_id == str(current_user.get("id")),
            AccountModel.id == account_id
        ).first()

        if not record:
            return None
        
        record.current_balance = float(new_balance)
        record.updated_at = now_dubai()
        self.db.commit()
        return _account_to_dict(record)
    
    def delete_account(self, current_user, account_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        record = self.db.query(AccountModel).filter(
            AccountModel.user_id == str(current_user.get("id")),
            AccountModel.id == account_id,
        ).first()
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, current_user, name, category_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        uid = str(current_user.get("id"))

        exists = self.db.query(CategoryModel).filter(
            CategoryModel.user_id == uid,
            CategoryModel.name.ilike(name.strip()),
            CategoryModel.type == category_type,
        ).first()
        if exists:
            raise ValueError("A category with this name already exists")

        record = CategoryModel(
            id=generate_id(),
            user_id=uid,
            name=name.strip(),
            type=category_type,
            created_at=now_dubai(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return _category_to_dict(record)

    def list_categories(self, current_user, category_type=None):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        uid = str(current_user.get("id"))
        q = self.db.query(CategoryModel).filter(CategoryModel.user_id == uid)
        if category_type:
            q = q.filter(CategoryModel.type == category_type)
        return [_category_to_dict(c) for c in q.all()]

    def get_category_by_id(self, current_user, category_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = self.db.query(CategoryModel).filter(
            CategoryModel.user_id == str(current_user.get("id")),
            CategoryModel.id == category_id,
        ).first()
        return _category_to_dict(record) if record else None

    def edit_category(self, current_user, category_id, updated_name, updated_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        uid = str(current_user.get("id"))

        duplicate = self.db.query(CategoryModel).filter(
            CategoryModel.user_id == uid,
            CategoryModel.name.ilike(updated_name.strip()),
            CategoryModel.type == updated_type,
            CategoryModel.id != category_id,
        ).first()
        if duplicate:
            raise ValueError("A category with this name already exists")

        record = self.db.query(CategoryModel).filter(
            CategoryModel.user_id == uid,
            CategoryModel.id == category_id,
        ).first()
        if not record:
            return None

        record.name = updated_name
        record.type = updated_type
        self.db.commit()
        return _category_to_dict(record)

    def delete_category(self, current_user, category_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        record = self.db.query(CategoryModel).filter(
            CategoryModel.user_id == str(current_user.get("id")),
            CategoryModel.id == category_id,
        ).first()
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, current_user, account_id, category_id, txn_type, amount, txn_date, description="", budget_id=""):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = TransactionModel(
            id=generate_id(),
            user_id=str(current_user.get("id")),
            account_id=account_id,
            category_id=category_id,
            budget_id=budget_id or None,
            txn_type=txn_type,
            amount=float(amount),
            txn_date=txn_date,
            description=description,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        account_service = AccountService(self.db)
        account_service.update_account_balance(current_user, account_id, amount, txn_type)

        return _transaction_to_dict(record)

    def list_transactions(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id"))
        ).all()
        return [_transaction_to_dict(t) for t in records]

    def list_transactions_by_type(self, current_user, txn_type):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.txn_type == txn_type,
        ).all()
        return [_transaction_to_dict(t) for t in records]

    def get_transaction_by_id(self, current_user, transaction_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.id == transaction_id,
        ).first()
        return _transaction_to_dict(record) if record else None

    def edit_transaction(self, current_user, transaction_id, updated_account_id, updated_category_id, updated_amount, updated_txn_date, updated_description):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.id == transaction_id,
        ).first()
        if not record:
            return None
        record.account_id = updated_account_id
        record.category_id = updated_category_id
        record.amount = float(updated_amount)
        record.txn_date = updated_txn_date
        record.description = updated_description
        self.db.commit()
        return _transaction_to_dict(record)

    def delete_transaction(self, current_user, transaction_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        record = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.id == transaction_id,
        ).first()
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

    def list_transactions_by_account(self, current_user, account_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.account_id == account_id,
        ).all()
        return [_transaction_to_dict(t) for t in records]

    def list_transactions_by_category(self, current_user, category_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.category_id == category_id,
        ).all()
        return [_transaction_to_dict(t) for t in records]

    def list_transactions_by_budget(self, current_user, budget_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.budget_id == budget_id,
        ).all()
        return [_transaction_to_dict(t) for t in records]

    def list_transactions_by_date(self, current_user, target_date):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        if not target_date:
            return []
        records = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.txn_date.startswith(target_date),
        ).all()
        return [_transaction_to_dict(t) for t in records]
    
    def list_transaction_by_budget(self, current_user, budget_id):
        current_user=ensure_current_user(current_user)
        if not current_user:
            return []

        record = self.db.query(TransactionModel).filter(
            TransactionModel.user_id == str(current_user.get("id")),
            TransactionModel.id == budget_id
        )

        return [_transaction_to_dict(t) for t in record]

    def get_account_spending_summary(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return {}
        uid = str(current_user.get("id"))
        rows = (
            self.db.query(
                TransactionModel.account_id,
                TransactionModel.txn_type,
                func.sum(TransactionModel.amount).label("total"),
            )
            .filter(TransactionModel.user_id == uid)
            .group_by(TransactionModel.account_id, TransactionModel.txn_type)
            .all()
        )
        summary = {}
        for account_id, txn_type, total in rows:
            if account_id not in summary:
                summary[account_id] = {"income": 0.0, "expenses": 0.0}
            if txn_type == "income":
                summary[account_id]["income"] = float(total)
            else:
                summary[account_id]["expenses"] = float(total)
        return summary


class FinanceSummaryService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_service = TransactionService(db)
        self.account_service = AccountService(db)

    def calculate_total_income(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        income_transactions = self.transaction_service.list_transactions_by_type(current_user, "income")
        return sum(float(t.get("amount", 0)) for t in income_transactions)

    def calculate_total_expenses(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        expense_transactions = self.transaction_service.list_transactions_by_type(current_user, "expense")
        return sum(float(t.get("amount", 0)) for t in expense_transactions)

    def calculate_net_balance(self, current_user):
        return self.calculate_total_income(current_user) - self.calculate_total_expenses(current_user)

    def calculate_account_balances(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        accounts = self.account_service.list_accounts(current_user)
        return [
            {
                "account_name": a.get("account_name"),
                "account_type": a.get("account_type"),
                "currency": a.get("currency"),
                "current_balance": a.get("current_balance"),
            }
            for a in accounts
        ]

    def calculate_total_income_by_month(self, current_user, year, month):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        transactions = self.transaction_service.list_transactions_by_type(current_user, "income")
        total = 0
        for t in transactions:
            parts = str(t.get("txn_date", "")).split("T")[0].split("-")
            if len(parts) == 3 and int(parts[0]) == year and int(parts[1]) == month:
                total += float(t.get("amount", 0))
        return total

    def calculate_total_expenses_by_month(self, current_user, year, month):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        transactions = self.transaction_service.list_transactions_by_type(current_user, "expense")
        total = 0
        for t in transactions:
            parts = str(t.get("txn_date", "")).split("T")[0].split("-")
            if len(parts) == 3 and int(parts[0]) == year and int(parts[1]) == month:
                total += float(t.get("amount", 0))
        return total

    def calculate_total_income_by_year(self, current_user, year):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        transactions = self.transaction_service.list_transactions_by_type(current_user, "income")
        total = 0
        for t in transactions:
            parts = str(t.get("txn_date", "")).split("T")[0].split("-")
            if len(parts) == 3 and int(parts[0]) == year:
                total += float(t.get("amount", 0))
        return total

    def calculate_total_expenses_by_year(self, current_user, year):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        transactions = self.transaction_service.list_transactions_by_type(current_user, "expense")
        total = 0
        for t in transactions:
            parts = str(t.get("txn_date", "")).split("T")[0].split("-")
            if len(parts) == 3 and int(parts[0]) == year:
                total += float(t.get("amount", 0))
        return total

    def build_finance_summary(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return {}
        category_svc = CategoryService(self.db)
        all_transactions = self.transaction_service.list_transactions(current_user)
        categories = {c["id"]: c["name"] for c in category_svc.list_categories(current_user)}

        income_by_cat: dict[str, float] = {}
        expense_by_cat: dict[str, float] = {}
        for t in all_transactions:
            cat_name = categories.get(t.get("category_id", ""), "Uncategorized")
            amount = float(t.get("amount", 0))
            if t.get("txn_type") == "income":
                income_by_cat[cat_name] = income_by_cat.get(cat_name, 0) + amount
            else:
                expense_by_cat[cat_name] = expense_by_cat.get(cat_name, 0) + amount

        income_by_category = sorted(
            [{"name": k, "amount": round(v, 2)} for k, v in income_by_cat.items()],
            key=lambda x: x["amount"], reverse=True,
        )
        expense_by_category = sorted(
            [{"name": k, "amount": round(v, 2)} for k, v in expense_by_cat.items()],
            key=lambda x: x["amount"], reverse=True,
        )

        net = self.calculate_net_balance(current_user)
        return {
            "total_income": self.calculate_total_income(current_user),
            "total_expenses": self.calculate_total_expenses(current_user),
            "net_balance": net,
            "balance": net,
            "account_balances": self.calculate_account_balances(current_user),
            "income_by_category": income_by_category,
            "expense_by_category": expense_by_category,
        }


def _budget_to_dict(b: BudgetModel) -> dict:
    return {
        "id": b.id,
        "user_id": b.user_id,
        "category_id": b.category_id or "",
        "name": b.name,
        "amount": b.amount,
        "period": b.period,
        "start_date": b.start_date or "",
        "created_at": b.created_at or "",
        "updated_at": b.updated_at or "",
    }


class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    def create_budget(self, current_user, name: str, amount: float, period: str, category_id: str = "", start_date: str = ""):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        uid = str(current_user.get("id"))

        exists = self.db.query(BudgetModel).filter(
            BudgetModel.user_id == uid,
            BudgetModel.name.ilike(name.strip()),
        ).first()
        if exists:
            raise ValueError("A budget with this name already exists")

        record = BudgetModel(
            id=generate_id(),
            user_id=uid,
            category_id=category_id or None,
            name=name.strip(),
            amount=int(amount),
            period=period,
            start_date=start_date,
            created_at=now_dubai(),
            updated_at=now_dubai(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return _budget_to_dict(record)

    def list_budgets(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []
        records = self.db.query(BudgetModel).filter(
            BudgetModel.user_id == str(current_user.get("id"))
        ).all()
        return [_budget_to_dict(b) for b in records]

    def get_budget_by_id(self, current_user, budget_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        record = self.db.query(BudgetModel).filter(
            BudgetModel.user_id == str(current_user.get("id")),
            BudgetModel.id == budget_id,
        ).first()
        return _budget_to_dict(record) if record else None

    def edit_budget(self, current_user, budget_id, name, amount, period, category_id="", start_date=""):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None
        uid = str(current_user.get("id"))

        duplicate = self.db.query(BudgetModel).filter(
            BudgetModel.user_id == uid,
            BudgetModel.name.ilike(name.strip()),
            BudgetModel.id != budget_id,
        ).first()
        if duplicate:
            raise ValueError("A budget with this name already exists")

        record = self.db.query(BudgetModel).filter(
            BudgetModel.user_id == uid,
            BudgetModel.id == budget_id,
        ).first()
        if not record:
            return None

        record.name = name.strip()
        record.amount = int(amount)
        record.period = period
        record.category_id = category_id or None
        record.start_date = start_date
        record.updated_at = now_dubai()
        self.db.commit()
        return _budget_to_dict(record)

    def delete_budget(self, current_user, budget_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        record = self.db.query(BudgetModel).filter(
            BudgetModel.user_id == str(current_user.get("id")),
            BudgetModel.id == budget_id,
        ).first()
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

    def get_budget_spending(self, current_user, budget_id):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return 0
        transactions = TransactionService(self.db).list_transactions_by_budget(current_user, budget_id)
        return sum(float(t["amount"]) for t in transactions if t["txn_type"] == "expense")

    def get_all_budget_spending(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return {}
        uid = str(current_user.get("id"))
        rows = (
            self.db.query(
                TransactionModel.budget_id,
                func.sum(TransactionModel.amount).label("total"),
            )
            .filter(
                TransactionModel.user_id == uid,
                TransactionModel.budget_id.isnot(None),
                TransactionModel.txn_type == "expense",
            )
            .group_by(TransactionModel.budget_id)
            .all()
        )
        return {budget_id: float(total) for budget_id, total in rows}
    