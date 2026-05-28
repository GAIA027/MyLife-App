import calendar
import hashlib
import hmac
import logging
import os
import random
import re
import secrets
import string
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.database.models import (
    Habit as HabitModel,
    Project as ProjectModel,
    Task as TaskModel,
    User as UserModel,
)

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


def get_current_user_from_token(token: str, db: Session) -> dict | None:
    try:
        claims = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        logger.warning("Session expired while decoding JWT.")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token received.")
        return None

    user_id = claims.get("sub")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        logger.warning("Token decoded but user not found for user_id=%s", user_id)
        return None

    logger.info("User resolved from token for user_id=%s", user_id)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


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
    today = datetime.now(timezone).date()
    if not allow_past and deadline_datetime.date() < today:
        return None, "Deadline cannot be in the past."

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


def _task_to_dict(t: TaskModel) -> dict[str, Any]:
    return {
        "id": t.id,
        "user_id": t.user_id,
        "task_name": t.task_name,
        "task_type": t.task_type,
        "task_description": t.task_description or "",
        "task_deadline": t.task_deadline or "",
        "task_notes": t.task_notes or "",
        "status": t.status or "pending",
        "priority": t.priority,
        "is_recurring": t.is_recurring,
        "recurrence": t.recurrence,
        "completion_log": t.completion_log or [],
        "completed_at": t.completed_at,
        "is_archived": t.is_archived,
        "created_at": t.created_at or "",
        "updated_at": t.updated_at or "",
    }


def _habit_to_dict(h: HabitModel) -> dict[str, Any]:
    today_str = datetime.now(DXB_TZ).date().isoformat()
    return {
        "id": h.id,
        "user_id": h.user_id,
        "habit_name": h.habit_name,
        "today_count": sum(1 for e in (h.completion_log or []) if e == today_str),
        "habit_description": h.habit_description or "",
        "habit_frequency": h.habit_frequency or "",
        "habit_start_date": h.habit_start_date or "",
        "habit_notes": h.habit_notes or "",
        "completion_log": h.completion_log or [],
        "streak": h.streak or 0,
        "best_streak": h.best_streak or 0,
        "last_completed_date": h.last_completed_date,
        "status": h.status or "pending",
        "completed_at": h.completed_at,
        "is_archived": h.is_archived,
        "created_at": h.created_at or "",
        "updated_at": h.updated_at or "",
    }


def _project_to_dict(p: ProjectModel) -> dict[str, Any]:
    return {
        "id": p.id,
        "user_id": p.user_id,
        "project_title": p.project_title,
        "project_description": p.project_description or "",
        "project_duration": p.project_duration or 0,
        "project_deadline": p.project_deadline or "",
        "project_notes": p.project_notes or "",
        "status": p.status or "pending",
        "completed_at": p.completed_at,
        "is_archived": p.is_archived,
        "created_at": p.created_at or "",
        "updated_at": p.updated_at or "",
    }



