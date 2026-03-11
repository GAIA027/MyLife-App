from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import jwt
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("MyLife_main.py")
main_db = Path(__name__).with_name("MyLife_database_file")

def load_database():
    with open(main_db, "r")as file:
        return json.load(file)
    
def save_database(data):
    with open(main_db, "w") as file:
        json.dump(data, file, indent=4)


JWT_SECRET = "JWT_SERCRET"
if not JWT_SECRET:
    raise ValueError("jwt key does not exist")

JWT_ALGORITHM = "HS256"
JWT_EXP_TIME = 60

def create_access_token(user : dict) -> str:
    now = datetime.now(DXB_TZ)

    payload = {
        "sub" : str(user["id"]),
        "username" : str(user["username"]),
        "iat" : int(now.timestamp()),
        "exp" : int(now + timedelta(minutes=JWT_ALGORITHM))
    }
    return jwt.encode(JWT_SECRET, payload, algorithm=JWT_ALGORITHM)

def decode_access_token(token : str) -> str:
    return jwt.encode(token, JWT_SECRET, algorithm=JWT_EXP_TIME)

def get_curent_user_from_token(token : str) -> dict | None:
    try:
        claims = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        logging.warning("Token for this section has expired, Request for logging")
        print("Session expired. Please login again")
    except jwt.InvalidTokenError:
        print("Invalid token")

    data = load_database()
    user_id = claims.get("id")
    return next(user for user in data.get("users", []) if str(user.get("id") == str(user_id), None))

DXB_TZ = ZoneInfo("Asia/Dubai")
DXB_now = datetime.now(DXB_TZ)
print(DXB_now.isoformat(timespec="seconds"))

def dubai_now():
    return datetime.now(ZoneInfo("Asia/Dubai")).isoformat(timespec="seconds")
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})