from typing import Any

from app.modules.MyLife_Tracker import *
from app.modules.MyLife_Calender import get_calendar_overview
from app.modules.MyLife_Fitness import load_fitness_database, _current_user_id, _fitness_record_belongs_to_user
from app.modules.MyLife_Finance import get_user_finance_records


def _get_user_record(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None

    data_loader = load_database()
    current_id = str(current_user.get("id"))
    return next((u for u in data_loader.get("users", []) if str(u.get("id")) == current_id), None)


def _build_fitness_statistics(current_user: dict[str, Any] | None) -> dict[str, int]:
    current_user_id = _current_user_id(current_user)
    if not current_user_id:
        return {
            "meal_logs": 0,
            "workout_sessions": 0,
            "routines": 0,
            "meal_plans": 0,
        }

    fitness_data = load_fitness_database()
    return {
        "meal_logs": len([meal for meal in fitness_data.get("meal_log", []) if _fitness_record_belongs_to_user(meal, current_user_id)]),
        "workout_sessions": len([session for session in fitness_data.get("workout_sessions", []) if _fitness_record_belongs_to_user(session, current_user_id)]),
        "routines": len([routine for routine in fitness_data.get("routines", []) if _fitness_record_belongs_to_user(routine, current_user_id)]),
        "meal_plans": len([plan for plan in fitness_data.get("meal_plans", []) if _fitness_record_belongs_to_user(plan, current_user_id)]),
    }


def _build_finance_statistics(current_user: dict[str, Any] | None) -> dict[str, int]:
    finance_records = get_user_finance_records(current_user)
    if not finance_records:
        return {"accounts": 0, "categories": 0, "transactions": 0}

    return {
        "accounts": len(finance_records.get("accounts", [])),
        "categories": len(finance_records.get("categories", [])),
        "transactions": len(finance_records.get("transactions", [])),
    }


def build_statistics_summary(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None

    user = _get_user_record(current_user)
    if not user:
        return None

    fitness_stats = _build_fitness_statistics(current_user)
    finance_stats = _build_finance_statistics(current_user)
    calendar_stats = get_calendar_overview(current_user) or {}

    return {
        "tasks_tracked": len(user.get("tasks", [])),
        "habits_tracked": len(user.get("habits", [])),
        "projects_tracked": len(user.get("projects", [])),
        "fitness": fitness_stats,
        "finance": finance_stats,
        "calendar": calendar_stats,
    }


def build_productivity_analytics(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    user = _get_user_record(current_user)
    if not user:
        return None
    return {
        "tasks_total": len(user.get("tasks", [])),
        "tasks_completed": len([task for task in user.get("tasks", []) if task.get("is_completed")]),
        "projects_total": len(user.get("projects", [])),
        "projects_completed": len([project for project in user.get("projects", []) if project.get("is_completed")]),
    }


def build_habit_analytics(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    user = _get_user_record(current_user)
    if not user:
        return None
    habits = user.get("habits", [])
    return {
        "habits_total": len(habits),
        "habits_completed_today": len([habit for habit in habits if habit.get("completed_today")]),
    }


def build_finance_analytics(current_user: dict[str, Any] | None) -> dict[str, int]:
    return _build_finance_statistics(current_user)
