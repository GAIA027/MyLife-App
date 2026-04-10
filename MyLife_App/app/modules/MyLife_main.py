from fastapi import FastAPI, Request, status, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from app.config import STATIC_DIR, TEMPLATES_DIR, DATA_DIR, BASE_DIR
from app.routes.tracker import router as tracker_router
from app.routes.finance import router as finance_router
from app.routes.fitness import router as fitness_router
from app.routes.calendar import router as calendar_router
from app.routes.statistics import router as statistics_router
from app.routes.dashboard import router as dashboard_router
from app.routes.auth import auth_router
from app.dependencies import get_current_user
from app.modules.MyLife_Tracker import ensure_current_user, AccountService as UserAccountService, get_current_user_from_token
from app.database.schemas import *
from app.modules.MyLife_Finance import AccountService
from app.dependencies import require_user, get_current_user


MylifApp = FastAPI(title="Mylife Web App")
MylifApp.include_router(tracker_router)
MylifApp.include_router(finance_router)
MylifApp.include_router(fitness_router)
MylifApp.include_router(calendar_router)
MylifApp.include_router(statistics_router)
MylifApp.include_router(calendar_router)
MylifApp.include_router(auth_router)
MylifApp.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)



