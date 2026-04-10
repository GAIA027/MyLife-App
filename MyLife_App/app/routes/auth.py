from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.modules.MyLife_Tracker import AccountService as UserAccountService


auth_router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@auth_router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        "auth/signup.html",
        {"request": request, "error": None},
    )


@auth_router.post("/signup", response_class=HTMLResponse)
def signup_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    account_service = UserAccountService()

    try:
        account_service.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "auth/signup.html",
            {"request": request, "error": str(exc)},
            status_code=400,
        )

    return RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@auth_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "error": None},
    )


@auth_router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email_or_username: str = Form(...),
    password: str = Form(...),
):
    account_service = UserAccountService()
    user, token = account_service.authenticate_user(email_or_username, password)

    if not user or not token:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid login credentials"},
            status_code=401,
        )

    response = RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
    )
    return response


@auth_router.get("/logout")
def logout():
    response = RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie("access_token")
    return response
