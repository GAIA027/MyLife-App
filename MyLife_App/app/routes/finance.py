from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.dependencies import require_user
from app.modules.MyLife_Finance import (
    AccountService as FinanceAccountService,
    CategoryService,
    FinanceSummaryService,
    TransactionService,
)

router = APIRouter(prefix="/finance", tags=["finance"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/dashboard", response_class=HTMLResponse)
def finance_dashboard(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "finance/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )
@router.get("/accounts", response_class=HTMLResponse)
def create_account_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "finance/create_account.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )
@router.post("/accounts", response_class=HTMLResponse)
def account_submit(
    request: Request,
    current_user=Depends(require_user),
    account_name: str = Form(...),
    account_type: str = Form(...),
    currency: str = Form(...),
    opening_balance: float = Form(...),
):
    finance_account_service = FinanceAccountService()

    try:
        finance_account_service.create_account(
            current_user=current_user,
            account_name=account_name,
            account_type=account_type,
            currency=currency,
            opening_balance=opening_balance,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/create_account.html",
            {
                "request": request,
                "current_user": current_user,
                "error": str(exc),
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/finance/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/accounts/list", response_class=HTMLResponse)
def accounts_list_page(request: Request, current_user=Depends(require_user)):
    account_service = FinanceAccountService()
    accounts = account_service.list_accounts(current_user)

    return templates.TemplateResponse(
        "finance/accounts_list.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
            "accounts": accounts,
        },
    )
@router.post("/accounts/{account_id}/delete")
def delete_account(account_id: str, current_user=Depends(require_user)):
    account_service = FinanceAccountService()
    account_service.delete_account(current_user, account_id)

    return RedirectResponse(
        url="/finance/accounts/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/accounts/{account_id}/edit", response_class=HTMLResponse)
def edit_account_page(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
):
    account_service = FinanceAccountService()
    account = account_service.get_account_by_id(current_user, account_id)

    if not account:
        return RedirectResponse(
            url="/finance/accounts/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "finance/edit_account.html",
        {
            "request": request,
            "current_user": current_user,
            "account": account,
            "error": None,
        },
    )

@router.post("/accounts/{account_id}/edit", response_class=HTMLResponse)
def edit_account_submit(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
    account_name: str = Form(...),
    account_type: str = Form(...),
    currency: str = Form(...),
):
    account_service = FinanceAccountService()
    try:
        updated_account = account_service.edit_account(
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
                "account": {
                    "id": account_id,
                    "account_name": account_name,
                    "account_type": account_type,
                    "currency": currency,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not updated_account:
        return RedirectResponse(
            url="/finance/accounts/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/finance/accounts/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/categories", response_class=HTMLResponse)
def create_category_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "finance/create_category.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )

@router.post("/categories", response_class=HTMLResponse)
def category_submit(
    request: Request,
    current_user=Depends(require_user),
    name: str = Form(...),
    category_type: str = Form(...),
):
    finance_category_service = CategoryService()

    try:
        finance_category_service.create_category(
            current_user=current_user,
            name=name,
            category_type=category_type,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "finance/create_category.html",
            {
                "request": request,
                "current_user": current_user,
                "error": str(exc),
            },
            status_code=400,
        )
    return RedirectResponse(
        url="/finance/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )
@router.get("/categories/list", response_class=HTMLResponse)
def categories_list_page(request: Request, current_user=Depends(require_user)):
    category_service = CategoryService()
    categories = category_service.list_categories(current_user)

    return templates.TemplateResponse(
        "finance/categories_list.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
            "categories": categories,
        },
    )
@router.post("/categories/{category_id}/delete")
def delete_category(category_id: str, current_user=Depends(require_user)):
    category_service = CategoryService()
    category_service.delete_category(current_user, category_id)

    return RedirectResponse(
        url="/finance/categories/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )
@router.get("/transactions", response_class=HTMLResponse)
def create_transaction_page(request: Request, current_user=Depends(require_user)):
    account_service = FinanceAccountService()
    category_service = CategoryService()

    return templates.TemplateResponse(
        "finance/create_transaction.html",
        {
            "request": request,
            "current_user": current_user,
            "accounts": account_service.list_accounts(current_user),
            "categories": category_service.list_categories(current_user),
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
):
    finance_transaction_service = TransactionService()
    account_service = FinanceAccountService()
    category_service = CategoryService()

    try:
        finance_transaction_service.create_transaction(
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
                "accounts": account_service.list_accounts(current_user),
                "categories": category_service.list_categories(current_user),
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/finance/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/transactions/list", response_class=HTMLResponse)
def transaction_list_page(request: Request, current_user=Depends(require_user)):
    transaction_service = TransactionService()
    transactions = transaction_service.list_transactions(current_user)

    return templates.TemplateResponse(
        "finance/transactions_list.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
            "transactions": transactions,
        },
    )


@router.post("/transactions/{transaction_id}/delete")
def delete_transaction_route(transaction_id: str, current_user=Depends(require_user)):
    transaction_service = TransactionService()
    transaction_service.delete_transaction(current_user, transaction_id)

    return RedirectResponse(
        url="/finance/transactions/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
def edit_transaction_page(
    request: Request,
    transaction_id: str,
    current_user=Depends(require_user),
):
    transaction_service = TransactionService()
    category_service = CategoryService()
    account_service = FinanceAccountService()

    transaction = transaction_service.get_transaction_by_id(current_user, transaction_id)
    if not transaction:
        return RedirectResponse(
            url="/finance/transactions/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "finance/edit_transaction.html",
        {
            "request": request,
            "current_user": current_user,
            "transaction": transaction,
            "accounts": account_service.list_accounts(current_user),
            "categories": category_service.list_categories(current_user),
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
):
    transaction_service = TransactionService()
    account_service = FinanceAccountService()
    category_service = CategoryService()

    try:
        updated_transaction = transaction_service.edit_transaction(
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
                    "id": transaction_id,
                    "account_id": account_id,
                    "category_id": category_id,
                    "amount": amount,
                    "txn_date": txn_date,
                    "description": description,
                },
                "accounts": account_service.list_accounts(current_user),
                "categories": category_service.list_categories(current_user),
                "error": str(exc),
            },
            status_code=400,
        )

    if not updated_transaction:
        return RedirectResponse(
            url="/finance/transactions/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/finance/transactions/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/categories/{category_id}/edit", response_class=HTMLResponse)
def edit_category_page(
    request: Request,
    category_id: str,
    current_user=Depends(require_user),
):
    category_service = CategoryService()
    category = category_service.get_category_by_id(current_user, category_id)

    if not category:
        return RedirectResponse(
            url="/finance/categories/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "finance/edit_category.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
            "category": category,
        },
    )


@router.post("/categories/{category_id}/edit", response_class=HTMLResponse)
def edit_category_submit(
    request: Request,
    category_id: str,
    current_user=Depends(require_user),
    name: str = Form(...),
    category_type: str = Form(...),
):
    category_service = CategoryService()

    try:
        updated_category = category_service.edit_category(
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
                "category": {
                    "id": category_id,
                    "name": name,
                    "type": category_type,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not updated_category:
        return RedirectResponse(
            url="/finance/categories/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/finance/categories/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/transactions/income", response_class=HTMLResponse)
def income_transactions_page(request: Request, current_user=Depends(require_user)):
    transaction_service = TransactionService()
    transactions = transaction_service.list_transactions_by_type(current_user, "income")

    return templates.TemplateResponse(
        "finance/income_transactions.html",
        {
            "request": request,
            "current_user": current_user,
            "transactions": transactions,
        },
    )


@router.get("/transactions/expense", response_class=HTMLResponse)
def expense_transactions_page(request: Request, current_user=Depends(require_user)):
    transaction_service = TransactionService()
    transactions = transaction_service.list_transactions_by_type(current_user, "expense")

    return templates.TemplateResponse(
        "finance/expense_transactions.html",
        {
            "request": request,
            "current_user": current_user,
            "transactions": transactions,
        },
    )


@router.get("/accounts/{account_id}/transactions", response_class=HTMLResponse)
def show_txn_by_account_id(
    request: Request,
    account_id: str,
    current_user=Depends(require_user),
):
    account_service = FinanceAccountService()
    transaction_service = TransactionService()

    account = account_service.get_account_by_id(current_user, account_id)
    if not account:
        return RedirectResponse(
            url="/finance/accounts/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    transactions = transaction_service.list_transactions_by_account(current_user, account_id)

    return templates.TemplateResponse(
        "finance/account_transactions.html",
        {
            "request": request,
            "current_user": current_user,
            "account": account,
            "transactions": transactions,
        },
    )


@router.get("/categories/{category_id}/transactions", response_class=HTMLResponse)
def show_txn_by_category(
    request: Request,
    category_id: str,
    current_user=Depends(require_user),
):
    category_service = CategoryService()
    transaction_service = TransactionService()

    category = category_service.get_category_by_id(current_user, category_id)
    if not category:
        return RedirectResponse(
            url="/finance/categories/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    transactions = transaction_service.list_transactions_by_category(current_user, category_id)

    return templates.TemplateResponse(
        "finance/category_transactions.html",
        {
            "request": request,
            "current_user": current_user,
            "category": category,
            "transactions": transactions,
        },
    )


@router.get("/transactions/date/{target_date}", response_class=HTMLResponse)
def show_txn_by_date(
    request: Request,
    target_date: str,
    current_user=Depends(require_user),
):
    transaction_service = TransactionService()
    transactions = transaction_service.list_transactions_by_date(current_user, target_date)

    return templates.TemplateResponse(
        "finance/date_transactions.html",
        {
            "request": request,
            "current_user": current_user,
            "transactions": transactions,
            "target_date": target_date,
        },
    )

