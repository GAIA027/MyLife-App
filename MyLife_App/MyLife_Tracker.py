# To-DO App allows users to manage their tasks effectively. It provides functionalities to add, view, update, and delete tasks. The app also supports categorizing tasks and setting deadlines.
import re
import hashlib
import random
import string
from wonderwords import RandomWord
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable
import jwt
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("mylife_tracker")

JWT_SECRET = os.getenv("SECRET_KEY", "dev-secret-key")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

def is_due_within_days(task: dict, days: int, tz: str = "Asia/Dubai") -> bool:
    raw_deadline = task.get("task_deadline")
    if not raw_deadline:
        return False

    try:
        deadline = datetime.fromisoformat(raw_deadline).date()
    except ValueError:
        deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()

    today = datetime.now(ZoneInfo(tz)).date()
    delta_days = (deadline - today).days
    return 0 <= delta_days <= days


def create_access_token(user : dict) -> str:
    now = datetime.now(DXB_TZ)

    payload = {
        "sub" : str(user["id"]),
        "username" : user["username"],
        "iat" : int(now.timestamp()),
        "exp" : int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token : str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

def get_current_user_from_token(token : str) -> dict | None:
    try:
        claims = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        logger.warning("Session expired while decoding JWT.")
        print("Session expired. Please login again")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token received.")
        print("Invalid token")
        return None
    
    data = load_database()
    user_id = claims.get("sub")
    current_user = next((u for u in data.get("users", []) if str(u.get("id")) == str(user_id)), None)
    if current_user:
        logger.info("User resolved from token for user_id=%s", user_id)
    else:
        logger.warning("Token decoded but user not found for user_id=%s", user_id)
    return current_user


DXB_TZ = ZoneInfo("Asia/Dubai")
DXB_now = datetime.now(DXB_TZ)
logger.info("App boot timestamp (Dubai): %s", DXB_now.isoformat(timespec="seconds"))
print(DXB_now.isoformat(timespec="seconds"))

def now_dubai():
    return datetime.now(ZoneInfo("Asia/Dubai")).isoformat(timespec="seconds")

def validate_deadline_input(raw_deadline : str, timezone : ZoneInfo = DXB_TZ, allow_past: bool = False):
    raw_deadline = raw_deadline.strip()
    if not raw_deadline:
        return None, "Deadline is required"
    
    accepted_formats = (
        "%Y-%m-%d %H:%M",   
        "%Y-%m-%d",         
        "%m/%d/%Y %H:%M",   
        "%m/%d/%Y",  
    )

    deadline_datetime = None
    for format in accepted_formats:
        try:
            deadline_datetime = datetime.strptime(raw_deadline, format)
            break
        except ValueError:
            continue

    if deadline_datetime is None:
        return None, "Invalid deadline format. use YYYY-MM-DD HH:MM or MM/DD/YYYY HH:MM"
    
    deadline_datetime = deadline_datetime.replace(tzinfo=timezone)
    now = datetime.now(timezone)

    if not allow_past and deadline_datetime <= now:
        return None, "Deadline must be in the future. "
    
    return deadline_datetime.isoformat(timespec="seconds"), None

def user_special_key():
    r = RandomWord()
    special_key = r.word(word_min_length=5,word_max_length=5)
    return special_key

def hash_password(password : str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(input_password : str, stored_password: str) -> bool:
    return hash_password(input_password) == stored_password

database_file = Path(__file__).with_name("MyLife_database_file.json")

def load_database():
    try:
        with open(database_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.exception("Database file not found: %s", database_file)
        raise
    except json.JSONDecodeError:
        logger.exception("Database file is not valid JSON: %s", database_file)
        raise
    
def save_database(data):
    try:
        with open(database_file, "w") as file:
            json.dump(data, file, indent=4)
    except OSError:
        logger.exception("Failed to write database file: %s", database_file)
        raise

def find_user(username):
    data = load_database()
    
    for user in data["users"]:
        if user["username"] == username:
            return user
        return f"User not found"

def generate_id(length = 10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def validate_username(username : str):
    if len(username) < 5:
        return f"username must be at least 5 charchters"
    return None

def validate_email(email : str) -> str:
    email_pattern =  r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, email):
        return f"Invalid email format"
    return None

def validate_password(password : str) -> str:
    if len(password) < 8:
        return f"password must be at least 8 characters"
    
    if not any(char.isupper() for char in password):
        return f"password must contain at least one uppercae letter"
    if not any(char.islower() for char in password):
        return f"password must contain at least one lowercase letter"
    if not any(char.isdigit() for char in password):
        return f"Password must contain at least one number"
    if not any(char in "!@#$%^&*()-_=+[{]}|;:'\",<.>/?`~" for char in password ):
        return f"Password must contain at least a special character"
    
    return None

def user_create_account():
    data = load_database()

    logger.info("Signup flow started.")
    print("\n===Signup===")
    username = input("username : ").strip().lower()
    validate_username(username)
    email = input("Email : ").strip().lower()
    validate_email(email)
    password = input("Password : ")
    validate_password(password)

    for user in data["users"]:
        if user["email"] == email:
            logger.warning("Signup rejected: duplicate email=%s", email)
            print("User already exists")
            return
    hashed = hash_password(password)

    new_user = {
        "id" : generate_id(),
        "first_name" : input("First name : "),
        "last_name" : input("Last name : "),
        "username" : username,
        "email" : email,
        "password" : hashed,
        "tasks" : [],
        "projects" : [],
        "habits" : [],
        "finance" : [],
        "fitness" : [],
        "archived_tasks_log" : [],
        "archived_habits_log" : [],
        "archived_projects_log" : [],
        "tasks" : []
    }
    data["users"].append(new_user)
    save_database(data)
    logger.info("Signup successful for username=%s", username)
    print(f"\nSignup successful. Welcome to MyLife ")
    return new_user

def user_login():
    logger.info("Login flow started.")
    print("\n===Log-in===")
    data = load_database()

    email_or_username = input("\nEmail or Username : ").strip().lower()
    for user in data["users"]:
        if user["email"] == email_or_username or user["username"] == email_or_username:
            user_password_attempt_left = 3
            while user_password_attempt_left > 0:
                password = input("\nPassword : ")
                if verify_password(password, user["password"]):
                    token = create_access_token(user)
                    time.sleep(3)
                    logger.info("Login successful for username=%s", user.get("username"))
                    print("\nLogin Successful. Welcome to MyLife")
                    return user, token
                else:
                    user_password_attempt_left -= 1
                    logger.warning(
                        "Invalid password attempt for username=%s. attempts_left=%s",
                        user.get("username"),
                        user_password_attempt_left,
                    )
                    print(f"\nIncorrect password. You have {user_password_attempt_left} attempts left.")
            logger.warning("Login failed after max attempts for identifier=%s", email_or_username)
            print("User not found. Please check your email/username and try again.")
    logger.warning("Login failed: account not found for identifier=%s", email_or_username)
    return None, None

class task:
    def __init__(self):
        pass
    def create_task(current_user : str, task_name, task_type, task_description, created_at, task_deadline, task_notes):
        data = load_database()

        for user in data["users"]:
            if user["id"] == current_user["id"]:

                task = {
                    "id" : generate_id(),
                    "task_name": task_name,
                    "task_type": task_type,
                    "task_description" : task_description,
                    "created_at": created_at,
                    "task_deadaline": task_deadline,
                    "task_notes": task_notes
                    
                }
                data["tasks"].append(task)
                save_database(data)
                return True
            return f"user ID not found"
    def view_tasks(self):
        data = load_database()
        return data["tasks"]
    
    def update_task(self,user_update_request,  task_name : str, task_description : str, task_type : str, created_at : str, task_deadline : str, task_notes : str) -> str:
        data = load_database()
        for task in data["tasks"]:
                if task["task_name"] == user_update_request:
                    task.update({
                    "task_name": task_name,
                    "task_type": task_type,
                    "task_description" : task_description,
                    "created_at": created_at,
                    "task_deadaline": task_deadline,
                    "task_notes": task_notes
                })
                
                return f"Task updated successfully!"
        return f"Task not found! Please check the title and try again."
    
    def delete_task(self, delete_request):
        data = load_database()
        for task in data["tasks"]:
            if task["task_name"] == delete_request:
                data["tasks"].remove(task)
                return f"Task deleted successfully!"
            return f"Task not found"

def show_tasks(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data = load_database()

    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue

        tasks = user.get("tasks", [])
        if not tasks:
            print("No tasks found for this user.")
        else:
            print("\n===Tasks===")
            for task in tasks:
                logging.info(
                    f"- {task.get('task_name', 'Untitled')} "
                    f"[{task.get('status', 'pending')}] "
                    f"(deadline: {task.get('task_deadline', 'N/A')})"
                    f"\n  Description: {task.get('task_description', '')}"
                    f"\n  Notes: {task.get('task_notes', '')}"
                    f"\n  Created at: {task.get('created_at', '')}"
                    f"\n  Updated at: {task.get('updated_at', '')}"
                )

        if input("Main menu  Yes/No: ").strip().lower() == "yes":
            app_dashboard(current_user)
        return

    logging.info("Current user not found.")

def remove_task(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return

    data = load_database()
    delete_request = input("Enter the title of the task you want to delete: ")
    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue
        tasks = user.setdefault("tasks", [])
        for task in tasks:
            if task.get("task_name") == delete_request:
                tasks.remove(task)
                save_database(data)
                print("Task deleted successfully!")
                if input("Main menu  Yes/No: ").strip().lower() == "yes":
                    app_dashboard(current_user)
                return
    print("Task not found! Please check the title and try again.")

task_main = task()


def record_task(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data = load_database()

    task_title = input("Task title: ").strip()
    task_description = input("Description: ").strip()
    task_type = input("Task type: ").strip()
    created_at = now_dubai()
    raw_task_deadline = input("Task deadline (YYYY-MM-DD HH:MM): ").strip()
    task_deadline, deadline_error = validate_deadline_input(raw_task_deadline)
    if deadline_error:
        logger.warning("Task creation failed: invalid deadline input (%s)", deadline_error)
        print(deadline_error)
        return
    
    task_notes = input("Task notes: ").strip()

    for user in data.get("users", []):
        if str(user.get("id")) == str(current_user.get("id")):
            user.setdefault("tasks", []).append({
                "id": generate_id(),
                "task_name": task_title,
                "task_description": task_description,
                "task_type": task_type,
                "create_at": created_at,
                "task_deadline": task_deadline,
                "task_notes": task_notes,
                "created_at" : now_dubai(),
                "updated_at " : now_dubai(),
                "status " : "pending",
                "completed_at" : False

            })
            
            save_database(data)
            logger.info("Task created for user_id=%s with title=%s", current_user.get("id"), task_title)
            print(f"\n===Task Recorded Successfully. Saved to {database_file}===")
            app_dashboard(current_user)
            return

    logger.warning("Task creation failed: current user not found in database user_id=%s", current_user.get("id"))
    print("Current user not found in database.")


def update_task(current_user):
    if not current_user:
        print("Please log in first.")
        return

    data = load_database()
    task_title = input("Enter the title of the task you want to update: ")
    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue
        tasks = user.setdefault("tasks", [])
        for task in tasks:
            if task.get("task_name") != task_title:
                continue
            print("Task found! Enter the new details:")
            new_task_title = input("New task title: ").strip()
            task_description = input("New description: ").strip()
            task_type = input("New task type: ").strip()
            raw_task_deadline = input("Task deadline (YYYY-MM-DD HH:MM): ").strip()
            task_deadline, deadline_error = validate_deadline_input(raw_task_deadline)
            if deadline_error:
                print(deadline_error)
                return
            task_notes = input("New task notes: ").strip()
            task.update({
                "task_name": new_task_title or task.get("task_name"),
                "task_type": task_type or task.get("task_type", ""),
                "task_description": task_description or task.get("task_description", ""),
                "task_deadline": task_deadline,
                "task_notes": task_notes or task.get("task_notes", "")
            })
            task["updated_at"] = now_dubai()
            save_database(data)
            print("Task updated successfully!")
            app_dashboard(current_user)
            return
    print("Task not found! Please check the title and try again.")

def mark_task_as_complete(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    
    data = load_database()
    task_name = input("Enter task name to mark complete: ").strip().lower()
    now = now_dubai()

    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue

        tasks = user.setdefault("tasks", [])
        for task in tasks:
            if task.get("task_name", "").strip().lower() != task_name:
                continue

            task["status"] = "completed"
            task["completed_at"] = now
            task["updated_at"] = now
            save_database(data)
            print("Task marked as completed.")
            return

        print("Task not found")
        return
    print("Current user not found")
                    
def create_habit(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data = load_database()
    habit_name = input("Habit name: ").lower()
    habit_description = input("Description: ").strip()
    habit_frequency = input("Habit frequency (e.g., daily, weekly): ").strip()
    raw_habit_start_date = input("Start date (YYYY-MM-DD or MM/DD/YYYY): ").strip()
    habit_start_date, start_date_error = validate_deadline_input(raw_habit_start_date, timezone=DXB_TZ, allow_past=True)
    if start_date_error:
        logger.warning("Habit creation failed: invalid start date (%s)", start_date_error)
        print(start_date_error)
        return
    habit_notes = input("Habit notes: ").strip()

    for user in data.get("users", []):
        if str(user.get("id")) == str(current_user.get("id")):
            user.setdefault("habits", []).append({
                "user_id" : generate_id(),
                "habit_name": habit_name,
                "habit_description" : habit_description,
                "habit_frequency" : habit_frequency,
                "habit_start_date" : habit_start_date,
                "habit_notes" : habit_notes,
                "completion_log" : [],
                "streak" : 0,
                "best_streak" : 0,
                "last_completed_date" : None,
                "created_at" : now_dubai(),
                "updated_at " : now_dubai(),
                "status " : "pending",
                "completed_at" : None
            })
            save_database(data)
            logger.info("Habit created for user_id=%s with habit_name=%s", current_user.get("id"), habit_name)
            print("\n===Habit Created successfully")
            app_dashboard(current_user)

def update_habit(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    
    data = load_database()
    habit_name_to_update = input("Enter habit name to upadate: ").lower()

    for user in data.get("users", []):
        if str(user.get("id")) == str(current_user.get("id")):
            habits = user.setdefault("habits", [])

            for habit in habits:
                if habit.get("habit_name", "").strip().lower() == habit_name_to_update:
                     new_description = input(f"New description [{habit.get('habit_description', '')}]: ").strip()
                     new_frequency = input(f"New frequency [{habit.get('habit_frequency', '')}]: ").strip()
                     new_start_date = input(f"New start date [{habit.get('habit_start_date', '')}]: ").strip()
                     new_notes = input(f"New notes [{habit.get('habit_notes', '')}]: ").strip()

                     habit.update({
                        "habit_description": new_description or habit.get("habit_description", ""),
                        "habit_frequency": new_frequency or habit.get("habit_frequency", ""),
                        "habit_start_date": new_start_date or habit.get("habit_start_date", ""),
                        "habit_notes": new_notes or habit.get("habit_notes", ""),
                    })
                     habit["updated_at"] = now_dubai()
                     save_database(data)
                     print("Habit updated successfully!")
                     return
            print("Habit not found.")
            return

    print("Current user not found.")

def show_habits(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data = load_database()
        
    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue
            
        habits = user.get("habits", [])
        if not habits:
            print("No habits found for this user")
        else:
            print("\n===Habits===")
            for habit in habits:
                print(
                    f"- {habit.get('habit_name', 'untitled')}"
                    f" [{habit.get('status', 'pending')}]"
                    f"\n Description: {habit.get('habit_description', '')}"
                    f"\n Notes: {habit.get('habit_notes', '')}"
                    f"\n Created at: {habit.get('created_at', '')}"
                    f"\n Updated at: {habit.get('updated_at', '')}"
                )
        if input("Main menu Yes/No?: ").strip().lower() == "yes":
            app_dashboard(current_user)
            return
        return
    print("User not found")
                    
def user_has_habits(current_user):
    data = load_database()

    for user in data.get("users"):
        if str(user.get("id")) == str(current_user.get("id")):
            habits = user.get("habits", [])
            return len(habits) > 0
        return False
    
def mark_habit_as_complete(current_user):
    if not current_user:
        print("Please log in first")
        return
    
    data = load_database()
    habit_name = input("Enter the habit name you want to mark complete: ").strip().lower()
    now  = now_dubai()

    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue

        habits = user.setdefault("habits", [])
        for habit in habits:
            if habit.get("habit_name", "").strip().lower() != habit_name:
                continue
            updated = update_habit_streak(habit)
            habit["status"] = "completed"
            habit["completed_at"] = now
            habit["updated_at"] = now
            save_database(data)

            if updated:
                print(f"Habit marked complete. Current streak: {habit.get('streak', 0)}")
                print(f"Best streak: {habit.get('best_streak', habit.get('streak', 0))}")
            else:
                print("Habit already completed today.")
            return
        print("Habit not found")
        return
    print("Current user not found")

def update_habit_streak(habit : dict ) -> bool:
    today = datetime.now(ZoneInfo("Asia/Dubai")).date()
    today_str = today.isoformat()

    last_completed = habit.get("last_completed_date")
    if last_completed == today_str:
        return False
    
    if last_completed:
        delta_days = (today-date.fromisoformat(last_completed)).days
        habit["streak"] = habit.get("streak", 0) + 1 if delta_days == 1 else 1
    else:
        habit["streak"] = 1

    habit["best_streak"] = max(habit.get("best_streak", 0), habit["streak"])
    habit["last_completed_date"] = today_str
    habit.setdefault("completion_log", []).append(today_str)
    return True

def delete_habit(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    habit_delete_request = input("Enter the name of the habit you want to delete: ")
    data = load_database()
    for user in data.get("users", []):
        habits = user.setdefault("habits", [])
        for habit in habits:
            if habit["habit_name"] == habit_delete_request:
                habits.remove(habit)
                save_database(data)
                print("Habit deleted successfully!")
                if input("Main menu  Yes/No: ").strip().lower() == "yes":
                    app_dashboard(current_user)
                return
    print("Habit not found! Please check the title and try again.")
class project:
    def __init__(self) -> None:
        self.projects : list[dict[str, str | int]] = []

    def create_projects(self,
                        project_title : str,
                        project_description : str,
                        project_duration : int,
                        project_created_at : str,
                        project_notes : str ) -> dict[str, str | int]:
        self.projects.append({
            "project_title" : project_title,
            "project_description" : project_description,
            "project_duration" : project_duration,
            "project_created_at" : project_created_at,
            "project_notes" : project_notes
        })
    
    def show_projects(self):
        output = self.projects
        return output
    
    def delete_project(self, project_delete_request : str):
        for project in self.projects:
            if project["project_title"] == project_delete_request:
                self.projects.remove(project)
                return f"Project deleted successfully"
        return "Project not found"

project_main = project()

def record_project(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data = load_database()
    project_title = input("Project title: ").strip().lower()
    project_description = input("Description: ").strip()
    try:
        project_duration = int(input("Project duration in days: "))
    except ValueError:
        logger.warning("Project creation failed: non-integer duration.")
        print("Project duration must be a whole number.")
        return
    project_created_at = now_dubai()
    raw_project_deadline = input("Project deadline (YYYY-MM-DD HH:MM): ").strip()
    project_deadline, deadline_error = validate_deadline_input(raw_project_deadline)
    if deadline_error:
        logger.warning("Project creation failed: invalid deadline input (%s)", deadline_error)
        print(deadline_error)
        return
    project_notes = input("Project notes: ").strip()

    for user in data.get("users", []):
        if str(user.get("id")) == str(current_user.get("id")):
            user.setdefault("projects", []).append({
                "project_title" : project_title,
                "project_description" : project_description,
                "project_duration" : project_duration,
                "project_created_at" : project_created_at,
                "project_deadline" : project_deadline,
                "project_notes" : project_notes,
                "created_at" : now_dubai(),
                "updated_at " : now_dubai(),
                "status" : "pending",
                "completed_at" : None
            })
            save_database(data)
            logger.info("Project created for user_id=%s title=%s", current_user.get("id"), project_title)
            print("Project created successfully")
            app_dashboard(current_user)
    

def view_projects(current_user):
    if not current_user:
        print("Please login first")
        return
    data = load_database()
    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue
        print(user.get("projects", []))
        break
    if input("Main menu  Yes/No: ").strip().lower() == "yes":
        app_dashboard(current_user)
    

def update_project_task(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data = load_database()
    project_update_request = input("Project title : ")
    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue
        projects = user.setdefault("projects", [])
        for project in projects:
            if project.get("project_title") != project_update_request:
                continue
            print("Project found! Enter new details")
            project_title = input("New project title: ").strip()
            project_description = input("New description: ").strip()
            project_notes = input("Project notes: ").strip()
            raw_project_deadline = input("Project deadline (YYYY-MM-DD HH:MM): ").strip()
            project_deadline, deadline_error = validate_deadline_input(raw_project_deadline)
            if deadline_error:
                print(deadline_error)
                return
            project.update({
                "project_title": project_title or project.get("project_title", ""),
                "project_description": project_description or project.get("project_description", ""),
                "project_deadline": project_deadline,
                "project_notes": project_notes or project.get("project_notes", ""),
                "updated_at": now_dubai(),
            })
            save_database(data)
            print("Project updated successfully!")
            app_dashboard(current_user)
            return
    print("Project not found! Please check the title and try again.")

def delete_project(current_user):
    if not current_user:
        print("Please login first")
        return
    data = load_database()
    project_delete_request = input("Enter the title of the project you want to delete: ")
    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue
        projects = user.setdefault("projects", [])
        for project in projects:
            if project.get("project_title") == project_delete_request:
                projects.remove(project)
                save_database(data)
                print("Project deleted successfully!")
                if input("Main menu  Yes/No: ").strip().lower() == "yes":
                    app_dashboard(current_user)
                return
    print("Project not found! Please check the title and try again.")

def mark_project_as_complete(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    
    data = load_database()
    project_title = input("Enter the project name you want to mark complete: ").strip().lower()
    now = now_dubai()

    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue

        projects = user.setdefault("projects", [])
        for project in projects:
            title = project.get("project_title", "").strip().lower()
            if title != project_title:
                continue

            project["status"] = "completed"
            project["completed_at"] = now
            project["updated_at"] = now
            save_database(data)
            print("Project marked as completed.")
            return

        print("Project not found.")
        return
    print("Current user not found")


def exit_app(current_user=None):
    user_exit_request = input("\nExit MyLife")
    if user_exit_request == "Yes":
        print("Exited!")
    elif user_exit_request == "No":
        app_dashboard(current_user)

def user_register_text():
    register_request = input("Do you have an account?   yes/no").strip().lower()
    if register_request == "yes":
        user_login()
    elif register_request == "no":
        user_create_account()


def set_priority(task_id, cureent_user):
    data = load_database()

    for user in data.get("users"):
        if str(user.get("id")) == str(cureent_user.get("id")):
            tasks = user.setdefault("tasks", [])

            for task in tasks:
                if task["id"] == task_id:
                    priority = int(input("priority level\n1 - very low\n2 - low\n3 - Medium\n4 - high\n5 - Very high"))
                    if 1 <= priority <= 5:
                        task["priority"] = priority
                        save_database(data)
                        print("priority updated")
                    else:
                        return f"invalid range"

@dataclass
class ArchiveStore:
    archived_habits_log : list[dict] = field(default_factory=list)
    archived_tasks_log : list[dict] = field(default_factory=list)
    archived_projects_log : list[dict] = field(default_factory=list)

    def archive_habits(self, current_user, habit_name):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                habits = user.setdefault("habits", [])
                for i, habit in enumerate(habits):
                    if habit.get("habit_name", "").strip().lower() == habit_name.strip().lower():
                        archive_entry = habit.copy()
                        archive_entry["archive_id"] = generate_id()
                        archive_entry["archived_at"] = now_dubai()
                        self.archived_habits_log.append(archive_entry)

                        habits.pop(i)
                        save_database(data)
                        return True
        return False

    def archive_tasks(self, current_user, task_name):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                tasks = user.setdefault("tasks", [])
                for i, task in enumerate(tasks):
                    if task.get("task_name", "").strip().lower() == task_name.strip().lower():
                        archive_entry = task.copy()
                        archive_entry["archive_id"] = generate_id()
                        archive_entry["archived_at"] = now_dubai()
                        self.archived_tasks_log.append(archive_entry)

                        tasks.pop(i)
                        save_database(data)
                        return True
        return False

    def archive_projects(self,current_user, project_title):
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                projects = user.setdefault("projects", [])

                for i, project in enumerate(projects):
                    if project.get("project_title", "").strip().lower() == project_title.strip().lower():
                        archive_entry = project.copy()
                        archive_entry["archive_id"] = generate_id()
                        archive_entry["archived_at"] = now_dubai()
                        self.archived_projects_log.append(archive_entry)

                        projects.pop(i)
                        save_database(data)
                        return True
        return False

    def save_archive(self, currnet_user):
        currnet_user = ensure_current_user(currnet_user)
        if not currnet_user:
            return False, "Please log in first"

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(currnet_user.get("id")):
                user["archive"] = {
                    "archive_habits_log" : self.archive_habits_log,
                    "archive_tasks_log" : self.archived_tasks_log,
                    "archive_projects_log" : self.archived_projects_log
                }
                save_database(data)
                return True, "Saved"
            return False, "User not found"

    def load_archive(self, current_user):
        current_user = ensure_current_user(current_user)
        if not current_user:
            print("Please login first")
            return
        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                archived_data = user.get("archive", {})
                self.archive_habits_log = archived_data.get("archive_habits_log", [])
                self.archived_tasks_log = archived_data.get("archive_tasks_log", [])
                self.archived_projects_log = archived_data.get("archived_projects_log", [])
                return True
        print("current user not found")
        return False
    
    def view_archive(self, current_user : dict) -> dict[str, str, int | bool | float]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False
        data_loader = load_database()
        for user in data_loader.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                user["archive"] = {
                    "archived_habits_log" : self.archived_habits_log,
                    "archived_tasks_log" : self.archived_tasks_log,
                    "archived_projects_log" : self.archived_projects_log,
                    "updated_at" : now_dubai()
                }
                save_database(data_loader)
                return True
        print("Current user not found")
        return False
        
def ensure_current_user(current_user):
    if current_user:
        return current_user
    print("Please log in first. ")
    user, _ = user_login()
    return user

def archive_dashboard(current_user):
    pass
@dataclass(slots=True)
class Tracker_search_engine:
        data_loader: Callable[[], dict[str, Any]] = load_database

        @staticmethod
        def find_user(users : list[dict[str, Any]],current_user : dict) -> dict |None:
            current_id = str(current_user.get("id"))
            return next((user for user in users if str(user.get("id")) == str(current_id)), None)
        def search_collection(
                self,
                current_user : dict | None,
                collection_key : str,
                title_key : str,
                keyword : str | None = None,
        ) -> list[dict[str, Any]]:
            current_user = ensure_current_user(current_user)
            if not current_user:
                return []
            
            data = self.data_loader()
            user = self.find_user(data.get("users", []), current_user)
            if not user:
                print("user not found")
                return []

            if keyword is None:
                keyword = input("search keyword : ").lower()

            if not keyword:
                print("Keyword not found")
                return []
            
            items = user.get(collection_key, [])
            matches = [item for item in items if keyword in str(item.get(title_key, "")).lower()]
            if not matches:
                print("Keyword not found")
            else:
                print(f"found {len(matches)} match(es):")
                for item in matches:
                    print(item)
            
            return matches
        
        def search_tasks_engine(self, current_user : dict | None, keyword : str | None = None):
            return self.search_collection(current_user, "tasks", "task_name", keyword)
        
        def search_habits_engine(self, current_user : dict | None, keyword : str | None = None):
            return self.search_collection(current_user, "habits", "habit_name", keyword)
        
        def search_projects_engine(self, current_user : dict | None, keyword : str | None = None):
            return self.search_collection(current_user, "projects", "project_title", keyword)

search_engine = Tracker_search_engine()

def change_password(current_user : dict) -> dict | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return False
    
    data_loader : Callable[[], dict[str, Any]] = load_database()
    current_id = str(current_user.get("id"))
    for user in data_loader.get("users", []):
        if str(user.get("id")) != str(current_id):
            continue

        current_password = input("Enter your current password to change")
        if not verify_password(current_password, user.get("password", [])):
                logger.warning("Password change failed: incorrect current password for user_id=%s", current_id)
                print("Incorrect password")
                time.sleep(2)
                print("Enter your current password to change password")
                return False

        new_passoword = input("Enter your new password : ")
        validation_error = validate_password(new_passoword)
        if validation_error:
            logger.warning("Password change validation failed for user_id=%s: %s", current_id, validation_error)
            print(validation_error)
            return False
        
        if verify_password(new_passoword, user.get("password", "")):
            logger.warning("Password change rejected: new password matches current for user_id=%s", current_id)
            print("Your new password cannot be your current password")
            return False
        
        user["password"] = hash_password(new_passoword)
        save_database(data_loader)
        logger.info("Password changed successfully for user_id=%s", current_id)
        print("Password changed successfully")
        return True
    
    logger.warning("Password change failed: user not found for user_id=%s", current_id)
    print("user not found")
    return False

def delete_account(current_user : dict):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return False
    
    data_loader = load_database()
    current_id = str(current_user.get("id"))
    for user in data_loader.get("users", []):
        if str(user.get("id")) != str(current_id):
            continue

        delete_request = input("\nAre you sure you want to delete your account? yes/no").lower()
        if delete_request == "yes":
            current_password = input("Enter your password to confirm account deletion")
            if not verify_password(current_password, user.get("password")):
                logger.warning("Account deletion failed: incorrect password for user_id=%s", current_id)
                print("Password incorrect")
                time.sleep(2)
                print("Enter your current password to delete this account")
                return False
            data_loader["users"].remove(user)
            save_database(data_loader)
            logger.info("Account deleted successfully for user_id=%s", current_id)
            print("User deleted successfully")
        else:
            logger.info("Account deletion cancelled for user_id=%s", current_id)
            app_settings(current_user)

def create_tag(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data_loader : list[dict[str, str | int | bool | float]] = load_database()
    current_id = str(current_user.get("id"))
    for user in data_loader.get("users", []):
        if str(user.get("id")) != str(current_id):
            continue

    tag_name = input("\nTag name : ").lower()
    if not tag_name:
        logger.warning("Tag creation failed: empty tag name for user_id=%s", current_id)
        print("Tag name is required")
        return False
    
    tags = user.setdefault("tags", [])

    if any(tag.get("tag_name", "").strip().lower() == tag_name for tag in tags):
        logger.warning("Tag creation failed: duplicate tag '%s' for user_id=%s", tag_name, current_id)
        print("Tag already exists")
        return False
    display_tag_color()
    try:
        tag_color = int(input("\nEnter a color for yout current tag"))
    except ValueError:
        logger.warning("Tag creation failed: invalid tag color for user_id=%s", current_id)
        print("Enter a valid number for color")
        return False
    tag_description = input("Description : ")

    tags.append({
        "id" : generate_id(),
        "tag_name" : tag_name,
        "tag_color" : tag_color,
        "tag_description" : tag_description,
        "created_at" : now_dubai(),
        "updated_at" : now_dubai()
    })
    save_database(data_loader)
    logger.info("Tag created successfully: tag_name=%s user_id=%s", tag_name, current_id)
    print("Tag created successfully")
    return True

def view_tag(current_user) -> dict[str,str | int | bool | float ]:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data_loader : list[dict[str, str, int | bool | float]] = load_database()
    current_id = str(current_user.get("id"))
    for user in data_loader.get("users", []):
        if str(user.get("id")) != str(current_id):
            continue

        tags = user.get("tags", [])
        print("\nTags")

        for tag in tags:
            print(
                f"- {tag.get('tag_name', 'untitled')}"
                f"\n Color: {tag.get('tag_color', '')}"
                f"\n Description: {tag.get('tag_description', '')}"
                f"\n Created at: {tag.get('created_at', '')}"
                f"\n Updated at: {tag.get('updated_at', '')}"
            )
            save_database(data_loader)
        if input("Main menu Yes/No?: ").strip().lower() == "yes":
            app_dashboard(current_user)
            return
        return
    
def edit_tag(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    data_loader : list[dict[str, str, int | bool | float]] = load_database()
    current_id = str(current_user.get("id"))
    for user in data_loader.get("users", []):
        if str(user.get("id")) != str(current_id):
            continue

        tags = user.setdefault("tags", [])
        tag_name_to_update = input("Enter the name of the tag you want to edit : ").strip().lower()

        for tag in tags:
            if tag.get("tag_name", "").strip().lower() == tag_name_to_update:
                new_tag_name = input(f"New tag name [{tag.get('tag_name', '')}]: ").strip()
                display_tag_color()
                try:
                    new_tag_color = int(input(f"New tag color [{tag.get('tag_color', '')}]: "))
                except ValueError:
                    print("Enter a valid number for color")
                    return
                new_tag_description = input(f"New tag description [{tag.get('tag_description', '')}]: ").strip()

                tag.update({
                    "tag_name": new_tag_name or tag.get("tag_name", ""),
                    "tag_color": new_tag_color or tag.get("tag_color", ""),
                    "tag_description": new_tag_description or tag.get("tag_description", ""),
                    "updated_at": now_dubai()
                })
                save_database(data_loader)
                print("Tag updated successfully!")
                app_dashboard(current_user)
                return
        print("Tag not found! Please check the name and try again.")

def delete_tag(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    
    data_loader : list[dict[str, str | bool | float]] = load_database()
    current_id = str(current_user.get("id"))
    tag_name_to_update = input("Enter the name of the tag you want to remove")

    for user in data_loader.get("users", []):
        if str(user.get("id")) != str(current_id):
            continue

        tags = user.setdefault("tags", [])

        for tag in tags:
            if tag.get("tag_name", "").strip().lower() == tag_name_to_update:
                tag.remove(tag_name_to_update)
                save_database(data_loader)
                print("Tag removed successfully")
                return True
            print("Tag not found")
            time.sleep(0.15)
            print("Enter the correct tag name you want to delete")
            return False
    print("User not found")
    return False

def attach_tag_to_item(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return False
    data_loader: dict[str, Any] = load_database()
    current_id = str(current_user.get("id"))
    user = next(
        (u for u in data_loader.get("users", []) if str(u.get("id")) == current_id),
        None,
    )

    if not user:
        print("User not found")
        return False
    
    tags = user.setdefault("tags", [])
    if not tags:
        print("No tags found. Create a tag first")
        return False
    

    get_items()
    try:
        item_type = int(input("\n 1. Task. 2. habit 3. projects"))
    except ValueError:
        print("Enter a valid number")
        return False
    
    tag_name = input("Tag name : ").strip().lower()
    tag_obj = next(
        (tag for tag in tags if tag.get("tag_name", "").strip().lower() == tag_name),
        None,
    )
    if not tag_obj:
        print("Tag does not exist")
        return False
    
    if item_type == 1:
        task_name = input("Task name : ").strip().lower()
        tasks = user.setdefault("tasks", [])
        task = next(
            (t for t in tasks if t.get("task_name", "").strip().lower() == task_name),
            None,
        )
        if not task:
            print("Task not found")
            return False
        task.setdefault("tags", [])
        if tag_name not in task["tags"]:
            task["tags"].append(tag_name)
        task["updated_at"] = now_dubai()
        save_database(data_loader)
        print("Task updated successfully")
        return True

    elif item_type == 2:
        habit_name = input("Habit name : ").strip().lower()
        habits = user.setdefault("habits", [])
        habit = next(
            (h for h in habits if h.get("habit_name", "").strip().lower() == habit_name),
            None,
        )
        if not habit:
            print("Habit not found")
            return False
        habit.setdefault("tags", [])
        if tag_name not in habit["tags"]:
            habit["tags"].append(tag_name)
        habit["updated_at"] = now_dubai()
        save_database(data_loader)
        print("Habit updated successfully")
        return True

    elif item_type == 3:
        project_name = input("Project name : ").strip().lower()
        projects = user.setdefault("projects", [])
        project = next(
            (p for p in projects if p.get("project_title", "").strip().lower() == project_name),
            None,
        )
        if not project:
            print("Project not found")
            return False
        project.setdefault("tags", [])
        if tag_name not in project["tags"]:
            project["tags"].append(tag_name)
        project["updated_at"] = now_dubai()
        save_database(data_loader)
        print("Project updated successfully")
        return True
    else:
        print("Enter a valid number")
        return False

def remove_tag_to_item(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    
    data_loader : list[dict[str, str | int | float | bool]] = load_database()
    current_id = str(current_user.get("id"))
    user = ((user for user in data_loader.get("users", []) == str(current_id))), None
    if not user:
        print("user not found")
        return False
    
    tags = user.setdefault("tags", [])
    if not tags:
        print("No tags found. Create a tag first")
        return False
    
    get_items()
    try:
        item_type = int(input("\n 1. Task. 2. habit 3. projects"))
    except ValueError:
        print("Enter a valid number")
        return False
    
    tag_name = input("Tag name : ").strip().lower()
    tag_obj = next(
        (tag for tag in tags if tag.get("tag_name", "").strip().lower() == tag_name),
        None,
    )
    if not tag_obj:
        print("Tag does not exist")
        return False
    
    if item_type == 1:
        task_name = input("Task name : ").strip().lower()
        tasks = user.setdefault("tasks", [])
        task = next(
            (t for t in tasks if t.get("task_name", "").strip().lower() == task_name),
            None,
        )
        if not task:
            print("Task not found")
            return False
        if "tags" in task and tag_name in task["tags"]:
            task["tags"].remove(tag_name)
            task["updated_at"] = now_dubai()
            save_database(data_loader)
            print("Tag removed from task successfully")
            return True
        else:
            print("Tag not found in the specified task.")
            return False
    
    elif item_type == 2:
        habit_name = input("Habit name : ").strip().lower()
        habits = user.setdefault("habits", [])
        habit = next(
            (h for h in habits if h.get("habit_name", "").strip().lower() == habit_name),
            None,
        )
        if not habit:
            print("Habit not found")
            return False
        if "tags" in habit and tag_name in habit["tags"]:
            habit["tags"].remove(tag_name)
            habit["updated_at"] = now_dubai()
            save_database(data_loader)
            print("Tag removed from habit successfully")
            return True
        else:
            print("Tag not found in the specified habit.")
            return False
    
    elif item_type == 3:
        project_name = input("Project name : ").strip().lower()
        projects = user.setdefault("projects", [])
        project = next(
            (p for p in projects if p.get("project_title", "").strip().lower() == project_name),
            None,
        )
        if not project:
            print("Project not found")
            return False
        if "tags" in project and tag_name in project["tags"]:
            project["tags"].remove(tag_name)
            project["updated_at"] = now_dubai()
            save_database(data_loader)
            print("Tag removed from project successfully")
            return True
        else:
            print("Tag not found in the specified project.")
            return False
class ProductivityOverviewDashboard:
    def __init__(self,
        current_user : dict | None,
        data_loader : Callable[[], dict[str, Any]] = load_database,
        tz : str = "Asia/Dubai",
        ) -> None :
        self.current_user = ensure_current_user(current_user)
        self.data_loader = data_loader
        self.tz = ZoneInfo(tz)

    def _find_user(self) -> dict | None:
        if not self.current_user:
            return None
        data = self.data_loader()
        current_id = str(self.current_user.get("id"))
        user = next(
            (u for u in data.get("users", []) if str(u.get("id")) == str(current_id))
        ,None)

        if not user:
            print("User not found")
            logging.warning("User information was not found in DB")
            return None
        return user
    
    def task_metrics(self, tasks : list[dict[str, Any]]) -> dict[str, int]:
        today = datetime.now(self.tz).date()
        completed = 0
        pending = 0
        overdue = 0
        due_today = 0
        due_in_3 = 0
        due_in_7 = 0
        for task in tasks:
            status = task.get("status", "").lower()
            if status == "completed":
                completed += 1
            elif status == "pending":
                pending += 1

            raw_deadline = task.get("task_deadline")
            if not raw_deadline:
                continue

            try:
                deadline = datetime.fromisoformat(raw_deadline).date()
            except ValueError:
                try:
                    deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
                except ValueError:
                    continue

            delta_days = (deadline - today).days
            if deadline < today and status != "completed":
                overdue += 1
            if delta_days == 0:
                due_today += 1
            if 0 <= delta_days <= 3:
                due_in_3 += 1
            if 0 <= delta_days <= 7:
                due_in_7 += 1

        return {
            "total": len(tasks),
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "due_today": due_today,
            "due_in_3_days": due_in_3,
            "due_in_7_days": due_in_7,
        }
                
    def habits_metrics(self, habits : list[dict[str, Any]]) -> dict[str, int]:
        today = now_dubai()
        completed_today = 0
        missed_today = 0
        active_streaks = 0
        habits_at_risk = 0

        for habit in habits:
            if habit.get("completed_at", "") == today:
                completed_today += 1
            elif habit.get("completed_at", "") != today:
                missed_today += 1 
        for habit in habits:
            if habit.get("streaks", ""):
                active_streaks += 1
        for habit in habits:
            if is_due_within_days(habit, 1):
                habits_at_risk += 1
        return {
            "total": len(habits),
            "completed_today": completed_today,
            "missed_today": missed_today,
            "active_streaks": active_streaks,
            "at_risk": habits_at_risk,
        }

    def projects_metrics(self, projects : list[dict[str, Any]]) -> dict[str, int]:
        today = datetime.now(self.tz).date()
        is_active = 0
        is_completed = 0
        is_on_hold = 0
        is_overdue = 0
        pending = 0

        for project in projects:
            status = (project.get("status", "") or project.get("status ", "")).lower()
            if status == "active":
                is_active += 1
                pending += 1
            elif status == "completed":
                is_completed += 1
            elif status == "on hold":
                is_on_hold += 1
                pending += 1

            raw_deadline = project.get("project_deadline")
            if not raw_deadline:
                continue
            try:
                deadline = datetime.fromisoformat(raw_deadline).date()
            except ValueError:
                try:
                    deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
                except ValueError:
                    continue
            if deadline < today and status != "completed":
                is_overdue += 1

        return {
            "total": len(projects),
            "active": is_active,
            "completed": is_completed,
            "on_hold": is_on_hold,
            "pending": pending,
            "overdue": is_overdue,
        }


    def render_user_information(self):
        user = self._find_user()
        if not user:
            print("User not found")
            return False
        
        tasks = user.setdefault("tasks", [])
        habits = user.setdefault("habits", [])
        projects = user.setdefault("projects", [])

        task_metrics = self.task_metrics(tasks)
        habit_metrics = self.habits_metrics(habits)
        project_metrics = self.projects_metrics(projects)

        print("\n=== Productivity Overview ===")
        print(f"\nTasks : total={task_metrics['total']} completed={task_metrics['completed']} pending={task_metrics['pending']}")
        print(f"\noverdue : {task_metrics['overdue']} due_today={task_metrics['due_today']} due_3d={task_metrics['due_in_3_days']} due_7d={task_metrics['due_in_7_days']}")
        print(f"\nHabits : total={habit_metrics['total']} completed_today={habit_metrics['completed_today']}")
        print(f"\nProjects : total={project_metrics['total']} completed={project_metrics['completed']} pending={project_metrics['pending']}")
        return True



def tag_dashboard(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return    
    while True:
        print("\n===Tags===")
        print("\n1. Create Tag")
        print("\n2. View Tag")
        print("\n3. Edit Tag")
        print("\n4. Delete tag")
        print("\n5. Attach Tag to Item")
        print("\n6. Remove Tag to Item")
        print("\n7. Filter by Tag")
        print("\n8. Back to main menu")
        try:
            menu_choice = int(input("\nSelect option : ").strip())
        except ValueError:
            print("Enter a valid number")
            continue
        if menu_choice == 1:
            create_tag(current_user)
        if menu_choice == 2:
            view_tag(current_user)
        if menu_choice == 3:
            edit_tag(current_user)
        if menu_choice == 4:
            delete_tag(current_user)
        if menu_choice == 5:
            attach_tag_to_item(current_user)
        if menu_choice == 6:
            pass
        if menu_choice == 7:
            pass
        if menu_choice == 8:
            pass


def app_settings(current_user):
    print("\n===Settings===")
    print("1. Change password")
    print("2. Delete account")
    print("3. View archive")
    print("4. Export data")
    print("5. Clear data")
    print("6. Go back to main menu")
    print("7. Exit MyLife")
    user_request = int(input())
    if user_request == 1:
        change_password(current_user)
    elif user_request == 2:
        delete_account(current_user)
    elif user_request == 3:
        archive_dashboard(current_user)
    elif user_request == 4:
        pass
    elif user_request == 5:
        pass
    elif user_request == 6:
        pass
    elif user_request == 7:
        pass


def task_dashboard(current_user):
    print("\n===Tasks===")
    print("\n1. Search Tasks")
    print("\n2. Create task")
    print("\n3. View tasks")
    print("\n4. Update task")
    print("\n5. Mark task as done")
    print("\n6. Delete task")
    print("\n7. Go back to main menu")
    user_request = int(input())
    if user_request == 1:
        search_engine.search_tasks_engine(current_user)
    elif user_request == 2:
        record_task(current_user)
    elif user_request == 3:
        show_tasks(current_user)
    elif user_request == 4:
        update_task(current_user)
    elif user_request == 5:
        mark_task_as_complete(current_user)
    elif user_request == 6:
        remove_task(current_user)
    elif user_request == 7:
        app_dashboard(current_user)


def projects_dashboard(current_user):
    print("\n===Projects===")
    print("\n1. Search projects")
    print("\n2. Create Project")
    print("\n3. View Projects")
    print("\n4. Update Project")
    print("\n5. Delete Project")
    print("\n6. Go back to main menu")
    user_request = int(input())
    if user_request == 1:
        search_engine.search_projects_engine(current_user)
    elif user_request == 2:
        record_project(current_user)
    elif user_request == 3:
        view_projects(current_user)
    elif user_request == 4:
        update_project_task(current_user)
    elif user_request == 5:
        delete_project(current_user)
    elif user_request == 6:
        app_dashboard(current_user)
    else:
        print("Enter a valid number")

def habits_dashboard(current_user):
    print("\n===Habits===")
    print("\n1. Search Habits")
    print("\n2. Create Habit")
    print("\n3. Mark Habit")
    print("\n4. View Habits")
    print("\n5. Update Habit")
    print("\n6. Delete Habits")
    user_request = int(input())
    if user_request == 1:
        search_engine.search_habits_engine(current_user)
    elif user_request == 2:
        create_habit(current_user)
    elif user_request == 3:
        show_habits(current_user)
    elif user_request == 4:
        update_habit(current_user)
    elif user_request == 5:
        delete_habit(current_user)

def app_dashboard(current_user : dict | None):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return
    print(f"\nWelcome {current_user['username']} ")
    print("\n1. MyOverview")
    print("\n2. MyTasks")
    print("\n3. MyProjects")
    print("\n4. MyHabits")
    print("\n5. MyCalendar")
    print("\n6. MyFitness")
    print("\n7. MyFinance")    
    print("\n8. MyArchive")
    print("\n9. Settings") 
    print("\n10. Tags")  
    print("\n11. Log out")
    user_request = int(input())
    if user_request == 1:
        ProductivityOverviewDashboard(current_user).render_user_information()
    elif user_request == 2:
        task_dashboard(current_user)
    elif user_request == 3:
        projects_dashboard(current_user)
    elif user_request == 4:
        habits_dashboard(current_user)
    elif user_request == 5:
        print("Calendar tracking coming soon")
    elif user_request == 6:
        print("Fitness management coming soon")
        app_dashboard(current_user)
    elif user_request == 7:
        print("Finance management coming soon")
    elif user_request == 8:
        archive_dashboard(current_user)
    elif user_request == 9:
        app_settings(current_user)
    elif user_request == 10:
        tag_dashboard(current_user)
    elif user_request == 11:
        exit_app(current_user)

def app_UI():
    logger.info("App UI launched.")
    print("\n===MyLife===")
    print("\n1. Sign Up")
    print("\n2. Log In")
    print("\n3. Exit")
    user_choice = int(input())
    if user_choice == 1:
        user = user_create_account()
        if user:
            app_dashboard(user)
    elif user_choice == 2:
        user, token = user_login()
        if user:
            app_dashboard(user)
    elif user_choice == 3:
        exit_app()

def display_tag_color():
    print("\n1. Black")
    print("\n2. White")
    print("\n3. Blue")
    print("\n4. Red")
    print("\n5. Purple")
    print("\n6. yellow")
    print("\n7. Green")

def get_items():
    print("\n1. Tasks")
    print("\n2. Habits")
    print("\n3. Projects")

if __name__ == "__main__":
    app_UI()

#Features to add
#1 Deadline system (Done)
#2 Dashboard system (Done)
#3 Search system (Done)
#4 Tag System (done)
#5 Archive system  (Done)
#6 Session management system (Not started)
#7 Activity log system (Not started)
#8 Recurring task system (Not started)
#9 Data validation system (Not Started)
#10 Export data (Not Started)
#11 Nested project system (e.g Tasks inside projects) (Not started)
#12 Priority System (Not started)
#13 Add a settings system (Not started)
#14 Time task system that gives the user a time limit to complete the task e.g a task for one day (Not started)
#15 Add a feature to change user password (Done)
#16 Add a feature to delete user account (Done)
#16 Add a feature  to export user data(Not started)


#Finance System Logic
#1. Income tracker 
#2. Expense tracker
#3. category system
#4. Nested search engine
#5. Date System
#6 Settings system
#7 Investment tracker system
#8 Fund system

#Fitness System Logic
#1. Calaorie Tracker
#2. Food Category system
#3. Food tracker system
#4. Nested search engine system
#5. Date System
#6 Event System
#6 Settings system

#Database will be switched from json to postgres or SQlite 
