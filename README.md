MyLife is a full-stack personal productivity web application that brings your tasks, finances, fitness, habits, calendar, and schedule into a single, focused interface — so you stop juggling apps and start making progress.

---

## ✨ Features

MyLife is organised into **seven core modules**, each with its own dedicated dashboard:

| Module | Description |
|--------|-------------|
| ✅ **Task Tracker** | Manage tasks, habits, and projects with deadlines, priorities, and recurring schedules |
| 💰 **Finance** | Track income and expenses, manage multiple accounts, set budgets, and view spending summaries |
| 🏃 **Fitness** | Log workouts, build meal plans, set daily calorie goals, and track routines week by week |
| 📅 **Calendar** | Visualise your schedule, log events by type, and never miss what's coming up |
| 📊 **Statistics** | Cross-module summaries — finance by month, habit completion rates, fitness progress |
| 🗓 **Scheduler** | Build named schedules and fill them with timed activities — your day, structured your way |
| ⚙️ **Settings** | Change your password, toggle dark mode, and personalise your experience |

---

## 🌙 Dark Mode

MyLife ships with a full **black & purple glow** dark mode palette.

- Toggle available on the **home page**, **features page**, **login**, and **signup** — before you even have an account
- Preference is saved to `localStorage` and restored instantly on every page load (no flash)
- The login/signup wallpaper swaps to a custom dark-mode image when toggled

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| **Templating** | Jinja2 |
| **Database** | PostgreSQL via SQLAlchemy ORM |
| **Migrations** | Alembic |
| **Auth** | PyJWT (session token in cookie) |
| **Server** | Uvicorn |
| **Frontend** | Vanilla HTML / CSS / JS — no framework |

---

## 📁 Project Structure

```
MyLife_App/
├── alembic/                          # Database migrations
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py                       
│   ├── config.py
│   ├── dependencies.py               
│   ├── core/
│   │   ├── auth.py
│   │   ├── security.py
│   │   ├── utils.py
│   │   └── validators.py
│   ├── database/
│   │   ├── db.py                     
│   │   ├── models.py                 
│   │   └── schemas.py
│   ├── modules/                     
│   │   ├── MyLife_Calender.py
│   │   ├── MyLife_Finance.py
│   │   ├── MyLife_Fitness.py
│   │   ├── MyLife_Scheduler.py
│   │   ├── MyLife_Tracker.py
│   │   └── MyLife_statistics.py
│   ├── routes/                       
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── finance.py
│   │   ├── fitness.py
│   │   ├── tracker.py
│   │   ├── calendar.py
│   │   ├── scheduler.py
│   │   ├── statistics.py
│   │   ├── settings.py
│   │   └── home.py
│   ├── services/
│   │   ├── calendar_service.py
│   │   ├── finance_service.py
│   │   ├── fitness_service.py
│   │   ├── statistics_service.py
│   │   └── tracker_service.py
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css         
│   │   │   ├── auth/
│   │   │   ├── home/
│   │   │   ├── main-dashboard/
│   │   │   ├── finance/
│   │   │   ├── fitness/
│   │   │   ├── tracker/
│   │   │   ├── calendar/
│   │   │   ├── scheduler/
│   │   │   └── statistics/
│   │   ├── images/
│   │   │   ├── Login:signuppagephoto.jpg
│   │   │   └── Dark mode login:signup photo.webp
│   │   └── js/
│   └── templates/
│       ├── base.html                 
│       ├── auth/                     
│       ├── home/                     
│       ├── dashboard/
│       ├── finance/                 
│       ├── fitness/                 
│       ├── tracker/                  
│       ├── calendar/                 
│       ├── scheduler/                
│       ├── statistics/               
│       └── settings/
├── requirements.txt
├── alembic.ini
└── tests/
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL running locally

### 1. Clone the repo

```bash
git clone https://github.com/Al-Amin-Abdulkadir/MyLife-App.git
cd MyLife_App
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/mylife"
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🔐 Authentication

MyLife uses **JWT tokens stored in HTTP-only cookies**. All module routes are protected by a `require_user` dependency — unauthenticated requests are redirected to a styled session-expired page.

---

## 🎨 Design System

All colours, typography, and dark-mode variables are defined in `app/static/css/styles.css` as CSS custom properties:

```css
:root {
  --bg:      #495A58;   /* earthy green */
  --accent:  #c9a84c;   /* warm gold    */
  --text:    #f0ece4;
}

html[data-theme="dark"] {
  --bg:      #0a0a0f;   /* deep black   */
  --accent:  #a855f7;   /* purple glow  */
}
```

Every module's CSS inherits from these variables — the entire UI flips with a single `data-theme` attribute on `<html>`.

---

## 📜 License

This project is for personal use. All rights reserved © 2025 MyLife.

---
