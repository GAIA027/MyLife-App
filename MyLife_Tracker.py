# To-DO App allows users to manage their tasks effectively. It provides functionalities to add, view, update, and delete tasks. The app also supports categorizing tasks and setting deadlines.
import re
import hashlib
import random
import string
from wonderwords import RandomWord
import json
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
import time
import asyncio
from dataclasses import dataclass, field

DXB_TZ = ZoneInfo("Asia/Dubai")
DXB_now = datetime.now(DXB_TZ)
print(DXB_now.isoformat(timespec="seconds"))

def now_dubai():
    return datetime.now(ZoneInfo("Asia/Dubai")).isoformat(timespec="seconds")

def app_UI():
    print("\n===MyLife===")
    print("1. Sign Up")
    print("2. Log In")
    print("3. Exit")
    user_choice = int(input())
    if user_choice == 1:
        user = user_create_account()
        if user:
            app_dashboard(user)
    elif user_choice == 2:
        user = user_login()
        if user:
            app_dashboard(user)
    elif user_choice == 3:
        exit_app()

def user_special_key():
    r = RandomWord
    special_key = r.word(word_min_length=5,word_max_length=5)
    return special_key

def hash_password(password : str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(input_password : str, stored_password: str) -> bool:
    return hash_password(input_password) == stored_password

database_file = Path(__file__).with_name("MyLife_database_file.json")

def load_database():
    with open(database_file, "r") as file:
        return json.load(file)
    
def save_database(data):
    with open(database_file, "w") as file:
        json.dump(data, file, indent=4)

def find_user(username):
    data = save_database()
    
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

    print("\n===Signup===")
    username = input("username : ").strip().lower()
    email = input("Email : ").strip().lower()
    password = input("Password : ")

    for user in data["users"]:
        if user["email"] == email:
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
        "archived_projects_log" : []
    }
    data["users"].append(new_user)
    save_database(data)
    print(f"Signup successful. Saved to: {database_file}")
    return new_user

def user_login():
    print("\n===Log-in===")
    data = load_database()

    email_or_username = input("Email or Username : ").strip().lower()
    for user in data["users"]:
        if user["email"] == email_or_username or user["username"] == email_or_username:
            user_password_attempt_left = 3
            while user_password_attempt_left > 0:
                password = input("Password : ")
                if verify_password(password, user["password"]):
                    time.sleep(3)
                    print("\nLogin Successful. Welcome tp MyLife")
                    return user
                else:
                    user_password_attempt_left -= 1
                    print(f"Incorrect password. You have {user_password_attempt_left} attempts left.")
            print("User not found. Please check your email/username and try again.")


