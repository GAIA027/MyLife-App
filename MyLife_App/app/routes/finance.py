from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR
from app.database import get_db
from app.dependencies import require_user
from app.modules.MyLife_Finance import (
    AccountService as FinanceAccountService,
    BudgetService,
    CategoryService,
    FinanceSummaryService,
    TransactionService,
)

router = APIRouter(prefix="/finance", tags=["finance"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/dashboard", response_class=HTMLResponse)
def finance_dashboard(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    summary_service = FinanceSummaryService(db)
    account_service = FinanceAccountService(db)
    category_service = CategoryService(db)
    transaction_service = TransactionService(db)
    budget_service = BudgetService(db)

    accounts = account_service.list_accounts(current_user)
    transactions = transaction_service.list_transactions(current_user)

    account_currency_map = {acc["id"]: acc.get("currency", "USD") for acc in accounts}

    spending_by_account = transaction_service.get_account_spending_summary(current_user)
    accounts_with_summary = []
    for acc in accounts:
        s = spending_by_account.get(acc["id"], {"income": 0.0, "expenses": 0.0})
        accounts_with_summary.append({
            **acc,
            "income": s["income"],
            "expenses": s["expenses"],
            "net": s["income"] - s["expenses"],
        })

    recent_txns = []
    for t in sorted(transactions, key=lambda x: x.get("txn_date", ""), reverse=True)[:5]:
        recent_txns.append({**t, "currency": account_currency_map.get(t.get("account_id", ""), "USD")})

    return templates.TemplateResponse(
        "finance/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "summary": summary_service.build_finance_summary(current_user),
            "accounts": accounts,
            "accounts_with_summary": accounts_with_summary,
            "categories": category_service.list_categories(current_user),
            "transactions": transactions,
            "recent_transactions": recent_txns,
            "budgets": budget_service.list_budgets(current_user),
        },
    )


@router.get("/summary", response_class=HTMLResponse)
def finance_summary(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    summary = FinanceSummaryService(db).build_finance_summary(current_user)
    return templates.TemplateResponse(
        "finance/summary.html",
        {"request": request, "current_user": current_user, "summary": summary},
    )


@router.get("/accounts", response_class=HTMLResponse)
def create_account_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "finance/create_account.html",
        {"request": request, "current_user": current_user, "error": None},
    )


@router.post("/accounts", response_class=HTMLResponse)
def account_submit(
    request: Request,
    current_user=Depends(require_user),
    account_name: str = Form(...),
    account_type: str = Form(...),
    currency: str = Form(...),
    opening_balance: float = Form(...),
    db: Session = Depends(get_db),
):
    try:
        FinanceAccountService(db).create_account(
            current_user=current_user,
            account_name=account_name,
            account_type=account_type,
            currency=currency,
            opening_balance=opening_balance,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/create_account.html",
            {"request": request, "current_user": current_user, "error": str(exc)},
            status_code=400,
        )
    return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/accounts/list", response_class=HTMLResponse)
def accounts_list_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    accounts = FinanceAccountService(db).list_accounts(current_user)
    return templates.TemplateResponse(
        "finance/accounts_list.html",
        {"request": request, "current_user": current_user, "accounts": accounts, "error": None},
    )

@router.post("/accounts/{account_id}/delete")
def delete_account(
    account_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    FinanceAccountService(db).delete_account(current_user, account_id)
    return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/accounts/{account_id}/edit", response_class=HTMLResponse)
def edit_account_page(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    account = FinanceAccountService(db).get_account_by_id(current_user, account_id)
    if not account:
        return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "finance/edit_account.html",
        {"request": request, "current_user": current_user, "account": account, "error": None},
    )


@router.post("/accounts/{account_id}/edit", response_class=HTMLResponse)
def edit_account_submit(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
    account_name: str = Form(...),
    account_type: str = Form(...),
    currency: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        updated = FinanceAccountService(db).edit_account(
            current_user=current_user,
            account_id=account_id,
            updated_name=account_name,
            updated_type=account_type,
            updated_currency=currency,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/edit_account.html",
            {
                "request": request,
                "current_user": current_user,
                "account": {"id": account_id, "account_name": account_name, "account_type": account_type, "currency": currency},
                "error": str(exc),
            },
            status_code=400,
        )
    if not updated:
        return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/accounts/{account_id}/balance", response_class=HTMLResponse)
def edit_balance_page(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    account = FinanceAccountService(db).get_account_by_id(current_user, account_id)
    if not account:
        return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "finance/edit_balance.html",
        {"request": request, "current_user": current_user, "account": account, "error": None},
    )


@router.post("/accounts/{account_id}/balance", response_class=HTMLResponse)
def edit_balance_submit(
    request: Request,
    account_id: str,
    new_balance: float = Form(...),
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    updated = FinanceAccountService(db).set_account_balance(current_user, account_id, new_balance)
    if not updated:
        account = FinanceAccountService(db).get_account_by_id(current_user, account_id)
        return templates.TemplateResponse(
            "finance/edit_balance.html",
            {"request": request, "current_user": current_user, "account": account, "error": "Account not found."},
            status_code=404,
        )
    return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/categories", response_class=HTMLResponse)
def create_category_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "finance/create_category.html",
        {"request": request, "current_user": current_user, "error": None},
    )


@router.post("/categories", response_class=HTMLResponse)
def category_submit(
    request: Request,
    current_user=Depends(require_user),
    name: str = Form(...),
    category_type: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        CategoryService(db).create_category(current_user=current_user, name=name, category_type=category_type)
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/create_category.html",
            {"request": request, "current_user": current_user, "error": str(exc)},
            status_code=400,
        )
    return RedirectResponse(url="/finance/categories/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/categories/list", response_class=HTMLResponse)
def categories_list_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    categories = CategoryService(db).list_categories(current_user)
    return templates.TemplateResponse(
        "finance/categories_list.html",
        {"request": request, "current_user": current_user, "categories": categories, "error": None},
    )


@router.post("/categories/{category_id}/delete")
def delete_category(
    category_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    CategoryService(db).delete_category(current_user, category_id)
    return RedirectResponse(url="/finance/categories/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/categories/{category_id}/edit", response_class=HTMLResponse)
def edit_category_page(
    request: Request,
    category_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    category = CategoryService(db).get_category_by_id(current_user, category_id)
    if not category:
        return RedirectResponse(url="/finance/categories/list", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "finance/edit_category.html",
        {"request": request, "current_user": current_user, "category": category, "error": None},
    )


@router.post("/categories/{category_id}/edit", response_class=HTMLResponse)
def edit_category_submit(
    request: Request,
    category_id: str,
    current_user=Depends(require_user),
    name: str = Form(...),
    category_type: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        updated = CategoryService(db).edit_category(
            current_user=current_user,
            category_id=category_id,
            updated_name=name,
            updated_type=category_type,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/edit_category.html",
            {
                "request": request,
                "current_user": current_user,
                "category": {"id": category_id, "name": name, "type": category_type},
                "error": str(exc),
            },
            status_code=400,
        )
    if not updated:
        return RedirectResponse(url="/finance/categories/list", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/finance/categories/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/transactions", response_class=HTMLResponse)
def create_transaction_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "finance/create_transaction.html",
        {
            "request": request,
            "current_user": current_user,
            "accounts": FinanceAccountService(db).list_accounts(current_user),
            "categories": CategoryService(db).list_categories(current_user),
            "error": None,
        },
    )


@router.post("/transactions", response_class=HTMLResponse)
def transaction_submit(
    request: Request,
    current_user=Depends(require_user),
    account_id: str = Form(...),
    category_id: str = Form(...),
    txn_type: str = Form(...),
    amount: float = Form(...),
    txn_date: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        TransactionService(db).create_transaction(
            current_user=current_user,
            account_id=account_id,
            category_id=category_id,
            txn_type=txn_type,
            amount=amount,
            txn_date=txn_date,
            description=description,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/create_transaction.html",
            {
                "request": request,
                "current_user": current_user,
                "error": str(exc),
                "accounts": FinanceAccountService(db).list_accounts(current_user),
                "categories": CategoryService(db).list_categories(current_user),
            },
            status_code=400,
        )
    return RedirectResponse(url="/finance/transactions/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/transactions/list", response_class=HTMLResponse)
def transaction_list_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    transactions = TransactionService(db).list_transactions(current_user)
    return templates.TemplateResponse(
        "finance/transactions_list.html",
        {"request": request, "current_user": current_user, "transactions": transactions, "error": None},
    )


@router.post("/transactions/{transaction_id}/delete")
def delete_transaction_route(
    transaction_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    TransactionService(db).delete_transaction(current_user, transaction_id)
    return RedirectResponse(url="/finance/transactions/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
def edit_transaction_page(
    request: Request,
    transaction_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    transaction = TransactionService(db).get_transaction_by_id(current_user, transaction_id)
    if not transaction:
        return RedirectResponse(url="/finance/transactions/list", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "finance/edit_transaction.html",
        {
            "request": request,
            "current_user": current_user,
            "transaction": transaction,
            "accounts": FinanceAccountService(db).list_accounts(current_user),
            "categories": CategoryService(db).list_categories(current_user),
            "error": None,
        },
    )


@router.post("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
def edit_transaction_submit(
    request: Request,
    transaction_id: str,
    account_id: str = Form(...),
    category_id: str = Form(...),
    amount: float = Form(...),
    txn_date: str = Form(...),
    description: str = Form(...),
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        updated = TransactionService(db).edit_transaction(
            current_user=current_user,
            transaction_id=transaction_id,
            updated_account_id=account_id,
            updated_category_id=category_id,
            updated_amount=amount,
            updated_txn_date=txn_date,
            updated_description=description,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/edit_transaction.html",
            {
                "request": request,
                "current_user": current_user,
                "transaction": {
                    "id": transaction_id, "account_id": account_id, "category_id": category_id,
                    "amount": amount, "txn_date": txn_date, "description": description,
                },
                "accounts": FinanceAccountService(db).list_accounts(current_user),
                "categories": CategoryService(db).list_categories(current_user),
                "error": str(exc),
            },
            status_code=400,
        )
    if not updated:
        return RedirectResponse(url="/finance/transactions/list", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/finance/transactions/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/transactions/income", response_class=HTMLResponse)
def income_transactions_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    transactions = TransactionService(db).list_transactions_by_type(current_user, "income")
    return templates.TemplateResponse(
        "finance/income_transactions.html",
        {"request": request, "current_user": current_user, "transactions": transactions},
    )


@router.get("/transactions/expense", response_class=HTMLResponse)
def expense_transactions_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    transactions = TransactionService(db).list_transactions_by_type(current_user, "expense")
    return templates.TemplateResponse(
        "finance/expense_transactions.html",
        {"request": request, "current_user": current_user, "transactions": transactions},
    )


@router.get("/accounts/{account_id}/transactions", response_class=HTMLResponse)
def show_txn_by_account_id(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    account = FinanceAccountService(db).get_account_by_id(current_user, account_id)
    if not account:
        return RedirectResponse(url="/finance/accounts/list", status_code=status.HTTP_303_SEE_OTHER)
    transactions = TransactionService(db).list_transactions_by_account(current_user, account_id)
    return templates.TemplateResponse(
        "finance/account_transactions.html",
        {"request": request, "current_user": current_user, "account": account, "transactions": transactions},
    )


@router.get("/categories/{category_id}/transactions", response_class=HTMLResponse)
def show_txn_by_category(
    request: Request,
    category_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    category = CategoryService(db).get_category_by_id(current_user, category_id)
    if not category:
        return RedirectResponse(url="/finance/categories/list", status_code=status.HTTP_303_SEE_OTHER)
    transactions = TransactionService(db).list_transactions_by_category(current_user, category_id)
    return templates.TemplateResponse(
        "finance/category_transactions.html",
        {"request": request, "current_user": current_user, "category": category, "transactions": transactions},
    )


@router.get("/transactions/date/{target_date}", response_class=HTMLResponse)
def show_txn_by_date(
    request: Request,
    target_date: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    transactions = TransactionService(db).list_transactions_by_date(current_user, target_date)
    return templates.TemplateResponse(
        "finance/date_transactions.html",
        {"request": request, "current_user": current_user, "transactions": transactions, "target_date": target_date},
    )


@router.get("/budgets/list", response_class=HTMLResponse)
def budgets_list(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    svc = BudgetService(db)
    budgets = svc.list_budgets(current_user)
    spending = svc.get_all_budget_spending(current_user)
    for b in budgets:
        spent = spending.get(b["id"], 0.0)
        b["spent"] = spent
        b["remaining"] = b["amount"] - spent
        b["pct"] = min(100, int(spent / b["amount"] * 100)) if b["amount"] else 0
    categories = CategoryService(db).list_categories(current_user)
    return templates.TemplateResponse(
        "finance/budgets_list.html",
        {"request": request, "current_user": current_user, "budgets": budgets, "categories": categories},
    )


@router.get("/budgets/new", response_class=HTMLResponse)
def create_budget_page(
    request: Request,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    categories = CategoryService(db).list_categories(current_user)
    return templates.TemplateResponse(
        "finance/create_budget.html",
        {"request": request, "current_user": current_user, "categories": categories, "error": None},
    )


@router.post("/budgets/new", response_class=HTMLResponse)
def create_budget_submit(
    request: Request,
    current_user=Depends(require_user),
    name: str = Form(...),
    amount: float = Form(...),
    period: str = Form(...),
    category_id: str = Form(""),
    start_date: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        BudgetService(db).create_budget(current_user, name, amount, period, category_id, start_date)
    except ValueError as exc:
        categories = CategoryService(db).list_categories(current_user)
        return templates.TemplateResponse(
            "finance/create_budget.html",
            {"request": request, "current_user": current_user, "categories": categories, "error": str(exc)},
            status_code=400,
        )
    return RedirectResponse(url="/finance/budgets/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/budgets/{budget_id}/edit", response_class=HTMLResponse)
def edit_budget_page(
    request: Request,
    budget_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    budget = BudgetService(db).get_budget_by_id(current_user, budget_id)
    if not budget:
        return RedirectResponse(url="/finance/budgets/list", status_code=status.HTTP_303_SEE_OTHER)
    categories = CategoryService(db).list_categories(current_user)
    return templates.TemplateResponse(
        "finance/edit_budget.html",
        {"request": request, "current_user": current_user, "budget": budget, "categories": categories, "error": None},
    )


@router.post("/budgets/{budget_id}/edit", response_class=HTMLResponse)
def edit_budget_submit(
    request: Request,
    budget_id: str,
    current_user=Depends(require_user),
    name: str = Form(...),
    amount: float = Form(...),
    period: str = Form(...),
    category_id: str = Form(""),
    start_date: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        BudgetService(db).edit_budget(current_user, budget_id, name, amount, period, category_id, start_date)
    except ValueError as exc:
        budget = BudgetService(db).get_budget_by_id(current_user, budget_id)
        categories = CategoryService(db).list_categories(current_user)
        return templates.TemplateResponse(
            "finance/edit_budget.html",
            {"request": request, "current_user": current_user, "budget": budget, "categories": categories, "error": str(exc)},
            status_code=400,
        )
    return RedirectResponse(url="/finance/budgets/list", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/budgets/{budget_id}/delete", response_class=HTMLResponse)
def delete_budget(
    budget_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    BudgetService(db).delete_budget(current_user, budget_id)
    return RedirectResponse(url="/finance/budgets/list", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/budgets/{budget_id}/transactions", response_class=HTMLResponse)
def budget_transactions(
    request : Request,
    budget_id : str,
    db=Depends(get_db),
    current_user=Depends(require_user),
):
    budget = BudgetService(db).get_budget_by_id(current_user, budget_id)
    if not budget:
        return RedirectResponse(
            url="/finance/budgets/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    transactions = TransactionService(db).list_transactions_by_budget(current_user, budget_id)
    spent = sum(t["amount"] for t in transactions if t["txn_type"] == "expense")
    return templates.TemplateResponse(
        "finance/budget_transactions.html",
        {
            "request": request,
            "current_user": current_user,
            "spent": spent,
            "budget": budget,
            "transactions": transactions,
        },
    )


@router.get("/budgets/{budget_id}/add-transaction", response_class=HTMLResponse)
def budget_add_txn_page(
    request: Request,
    budget_id: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    budget = BudgetService(db).get_budget_by_id(current_user, budget_id)
    if not budget:
        return RedirectResponse(url="/finance/budgets/list", status_code=status.HTTP_303_SEE_OTHER)
    accounts = FinanceAccountService(db).list_accounts(current_user)
    categories = CategoryService(db).list_categories(current_user, "expense")
    return templates.TemplateResponse(
        "finance/budget_add_transaction.html",
        {
            "request": request,
            "current_user": current_user,
            "accounts": accounts,
            "budget": budget,
            "categories": categories,
            "error": None,
        },
    )


@router.post("/budgets/{budget_id}/add-transaction", response_class=HTMLResponse)
def budget_add_txn_submit(
    request: Request,
    budget_id: str,
    account_id: str = Form(...),
    category_id: str = Form(...),
    amount: float = Form(...),
    txn_date: str = Form(...),
    description: str = Form(""),
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        TransactionService(db).create_transaction(
            current_user=current_user,
            account_id=account_id,
            category_id=category_id,
            txn_type="expense",
            amount=amount,
            txn_date=txn_date,
            description=description,
            budget_id=budget_id,
        )
    except Exception as exc:
        budget = BudgetService(db).get_budget_by_id(current_user, budget_id)
        accounts = FinanceAccountService(db).list_accounts(current_user)
        categories = CategoryService(db).list_categories(current_user, "expense")
        return templates.TemplateResponse(
            "finance/budget_add_transaction.html",
            {
                "request": request,
                "current_user": current_user,
                "accounts": accounts,
                "budget": budget,
                "categories": categories,
                "error": str(exc),
            },
            status_code=400,
        )
    return RedirectResponse(
        url=f"/finance/budgets/{budget_id}/transactions",
        status_code=status.HTTP_303_SEE_OTHER,
    )