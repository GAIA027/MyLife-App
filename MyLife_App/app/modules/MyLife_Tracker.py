import calendar
import hashlib
import hmac
import json
import logging
import os
import random
import re
import secrets
import string
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import jwt
from wonderwords import RandomWord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("mylife_tracker")

JWT_SECRET = os.getenv("SECRET_KEY")
if not JWT_SECRET:
    JWT_SECRET = secrets.token_urlsafe(32)
    logger.warning("SECRET_KEY is not set. Using an ephemeral JWT secret for this process.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60
DXB_TZ = ZoneInfo("Asia/Dubai")


def validate_date_input(date_text: str) -> bool:
    try:
        datetime.strptime(date_text.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def add_months(value: datetime, months: int) -> datetime:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return value.replace(year=year, month=month, day=min(value.day, last_day))


def calculate_next_due(due_iso: str, rule: dict) -> str:
    try:
        due = datetime.fromisoformat(due_iso)
    except ValueError:
        due = datetime.strptime(due_iso, "%Y-%m-%d %H:%M")

    interval = int(rule.get("interval", 1))
    frequency = (rule.get("frequency") or rule.get("freq") or "").lower()

    if frequency == "daily":
        next_due = due + timedelta(days=interval)
    elif frequency == "weekly":
        next_due = due + timedelta(weeks=interval)
    elif frequency == "monthly":
        next_due = add_months(due, interval)
    else:
        raise ValueError("Unsupported frequency (use daily/weekly/monthly)")

    return next_due.isoformat(timespec="seconds")


def is_due_within_days(task_item: dict, days: int, tz: str = "Asia/Dubai") -> bool:
    raw_deadline = task_item.get("task_deadline")
    if not raw_deadline:
        return False

    try:
        deadline = datetime.fromisoformat(raw_deadline).date()
    except ValueError:
        deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()

    today = datetime.now(ZoneInfo(tz)).date()
    delta_days = (deadline - today).days
    return 0 <= delta_days <= days


def create_access_token(user: dict) -> str:
    now = datetime.now(DXB_TZ)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_current_user_from_token(token: str) -> dict | None:
    try:
        claims = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        logger.warning("Session expired while decoding JWT.")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token received.")
        return None

    data = load_database()
    user_id = claims.get("sub")
    current_user = next((u for u in data.get("users", []) if str(u.get("id")) == str(user_id)), None)
    if current_user:
        logger.info("User resolved from token for user_id=%s", user_id)
    else:
        logger.warning("Token decoded but user not found for user_id=%s", user_id)
    return current_user


def now_dubai() -> str:
    return datetime.now(DXB_TZ).isoformat(timespec="seconds")


def validate_deadline_input(
    raw_deadline: str,
    timezone: ZoneInfo = DXB_TZ,
    allow_past: bool = False,
) -> tuple[str | None, str | None]:
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
    for fmt in accepted_formats:
        try:
            deadline_datetime = datetime.strptime(raw_deadline, fmt)
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


def user_special_key() -> str:
    return RandomWord().word(word_min_length=5, word_max_length=5)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return "pbkdf2_sha256$100000$%s$%s" % (
        urlsafe_b64encode(salt).decode(),
        urlsafe_b64encode(derived_key).decode(),
    )


def verify_password(input_password: str, stored_password: str) -> bool:
    if not stored_password:
        return False

    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, encoded_salt, encoded_hash = stored_password.split("$", 3)
            salt = urlsafe_b64decode(encoded_salt.encode())
            expected_hash = urlsafe_b64decode(encoded_hash.encode())
            candidate_hash = hashlib.pbkdf2_hmac(
                "sha256",
                input_password.encode(),
                salt,
                int(iterations),
            )
            return hmac.compare_digest(candidate_hash, expected_hash)
        except (ValueError, TypeError):
            logger.warning("Stored password hash is malformed.")
            return False

    legacy_hash = hashlib.sha256(input_password.encode()).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_password)


database_file = Path(__file__).resolve().parents[2] / "data" / "mylife.json"


def load_database() -> dict[str, Any]:
    try:
        with open(database_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.exception("Database file not found: %s", database_file)
        raise
    except json.JSONDecodeError:
        logger.exception("Database file is not valid JSON: %s", database_file)
        raise


def save_database(data: dict[str, Any]) -> None:
    try:
        with open(database_file, "w") as file:
            json.dump(data, file, indent=4)
    except OSError:
        logger.exception("Failed to write database file: %s", database_file)
        raise


def find_user(username: str) -> dict[str, Any] | None:
    data = load_database()
    for user in data.get("users", []):
        if user.get("username") == username:
            return user
    return None


def generate_id(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def validate_username(username: str) -> str | None:
    if len(username) < 5:
        return "username must be at least 5 charchters"
    return None


def validate_email(email: str) -> str | None:
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_pattern, email):
        return "Invalid email format"
    return None


def validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "password must be at least 8 characters"
    if not any(char.isupper() for char in password):
        return "password must contain at least one uppercase letter"
    if not any(char.islower() for char in password):
        return "password must contain at least one lowercase letter"
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one number"
    if not any(char in "!@#$%^&*()-_=+[{]}|;:'\",<.>/?`~" for char in password):
        return "Password must contain at least a special character"
    return None


def ensure_current_user(current_user: dict | None) -> dict | None:
    return current_user


class AccountService:
    def __init__(
        self,
        data_loader: Callable[[], dict[str, Any]] = load_database,
        data_saver: Callable[[dict[str, Any]], None] = save_database,
    ):
        self.data_loader = data_loader
        self.data_saver = data_saver

    def create_user(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        username = username.strip().lower()
        email = email.strip().lower()

        for validator in (validate_username(username), validate_email(email), validate_password(password)):
            if validator:
                raise ValueError(validator)

        data = self.data_loader()
        for user in data.get("users", []):
            if user.get("email") == email:
                raise ValueError("User already exists")
            if user.get("username") == username:
                raise ValueError("Username already exists")

        new_user = {
            "id": generate_id(),
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password": hash_password(password),
            "tasks": [],
            "projects": [],
            "habits": [],
            "finance": [],
            "fitness": [],
            "archived_tasks_log": [],
            "archived_habits_log": [],
            "archived_projects_log": [],
        }
        data.setdefault("users", []).append(new_user)
        self.data_saver(data)
        return new_user

    def authenticate_user(self, email_or_username: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
        identifier = email_or_username.strip().lower()
        data = self.data_loader()

        for user in data.get("users", []):
            if user.get("email") != identifier and user.get("username") != identifier:
                continue
            if not verify_password(password, user.get("password", "")):
                return None, None
            return user, create_access_token(user)
        return None, None

    def change_password(self, current_user: dict | None, current_password: str, new_password: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        validation_error = validate_password(new_password)
        if validation_error:
            raise ValueError(validation_error)

        data = self.data_loader()
        current_id = str(current_user.get("id"))
        for user in data.get("users", []):
            if str(user.get("id")) != current_id:
                continue
            if not verify_password(current_password, user.get("password", "")):
                return False
            if verify_password(new_password, user.get("password", "")):
                raise ValueError("Your new password cannot be your current password")
            user["password"] = hash_password(new_password)
            self.data_saver(data)
            return True
        return False

    def delete_account(self, current_user: dict | None, current_password: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = self.data_loader()
        users = data.get("users", [])
        current_id = str(current_user.get("id"))
        for index, user in enumerate(users):
            if str(user.get("id")) != current_id:
                continue
            if not verify_password(current_password, user.get("password", "")):
                return False
            users.pop(index)
            self.data_saver(data)
            return True
        return False


class task:
    def create_task(
        self,
        current_user: dict,
        task_name: str,
        task_type: str,
        task_description: str,
        created_at: str,
        task_deadline: str,
        task_notes: str,
        recurring: bool = False,
        rule: dict[str, Any] | None = None,
    ) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                user.setdefault("tasks", []).append(
                    {
                        "id": generate_id(),
                        "user_id": str(current_user.get("id")),
                        "task_name": task_name,
                        "task_type": task_type,
                        "task_description": task_description,
                        "created_at": created_at,
                        "task_deadline": task_deadline,
                        "task_notes": task_notes,
                        "updated_at": now_dubai(),
                        "status": "pending",
                        "completed_at": None,
                        "is_recurring": recurring,
                        "recurrence": rule,
                        "completion_log": [],
                    }
                )
                save_database(data)
                return True
        return False

    def view_tasks(self, current_user: dict) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                return user.get("tasks", [])
        return []

    def update_task(
        self,
        current_user: dict,
        user_update_request: str,
        updated_task_name: str,
        updated_task_description: str,
        updated_task_type: str,
        updated_task_deadline: str,
        updated_task_notes: str,
    ) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first."

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            for task_item in user.setdefault("tasks", []):
                if task_item.get("task_name") == user_update_request:
                    task_item.update(
                        {
                            "task_name": updated_task_name,
                            "task_type": updated_task_type,
                            "task_description": updated_task_description,
                            "task_deadline" : updated_task_deadline,
                            "task_notes": updated_task_notes,
                            "updated_at": now_dubai(),
                        }
                    )
                    save_database(data)
                    return "Task updated successfully!"
        return "Task not found! Please check the title and try again."

    def delete_task(self, current_user: dict, delete_request: str) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first."

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            tasks = user.setdefault("tasks", [])
            for task_item in tasks:
                if task_item.get("task_name") == delete_request:
                    tasks.remove(task_item)
                    save_database(data)
                    return "Task deleted successfully!"
        return "Task not found"

    def mark_task_as_complete(self, current_user: dict, task_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            tasks = user.setdefault("tasks", [])
            for task_item in tasks:
                if task_item.get("task_name", "").strip().lower() != task_name.strip().lower():
                    continue
                now = now_dubai()
                task_item.setdefault("completion_log", []).append(now)
                if task_item.get("is_recurring") and task_item.get("recurrence"):
                    task_item["task_deadline"] = calculate_next_due(task_item["task_deadline"], task_item["recurrence"])
                    task_item["status"] = "pending"
                    task_item["completed_at"] = None
                else:
                    task_item["status"] = "completed"
                    task_item["completed_at"] = now
                task_item["updated_at"] = now
                save_database(data)
                return True
        return False

    def set_priority(self, current_user: dict, task_id: str, priority: int) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            tasks = user.setdefault("tasks", [])
            for task_item in tasks:
                if str(task_item.get("id")) != str(task_id):
                    continue
                task_item["priority"] = priority
                task_item["updated_at"] = now_dubai()
                save_database(data)
                return True
        return False
        
task_main = task()


def update_habit_streak(habit: dict) -> bool:
    today = datetime.now(DXB_TZ).date()
    today_str = today.isoformat()
    last_completed = habit.get("last_completed_date")
    if last_completed == today_str:
        return False

    if last_completed:
        delta_days = (today - date.fromisoformat(last_completed)).days
        habit["streak"] = habit.get("streak", 0) + 1 if delta_days == 1 else 1
    else:
        habit["streak"] = 1

    habit["best_streak"] = max(habit.get("best_streak", 0), habit["streak"])
    habit["last_completed_date"] = today_str
    habit.setdefault("completion_log", []).append(today_str)
    return True


class HabitService:
    def create_habit(
        self,
        current_user: dict | None,
        habit_name: str,
        habit_description: str,
        habit_frequency: str,
        habit_start_date: str,
        habit_notes: str,
    ) -> dict[str, Any] | None:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            habit = {
                "user_id": str(current_user.get("id")),
                "habit_name": habit_name.strip().lower(),
                "habit_description": habit_description,
                "habit_frequency": habit_frequency,
                "habit_start_date": habit_start_date,
                "habit_notes": habit_notes,
                "completion_log": [],
                "streak": 0,
                "best_streak": 0,
                "last_completed_date": None,
                "created_at": now_dubai(),
                "updated_at": now_dubai(),
                "status": "pending",
                "completed_at": None,
            }
            user.setdefault("habits", []).append(habit)
            save_database(data)
            return habit
        return None

    def list_habits(self, current_user: dict | None) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                return user.get("habits", [])
        return []

    def update_habit(
        self,
        current_user: dict | None,
        updated_habit_name: str,
        updated_description: str | None = None,
        updated_frequency: str | None = None,
        updated_start_date: str | None = None,
        updated_notes: str | None = None,
    ) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            for habit in user.setdefault("habits", []):
                if habit.get("habit_name", "").strip().lower() != updated_habit_name.strip().lower():
                    continue
                habit.update(
                    {
                        "habit_description": updated_description or habit.get("habit_description", ""),
                        "habit_frequency": updated_frequency or habit.get("habit_frequency", ""),
                        "habit_start_date": updated_start_date or habit.get("habit_start_date", ""),
                        "habit_notes": updated_notes or habit.get("habit_notes", ""),
                        "updated_at": now_dubai(),
                    }
                )
                save_database(data)
                return True
        return False

    def mark_habit_as_complete(self, current_user: dict | None, habit_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        now = now_dubai()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            for habit in user.setdefault("habits", []):
                if habit.get("habit_name", "").strip().lower() != habit_name.strip().lower():
                    continue
                if not update_habit_streak(habit):
                    return False
                habit["status"] = "completed"
                habit["completed_at"] = now
                habit["updated_at"] = now
                save_database(data)
                return True
        return False

    def delete_habit(self, current_user: dict | None, habit_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            habits = user.setdefault("habits", [])
            for habit in habits:
                if habit.get("habit_name", "").strip().lower() == habit_name.strip().lower():
                    habits.remove(habit)
                    save_database(data)
                    return True
        return False


class project:
    def __init__(self) -> None:
        self.projects: list[dict[str, str | int]] = []

    def create_projects(
        self,
        current_user: dict,
        project_title: str,
        project_description: str,
        project_duration: int,
        project_created_at: str,
        project_deadline: str,
        project_notes: str,
    ) -> dict[str, str | int]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return {}

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                project_record = {
                    "user_id": str(current_user.get("id")),
                    "project_title": project_title,
                    "project_description": project_description,
                    "project_duration": project_duration,
                    "project_created_at": project_created_at,
                    "project_deadline": project_deadline,
                    "project_notes": project_notes,
                    "created_at": now_dubai(),
                    "updated_at": now_dubai(),
                    "status": "pending",
                    "completed_at": None,
                }
                user.setdefault("projects", []).append(project_record)
                save_database(data)
                return project_record
        return {}

    def show_projects(self, current_user: dict) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                return user.get("projects", [])
        return []

    def update_project(
        self,
        current_user: dict,
        project_update_request: str,
        project_title: str,
        project_description: str,
        project_deadline: str,
        project_notes: str,
    ) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first"

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            projects = user.setdefault("projects", [])
            for project_item in projects:
                if project_item.get("project_title") == project_update_request:
                    project_item.update(
                        {
                            "project_title": project_title,
                            "project_description": project_description,
                            "project_deadline": project_deadline,
                            "project_notes": project_notes,
                            "updated_at": now_dubai(),
                        }
                    )
                    save_database(data)
                    return "Project updated successfully"
        return "Project not found"

    def delete_project(self, current_user: dict, project_delete_request: str) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first"

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            projects = user.setdefault("projects", [])
            for project_item in projects:
                if project_item.get("project_title") == project_delete_request:
                    projects.remove(project_item)
                    save_database(data)
                    return "Project deleted successfully"
        return "Project not found"

    def mark_project_as_complete(self, current_user: dict, project_title: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            projects = user.setdefault("projects", [])
            for project_item in projects:
                if project_item.get("project_title", "").strip().lower() != project_title.strip().lower():
                    continue
                now = now_dubai()
                project_item["status"] = "completed"
                project_item["completed_at"] = now
                project_item["updated_at"] = now
                save_database(data)
                return True
        return False


project_main = project()


@dataclass
class ArchiveStore:
    archived_habits_log: list[dict] = field(default_factory=list)
    archived_tasks_log: list[dict] = field(default_factory=list)
    archived_projects_log: list[dict] = field(default_factory=list)

    def archive_habits(self, current_user: dict | None, habit_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            habits = user.setdefault("habits", [])
            for index, habit in enumerate(habits):
                if habit.get("habit_name", "").strip().lower() != habit_name.strip().lower():
                    continue
                archive_entry = habit.copy()
                archive_entry["archive_id"] = generate_id()
                archive_entry["archived_at"] = now_dubai()
                self.archived_habits_log.append(archive_entry)
                habits.pop(index)
                save_database(data)
                return True
        return False

    def archive_tasks(self, current_user: dict | None, task_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            tasks = user.setdefault("tasks", [])
            for index, task_item in enumerate(tasks):
                if task_item.get("task_name", "").strip().lower() != task_name.strip().lower():
                    continue
                archive_entry = task_item.copy()
                archive_entry["archive_id"] = generate_id()
                archive_entry["archived_at"] = now_dubai()
                self.archived_tasks_log.append(archive_entry)
                tasks.pop(index)
                save_database(data)
                return True
        return False

    def archive_projects(self, current_user: dict | None, project_title: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) != str(current_user.get("id")):
                continue
            projects = user.setdefault("projects", [])
            for index, project_item in enumerate(projects):
                if project_item.get("project_title", "").strip().lower() != project_title.strip().lower():
                    continue
                archive_entry = project_item.copy()
                archive_entry["archive_id"] = generate_id()
                archive_entry["archived_at"] = now_dubai()
                self.archived_projects_log.append(archive_entry)
                projects.pop(index)
                save_database(data)
                return True
        return False

    def save_archive(self, current_user: dict | None) -> tuple[bool, str]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False, "Please log in first"

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                user["archive"] = {
                    "archive_habits_log": self.archived_habits_log,
                    "archive_tasks_log": self.archived_tasks_log,
                    "archive_projects_log": self.archived_projects_log,
                }
                save_database(data)
                return True, "Saved"
        return False, "User not found"

    def load_archive(self, current_user: dict | None) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        data = load_database()
        for user in data.get("users", []):
            if str(user.get("id")) == str(current_user.get("id")):
                archived_data = user.get("archive", {})
                self.archived_habits_log = archived_data.get("archive_habits_log", [])
                self.archived_tasks_log = archived_data.get("archive_tasks_log", [])
                self.archived_projects_log = archived_data.get("archived_projects_log", [])
                return True
        return False

    def view_archive(self, current_user: dict | None) -> dict[str, Any] | None:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None

        if not self.load_archive(current_user):
            return None

        return {
            "archived_habits_log": self.archived_habits_log,
            "archived_tasks_log": self.archived_tasks_log,
            "archived_projects_log": self.archived_projects_log,
            "updated_at": now_dubai(),
        }


@dataclass(slots=True)
class Tracker_search_engine:
    data_loader: Callable[[], dict[str, Any]] = load_database

    @staticmethod
    def find_user(users: list[dict[str, Any]], current_user: dict) -> dict | None:
        current_id = str(current_user.get("id"))
        return next((user for user in users if str(user.get("id")) == str(current_id)), None)

    def search_collection(
        self,
        current_user: dict | None,
        collection_key: str,
        title_key: str,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user or not keyword:
            return []

        data = self.data_loader()
        user = self.find_user(data.get("users", []), current_user)
        if not user:
            return []

        normalized_keyword = keyword.strip().lower()
        if not normalized_keyword:
            return []

        items = user.get(collection_key, [])
        return [item for item in items if normalized_keyword in str(item.get(title_key, "")).lower()]

    def search_tasks_engine(self, current_user: dict | None, keyword: str | None = None) -> list[dict[str, Any]]:
        return self.search_collection(current_user, "tasks", "task_name", keyword)

    def search_habits_engine(self, current_user: dict | None, keyword: str | None = None) -> list[dict[str, Any]]:
        return self.search_collection(current_user, "habits", "habit_name", keyword)

    def search_projects_engine(self, current_user: dict | None, keyword: str | None = None) -> list[dict[str, Any]]:
        return self.search_collection(current_user, "projects", "project_title", keyword)


search_engine = Tracker_search_engine()


class ProductivityOverviewDashboard:
    def __init__(
        self,
        current_user: dict | None,
        data_loader: Callable[[], dict[str, Any]] = load_database,
        tz: str = "Asia/Dubai",
    ) -> None:
        self.current_user = ensure_current_user(current_user)
        self.data_loader = data_loader
        self.tz = ZoneInfo(tz)

    def _find_user(self) -> dict | None:
        if not self.current_user:
            return None
        data = self.data_loader()
        current_id = str(self.current_user.get("id"))
        return next((u for u in data.get("users", []) if str(u.get("id")) == str(current_id)), None)

    def task_metrics(self, tasks: list[dict[str, Any]]) -> dict[str, int]:
        today = datetime.now(self.tz).date()
        completed = 0
        pending = 0
        overdue = 0
        due_today = 0
        due_in_3 = 0
        due_in_7 = 0

        for task_item in tasks:
            status = task_item.get("status", "").lower()
            if status == "completed":
                completed += 1
            elif status == "pending":
                pending += 1

            raw_deadline = task_item.get("task_deadline")
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

    def habits_metrics(self, habits: list[dict[str, Any]]) -> dict[str, int]:
        today = now_dubai().split("T")[0]
        completed_today = 0
        missed_today = 0
        active_streaks = 0
        habits_at_risk = 0

        for habit in habits:
            completed_at = str(habit.get("completed_at", "")).split("T")[0]
            if completed_at == today:
                completed_today += 1
            else:
                missed_today += 1
            if habit.get("streak", 0):
                active_streaks += 1
            if is_due_within_days(habit, 1):
                habits_at_risk += 1

        return {
            "total": len(habits),
            "completed_today": completed_today,
            "missed_today": missed_today,
            "active_streaks": active_streaks,
            "at_risk": habits_at_risk,
        }

    def projects_metrics(self, projects: list[dict[str, Any]]) -> dict[str, int]:
        today = datetime.now(self.tz).date()
        is_active = 0
        is_completed = 0
        is_on_hold = 0
        is_overdue = 0
        pending = 0

        for project_item in projects:
            status = (project_item.get("status", "") or project_item.get("status ", "")).lower()
            if status == "active":
                is_active += 1
                pending += 1
            elif status == "completed":
                is_completed += 1
            elif status == "on hold":
                is_on_hold += 1
                pending += 1

            raw_deadline = project_item.get("project_deadline")
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

    def render_user_information(self) -> dict[str, Any] | None:
        user = self._find_user()
        if not user:
            return None

        return {
            "tasks": self.task_metrics(user.setdefault("tasks", [])),
            "habits": self.habits_metrics(user.setdefault("habits", [])),
            "projects": self.projects_metrics(user.setdefault("projects", [])),
        }
