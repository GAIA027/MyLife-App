from fastapi import FastAPI,status
from fastapi.requests import Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import jwt
import json
import logging
from app.modules.MyLife_Tracker import app_UI, app_dashboard, ensure_current_user
from app.modules.MyLife_Fitness import FitnessOverviewDashboard
from app.modules.MyLife_Finance import Myfinance_dashboard_menu


from app.modules.MyLife_Tracker import (
    create_access_token as tracker_create_access_token,
    decode_access_token as tracker_decode_access_token,
    get_current_user_from_token as tracker_get_current_user_from_token,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("MyLife_main.py")
main_db = Path(__file__).resolve().parents[2] / "data" / "mylife.json"

def load_database():
    with open(main_db, "r")as file:
        return json.load(file)
    
def save_database(data):
    with open(main_db, "w") as file:
        json.dump(data, file, indent=4)

def create_access_token(user : dict) -> str:
    return tracker_create_access_token(user)

def decode_access_token(token : str) -> str:
    return tracker_decode_access_token(token)

def get_curent_user_from_token(token : str) -> dict | None:
    return tracker_get_current_user_from_token(token)

def MyLife_dashboard(current_user : dict | None):
    current_user = ensure_current_user(current_user)
    if not current_user:
        print("Current user not found")
        return
    
    while True:
        print("\n=== MyLife Dashboard ===")
        print("1. Tracker")
        print("2. Fitness")
        print("3. Finance")
        print("4. Logout")
        print("5. Exit")

    
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            app_dashboard(current_user)

        elif choice == "2":
            FitnessOverviewDashboard(current_user)

        elif choice == "3":
            Myfinance_dashboard_menu(current_user)

        elif choice == "4":
            print("Logging out...")
            return

        elif choice == "5":
            print("Exiting MyLife")
            raise SystemExit

        else:
            print("Invalid option")

def start_mylife():
    app_UI()

DXB_TZ = ZoneInfo("Asia/Dubai")
DXB_now = datetime.now(DXB_TZ)
print(DXB_now.isoformat(timespec="seconds"))

def dubai_now():
    return datetime.now(ZoneInfo("Asia/Dubai")).isoformat(timespec="seconds")
app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



if __name__ == "__main__":
    start_mylife()