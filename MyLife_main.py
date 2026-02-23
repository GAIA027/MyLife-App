from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from zoneinfo import ZoneInfo

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