class AccountService:
    def __init__(self, db: Session):
        self.db = db

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

        for error in (
            validate_username(username),
            validate_email(email),
            validate_password(password),
        ):
            if error:
                raise ValueError(error)

        if self.db.query(UserModel).filter(UserModel.email == email).first():
            raise ValueError("User already exists")

        if self.db.query(UserModel).filter(UserModel.username == username).first():
            raise ValueError("Username already taken")

        new_user = UserModel(
            id=generate_id(),
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }

    def authenticate_user(self, email_or_username: str, password: str):
        identifier = email_or_username.strip().lower()
        user = self.db.query(UserModel).filter(
            (UserModel.email == identifier) | (UserModel.username == identifier)
        ).first()
        if not user:
            return None, None

        if not verify_password(password, user.password_hash):
            return None, None

        token = create_access_token({"id": user.id, "username": user.username})
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }, token

    def change_password(
        self,
        current_user: dict | None,
        current_password: str,
        new_password: str,
    ) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        validation_error = validate_password(new_password)
        if validation_error:
            raise ValueError(validation_error)

        user = self.db.query(UserModel).filter(
            UserModel.id == str(current_user.get("id"))
        ).first()
        if not user:
            return False

        if not verify_password(current_password, user.password_hash):
            return False

        if verify_password(new_password, user.password_hash):
            raise ValueError("Your new password cannot be your current password")

        user.password_hash = hash_password(new_password)
        self.db.commit()
        return True

    def delete_account(self, current_user: dict | None, current_password: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        user = self.db.query(UserModel).filter(UserModel.id == str(current_user.get("id")) ).first()
        if not user:
            return False

        if not verify_password(current_password, user.password_hash):
            return False

        self.db.delete(user)
        self.db.commit()
        return True
    
    def reset_password(self, email_or_username: str, new_password: str) -> None:
        user = (
            self.db.query(UserModel)
            .filter(
                (UserModel.email == email_or_username) |
                (UserModel.username == email_or_username)
            )
            .first()
        )
        if not user:
            raise ValueError("No account found with that email or username.")
        error = validate_password(new_password)
        if error:
            raise ValueError(error)
        user.password_hash = hash_password(new_password)
        self.db.commit()

    def change_password(self, current_user, current_password : str, new_password : str) -> str:
        u_id = str(current_user.get("id"))
        user_record = self.db.query(UserModel).filter(
            UserModel.id == u_id
        ).first()

        if not user_record:
            return "User not found"
        
        if not verify_password(current_password, new_password):
            return "Current_password is incorrect"
        
        password_error = validate_password(new_password)
        if password_error:
            return password_error
        
        user_record.password_hash = hash_password(new_password)
        self.db.commit()
        return "ok"


class task:
    def __init__(self, db: Session) -> None:
        self.db = db

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

        new_task = TaskModel(
            id=generate_id(),
            user_id=str(current_user.get("id")),
            task_name=task_name,
            task_type=task_type,
            task_description=task_description,
            created_at=created_at,
            task_deadline=task_deadline,
            task_notes=task_notes,
            updated_at=now_dubai(),
            status="pending",
            completed_at=None,
            is_recurring=recurring,
            recurrence=rule,
            completion_log=[],
            is_archived=False,
        )
        self.db.add(new_task)
        self.db.commit()
        return True

    def view_tasks(self, current_user: dict) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        tasks = (self.db.query(TaskModel) .filter(TaskModel.user_id == str(current_user.get("id")),
                TaskModel.is_archived.is_(False),
                  )
            .all()
        )
        return [_task_to_dict(t) for t in tasks]

    def update_task(
        self,
        current_user: dict,
        user_update_request: str,
        updated_task_name: str,
        updated_task_description: str,
        updated_task_type: str,
        updated_task_deadline: str,
        updated_task_notes: str,
        recurring: bool = False,
        recurrence_rule: dict | None = None,
    ) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first."

        task_record = (
            self.db.query(TaskModel)
            .filter(
                TaskModel.user_id == str(current_user.get("id")),
                TaskModel.task_name == user_update_request,
            )
            .first()
        )
        if not task_record:
            return "Task not found! Please check the title and try again."

        task_record.task_name = updated_task_name
        task_record.task_type = updated_task_type
        task_record.task_description = updated_task_description
        task_record.task_deadline = updated_task_deadline
        task_record.task_notes = updated_task_notes
        task_record.is_recurring = recurring
        task_record.recurrence = recurrence_rule if recurring else None
        task_record.updated_at = now_dubai()
        self.db.commit()
        return "Task updated successfully!"

    def delete_task(self, current_user: dict, delete_request: str) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first."

        task_record = (
            self.db.query(TaskModel)
            .filter(
                TaskModel.user_id == str(current_user.get("id")),
                TaskModel.task_name == delete_request,
            )
            .first()
        )
        if not task_record:
            return "Task not found"

        self.db.delete(task_record)
        self.db.commit()
        return "Task deleted successfully!"

    def mark_task_as_complete(self, current_user: dict, task_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        task_record = (
            self.db.query(TaskModel)
            .filter(
                TaskModel.user_id == str(current_user.get("id")),
                TaskModel.task_name.ilike(task_name.strip()),
            )
            .first()
        )
        if not task_record:
            return False

        now = now_dubai()
        log = list(task_record.completion_log or [])
        log.append(now)
        task_record.completion_log = log

        if task_record.is_recurring and task_record.recurrence:
            task_record.task_deadline = calculate_next_due(
                task_record.task_deadline, task_record.recurrence
            )
            task_record.status = "pending"
            task_record.completed_at = None
        else:
            task_record.status = "completed"
            task_record.completed_at = now

        task_record.updated_at = now
        self.db.commit()
        return True

    def set_priority(self, current_user: dict, task_id: str, priority: int) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        task_record = (
            self.db.query(TaskModel)
            .filter(
                TaskModel.user_id == str(current_user.get("id")),
                TaskModel.id == str(task_id),
            )
            .first()
        )
        if not task_record:
            return False

        task_record.priority = str(priority)
        task_record.updated_at = now_dubai()
        self.db.commit()
        return True


class HabitService:
    def __init__(self, db: Session) -> None:
        self.db = db

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

        new_habit = HabitModel(
            id=generate_id(),
            user_id=str(current_user.get("id")),
            habit_name=habit_name.strip().lower(),
            habit_description=habit_description,
            habit_frequency=habit_frequency,
            habit_start_date=habit_start_date,
            habit_notes=habit_notes,
            completion_log=[],
            streak=0,
            best_streak=0,
            last_completed_date=None,
            created_at=now_dubai(),
            updated_at=now_dubai(),
            status="pending",
            completed_at=None,
            is_archived=False,
        )
        self.db.add(new_habit)
        self.db.commit()
        self.db.refresh(new_habit)
        return _habit_to_dict(new_habit)

    def list_habits(self, current_user: dict | None) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        habits = (
            self.db.query(HabitModel)
            .filter(
                HabitModel.user_id == str(current_user.get("id")),
                HabitModel.is_archived.is_(False),
            )
            .all()
        )
        return [_habit_to_dict(h) for h in habits]

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

        habit_record = (
            self.db.query(HabitModel)
            .filter(
                HabitModel.user_id == str(current_user.get("id")),
                HabitModel.habit_name.ilike(updated_habit_name.strip()),
            )
            .first()
        )
        if not habit_record:
            return False

        if updated_description is not None:
            habit_record.habit_description = updated_description
        if updated_frequency is not None:
            habit_record.habit_frequency = updated_frequency
        if updated_start_date is not None:
            habit_record.habit_start_date = updated_start_date
        if updated_notes is not None:
            habit_record.habit_notes = updated_notes
        habit_record.updated_at = now_dubai()
        self.db.commit()
        return True

    def mark_habit_as_complete(self, current_user: dict | None, habit_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        habit_record = (
            self.db.query(HabitModel)
            .filter(
                HabitModel.user_id == str(current_user.get("id")),
                HabitModel.habit_name.ilike(habit_name.strip()),
            )
            .first()
        )
        if not habit_record:
            return False

        today = datetime.now(DXB_TZ).date()
        today_str = today.isoformat()

        already_done_today = habit_record.last_completed_date == today_str
        if not already_done_today:
            if habit_record.last_completed_date:
                delta_days = (today - date.fromisoformat(habit_record.last_completed_date)).days
                habit_record.streak = (habit_record.streak or 0) + 1 if delta_days == 1 else 1
            else:
                habit_record.streak = 1
            habit_record.best_streak = max(habit_record.best_streak or 0, habit_record.streak)
            habit_record.last_completed_date = today_str

        log = list(habit_record.completion_log or [])
        log.append(today_str)
        habit_record.completion_log = log

        now = now_dubai()
        habit_record.status = "completed"
        habit_record.completed_at = now
        habit_record.updated_at = now
        self.db.commit()
        return True

    def delete_habit(self, current_user: dict | None, habit_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        habit_record = (
            self.db.query(HabitModel)
            .filter(
                HabitModel.user_id == str(current_user.get("id")),
                HabitModel.habit_name.ilike(habit_name.strip()),
            )
            .first()
        )
        if not habit_record:
            return False

        self.db.delete(habit_record)
        self.db.commit()
        return True

class project:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_projects(
        self,
        current_user: dict,
        project_title: str,
        project_description: str,
        project_duration: int,
        project_created_at: str,
        project_deadline: str,
        project_notes: str,
    ) -> dict[str, Any]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return {}

        new_project = ProjectModel(
            id=generate_id(),
            user_id=str(current_user.get("id")),
            project_title=project_title,
            project_description=project_description,
            project_duration=project_duration,
            project_deadline=project_deadline,
            project_notes=project_notes,
            created_at=project_created_at,
            updated_at=now_dubai(),
            status="pending",
            completed_at=None,
            is_archived=False,
        )
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return _project_to_dict(new_project)

    def show_projects(self, current_user: dict) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return []

        projects = (
            self.db.query(ProjectModel)
            .filter(
                ProjectModel.user_id == str(current_user.get("id")),
                ProjectModel.is_archived.is_(False),
            )
            .all()
        )
        return [_project_to_dict(p) for p in projects]

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

        project_record = (
            self.db.query(ProjectModel)
            .filter(
                ProjectModel.user_id == str(current_user.get("id")),
                ProjectModel.project_title == project_update_request,
            )
            .first()
        )
        if not project_record:
            return "Project not found"

        project_record.project_title = project_title
        project_record.project_description = project_description
        project_record.project_deadline = project_deadline
        project_record.project_notes = project_notes
        project_record.updated_at = now_dubai()
        self.db.commit()
        return "Project updated successfully"

    def delete_project(self, current_user: dict, project_delete_request: str) -> str:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return "Please log in first"

        project_record = (
            self.db.query(ProjectModel)
            .filter(
                ProjectModel.user_id == str(current_user.get("id")),
                ProjectModel.project_title == project_delete_request,
            )
            .first()
        )
        if not project_record:
            return "Project not found"

        self.db.delete(project_record)
        self.db.commit()
        return "Project deleted successfully"

    def mark_project_as_complete(self, current_user: dict, project_title: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        project_record = (
            self.db.query(ProjectModel)
            .filter(
                ProjectModel.user_id == str(current_user.get("id")),
                ProjectModel.project_title.ilike(project_title.strip()),
            )
            .first()
        )
        if not project_record:
            return False

        now = now_dubai()
        project_record.status = "completed"
        project_record.completed_at = now
        project_record.updated_at = now
        self.db.commit()
        return True

class ArchiveStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def archive_tasks(self, current_user: dict | None, task_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        task_record = (
            self.db.query(TaskModel)
            .filter(
                TaskModel.user_id == str(current_user.get("id")),
                TaskModel.task_name.ilike(task_name.strip()),
            )
            .first()
        )
        if not task_record:
            return False

        task_record.is_archived = True
        task_record.updated_at = now_dubai()
        self.db.commit()
        return True

    def archive_habits(self, current_user: dict | None, habit_name: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        habit_record = (
            self.db.query(HabitModel)
            .filter(
                HabitModel.user_id == str(current_user.get("id")),
                HabitModel.habit_name.ilike(habit_name.strip()),
            )
            .first()
        )
        if not habit_record:
            return False

        habit_record.is_archived = True
        habit_record.updated_at = now_dubai()
        self.db.commit()
        return True

    def archive_projects(self, current_user: dict | None, project_title: str) -> bool:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return False

        project_record = (
            self.db.query(ProjectModel)
            .filter(
                ProjectModel.user_id == str(current_user.get("id")),
                ProjectModel.project_title.ilike(project_title.strip()),
            )
            .first()
        )
        if not project_record:
            return False

        project_record.is_archived = True
        project_record.updated_at = now_dubai()
        self.db.commit()
        return True

    def save_archive(self, current_user: dict | None) -> tuple[bool, str]:
        return True, "Saved"

    def view_archive(self, current_user: dict | None) -> dict[str, Any] | None:
        current_user = ensure_current_user(current_user)
        if not current_user:
            return None

        uid = str(current_user.get("id"))
        tasks = (
            self.db.query(TaskModel)
            .filter(TaskModel.user_id == uid, TaskModel.is_archived.is_(True))
            .all()
        )
        habits = (
            self.db.query(HabitModel)
            .filter(HabitModel.user_id == uid, HabitModel.is_archived.is_(True))
            .all()
        )
        projects = (
            self.db.query(ProjectModel)
            .filter(ProjectModel.user_id == uid, ProjectModel.is_archived.is_(True))
            .all()
        )
        return {
            "tasks": [_task_to_dict(t) for t in tasks],
            "habits": [_habit_to_dict(h) for h in habits],
            "projects": [_project_to_dict(p) for p in projects],
        }

class Tracker_search_engine:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search_tasks_engine(
        self, current_user: dict | None, keyword: str | None = None
    ) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user or not keyword or not keyword.strip():
            return []

        kw = f"%{keyword.strip().lower()}%"
        tasks = (
            self.db.query(TaskModel)
            .filter(
                TaskModel.user_id == str(current_user.get("id")),
                TaskModel.is_archived.is_(False),
                TaskModel.task_name.ilike(kw),
            )
            .all()
        )
        return [_task_to_dict(t) for t in tasks]

    def search_habits_engine(
        self, current_user: dict | None, keyword: str | None = None
    ) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user or not keyword or not keyword.strip():
            return []

        kw = f"%{keyword.strip().lower()}%"
        habits = (
            self.db.query(HabitModel)
            .filter(
                HabitModel.user_id == str(current_user.get("id")),
                HabitModel.is_archived.is_(False),
                HabitModel.habit_name.ilike(kw),
            )
            .all()
        )
        return [_habit_to_dict(h) for h in habits]

    def search_projects_engine(
        self, current_user: dict | None, keyword: str | None = None
    ) -> list[dict[str, Any]]:
        current_user = ensure_current_user(current_user)
        if not current_user or not keyword or not keyword.strip():
            return []

        kw = f"%{keyword.strip().lower()}%"
        projects = (
            self.db.query(ProjectModel)
            .filter(
                ProjectModel.user_id == str(current_user.get("id")),
                ProjectModel.is_archived.is_(False),
                ProjectModel.project_title.ilike(kw),
            )
            .all()
        )
        return [_project_to_dict(p) for p in projects]


class ProductivityOverviewDashboard:
    def __init__(self, tz: str = "Asia/Dubai") -> None:
        self.tz = ZoneInfo(tz)

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
            "done_today": completed_today,
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
            status = (project_item.get("status", "") or "").lower()
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