def app_dashboard(current_user):
    print("\n===MyLife===")
    print("1. MyTasks")
    print("2. MyProjects")
    print("3. MyHabits")
    print("4. MyCalendar")
    print("5. MyFitness")
    print("6. MyFinance")       
    print("7. Log out")
    user_request = int(input())
    if user_request == 1:
        task_dashboard(current_user)
    elif user_request == 2:
        projects_dashboard(current_user)
    elif user_request == 3:
        habits_dashboard(current_user)
    elif user_request == 4:
        print("Calendar coming soon")
    elif user_request == 5:
        print("Fitness tracking coming soon")
    elif user_request == 6:
        print("Finance management coming soon")
        app_dashboard()
    elif user_request == 7:
        print("Logged out successfully")
        app_UI()

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
    data = load_database()
    if current_user is None:
        print("please login first")
        current_user = user_login()
        if not current_user:
            return

    for user in data.get("users", []):
        if str(user.get("id")) != str(current_user.get("id")):
            continue

        tasks = user.get("tasks", [])
        if not tasks:
            print("No tasks found for this user.")
        else:
            print("\n===Tasks===")
            for task in tasks:
                print(
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

    print("Current user not found.")

def remove_task(current_user):
    if current_user == None:
        user_login()

    data = load_database()
    delete_request = input("Enter the title of the task you want to delete: ")
    for task in data["tasks"]:
        if task["task_name"] == delete_request:
            data["tasks"].remove(task)
            save_database(data)
            print("Task deleted successfully!")
            if input("Main menu  Yes/No: ").strip().lower() == "yes":
                app_dashboard()
    print("Task not found! Please check the title and try again.")

task_main = task()


def record_task(current_user):
    data = load_database()
    if not current_user:
        print("Please log in first.")
        user_login()
        return

    task_title = input("Task title: ").strip()
    task_description = input("Description: ").strip()
    task_type = input("Task type: ").strip()
    created_at = input("Created at: ").strip()
    task_deadline = input("Task deadline: MM/DD/YYYY ").strip()
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
            print(f"\n===Task Recorded Successfully. Saved to {database_file}===")
            app_dashboard(current_user)
            return

    print("Current user not found in database.")


def update_task():
    data = load_database()
    task_title = input("Enter the title of the task you want to update: ")
    for task in task_main.tasks:
        if task["task_name"] == task_title:
            print("Task found! Enter the new details:")
            task_title = input("New task title: ")
            task_description = input("New description: ")
            task_type = input("New task type: ")
            created_at = input("Updated at: MM/DD/YYYY ")
            task_deadline = input("Task deadline: MM/DD/YYYY")
            task_notes = input("New task notes: ")
            task.update({
                "task_name" : task_title,
                "task_type": task_type,
                "task_description": task_description,
                "create_at": created_at,
                "task_deadaline": task_deadline,
                "task_notes": task_notes
            })
            task["updated_at"] = now_dubai()
            save_database(data)
            print("Task updated successfully!")
            app_dashboard()
            return
    print("Task not found! Please check the title and try again.")

def mark_task_as_complete(current_user):
    if not current_user:
        print("Please log in first")
        current_user = user_login()
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
            

def habits_dashboard(current_user):
    print("\n===Habits===")
    print("1. Create Habit")
    print("2. Mark Habit")
    print("3. View Habits")
    print("4. Update Habit")
    print("5. Delete Habits")
    user_request = int(input())
    if user_request == 1:
        create_habit(current_user)
    elif user_request == 2:
        mark_habit_as_complete(current_user)
    elif user_request == 3:
        show_habits(current_user)
    elif user_request == 4:
        update_habit(current_user)
    elif user_request == 5:
        delete_habit(current_user)
        
def create_habit(current_user):
    if not current_user:
        print("Please login first")
        user_login()
        return
    data = load_database()
    habit_name = input("Habit name: ").lower()
    habit_description = input("Description: ").strip()
    habit_frequency = input("Habit frequency (e.g., daily, weekly): ").strip()
    habit_start_date = input("Start date (MM/DD/YYYY): ").strip()
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
            print("\n===Habit Created successfully")
            app_dashboard(current_user)

def update_habit(current_user):
    if not current_user:
        print("please login first")
        user_login()
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
    data = load_database()
    if current_user is None:
        print("Please login first")
        current_user = user_login()
        if not current_user:
            return
        
    for user in data.get("tasks", []):
        if str(user.get("id")) == str(current_user.get("id")):
            continue
            
        habits = user.get("habits", [])
        if not habits:
            print("No habits found for this user")
        else:
            print("\n===Habits===")
            for habit in habits:
                print(
                    f"- {habit.get("habit_name", "untitled" )}"
                    f"[{habit.get("status", "pending")}]"
                    f"(deadline : {habit.get("habit_deadline", "N/A")})"
                    f"\n Description: {habit.get("habit_description", "")}"
                    f"\n Notes: {habit.get("habit_notes", '')}"
                    f"\n Created at: {habit.get("created_at", '')}"
                    f"\n Updated at: {habit.get("updated_at", '')}"
                )
        if input("Main menu Yes/No?: ").strip().lower():
            app_dashboard(current_user)
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
    if not current_user:
        print("Please log in first")
        user_login()
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
                    app_dashboard()
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
            app_dashboard()

project_main = project()

def record_project(current_user):
    if not current_user:
        print("Please login first")
        user_login()
        return
    data = load_database()
    project_title = input("Project title: ").strip().lower()
    project_description = input("Description: ").strip()
    project_duration = int(input("Project duration in days: "))
    project_created_at = input("Created at: ").strip()
    project_notes = input("Project notes: ").strip()

    for user in data.get("users", []):
        if str(user.get("id")) == str(current_user.get("id")):
            user.setdefault("projects", []).append({
                "project_title" : project_title,
                "project_description" : project_description,
                "project_duration" : project_duration,
                "project_created_at" : project_created_at,
                "project_notes" : project_notes,
                "created_at" : now_dubai(),
                "updated_at " : now_dubai(),
                "status" : "pending",
                "completed_at" : None
            })
            save_database(data)
            print("Project created successfully")
            app_dashboard(current_user)
    

def view_projects(project_main):
    print(project_main.show_projects())
    if input("Main menu  Yes/No: ").strip().lower() == "yes":
        app_dashboard()
    

def update_project_task():
    project_update_request = input("Project title : ")
    for project in project_main.projects:
        if project["project_title"] == project_update_request:
            print("Project found! Enter new details")
            project_title = input("New project title: ")
            project_description = input("New description: ")
            project_duration = input("Project duration: ")
            project_created_at = input("Created at: ")
            project_notes = input("project notes: ")
            project.update({
                "project_title" : project_title,
                "project_description" : project_description,
                "project_duration" : project_duration,
                "project_created_at" : project_created_at,
                "project_notes" : project_notes
            })
            project["updated at"] = now_dubai()
            print("Project updated successfully!")
            app_dashboard()

def delete_project():
    project_delete_request = input("Enter the title of the project you want to delete: ")
    for project in project_main.projects:
        if project["project_title"] == project_delete_request:
            project_main.delete_project(project_delete_request)
            print("Project deleted successfully!")
            if input("Main menu  Yes/No: ").strip().lower() == "yes":
                app_dashboard()
    print("Project not found! Please check the title and try again.")

def mark_project_as_complete(current_user):
    if not current_user:
        print("Please log in first.")
        current_user = user_login()
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

def projects_dashboard():
    print("\n===Projects===")
    print("1. Create Project")
    print("2. View Projects")
    print("3. Update Project")
    print("4. Delete Project")
    print("Go back to main menu")
    user_request = int(input())
    if user_request == 1:
        record_project(project_main)
    elif user_request == 2:
        view_projects(project_main)
    elif user_request == 3:
        update_project_task()
    elif user_request == 4:
        delete_project()
    elif user_request == 5:
        app_dashboard()
    else:
        print("Enter a valid number")

def exit_app():
    user_exit_request = input("\nExit MyLife")
    if user_exit_request == "Yes":
        print("Exited!")
    elif user_exit_request == "No":
        app_dashboard()

def user_register_text():
    register_request = input("Do you have an account?   yes/no").strip().lower()
    if register_request == "yes":
        user_login()
    elif register_request == "no":
        user_create_account()


def task_dashboard(current_user):
    print("\n===Tasks===")
    print("1. Create task")
    print("2. View tasks")
    print("3. Update task")
    print("4. Mark task as done")
    print("5. Delete task")
    print("6. Go back to main menu")
    user_request = int(input())
    if user_request == 1:
        record_task(current_user)
    elif user_request == 2:
        show_tasks(current_user)
    elif user_request == 3:
        update_task(current_user)
    elif user_request == 4:
        mark_task_as_complete(current_user)
    elif user_request == 5:
        remove_task(current_user)
    elif user_request == 6:
        app_dashboard(current_user)

def set_priority(task_id, cureent_user):
    data = load_database()

    for user in data.get("users"):
        if str(user.get("id")) == str(cureent_user.get("id")):
            tasks = user.setdefault("tasks", [])

            for task in tasks:
                if task["id"] == task_id:
                    priority = int(input("priority level\n1 - very low\n2 - low\n3 - Medium\n4 - high\n5 - Very high"))
                    if 1 <= priority <= 5:
                        tasks["priority"] = priority
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
        if current_user is None:
            print("Please login first")
            current_user = user_login()
            return
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

                        habit.pop(i)
                        save_database(data)
                        return True
        return False

    def archive_tasks(self, current_user, task_name):
        if current_user is None:
            print("please login first")
            current_user = user_login()
            return
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

                        task.pop(i)
                        save_database(data)
                        return True
        return False

    def archive_projects(self,current_user, project_title):
        if not current_user:
            print("Please login first")
            current_user = user_login()
            return
        
        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                projects = user.setdefault("projects", [])

                for i, project in enumerate(projects):
                    if project.get("project_title", "").strip().lower() == project_title.strip().lower():
                        archive_entry = project.copy
                        archive_entry["archive_id"] = generate_id()
                        archive_entry["archived_at"] = now_dubai()
                        self.archived_projects_log.append(archive_entry)

                        project.pop(i)
                        save_database(data)
                        return True
        return False

    def save_archive(self,):
        pass

    def load_archive(self,):
        pass

    def view_archive(self):
        pass

app_UI()



#Features to add
#1 Deadline system
#2 Dashboard system
#3 Search system
#4 Tag System
#5 Archive system  (In the proccess)
#6 Session management system
#7 Activity log system
#8 Recurring task system
#9 Data validation system
#10 Export system
#11 Nested project system (e.g Tasks inside projects)
#12 Priority System 


#Finance System Logic
#1. Income tracker 
#2. Expense tracker
#3. category system
#4. Nested search engine
#5. Date System

#Fitness System Logic
#1. Calaorie Tracker
#2. Food Category system
#3. Food tracker system
#4. Nested search engine system
#5. Date System
#6 Event System

#Database will be swqwitched from json to postgres or SQlite 