# calendar logic for MyLife app
from typing import Any

from app.modules.MyLife_Tracker import *


def _get_user_record(current_user: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    current_user = ensure_current_user(current_user)
    data = load_database()
    if not current_user:
        return data, None

    user = next(
        (u for u in data.get("users", []) if str(u.get("id")) == str(current_user.get("id"))),
        None,
    )
    return data, user


def create_calendar_event(
    current_user: dict[str, Any] | None,
    title: str,
    event_type: str,
    event_date: str,
    notes: str = "",
) -> dict[str, Any] | None:
    data, user = _get_user_record(current_user)
    if not user:
        return None

    event = {
        "id": generate_id(),
        "title": title.strip() or "untitled",
        "event_type": event_type.strip().lower() or "general",
        "event_date": event_date,
        "notes": notes.strip(),
        "created_at": now_dubai(),
        "updated_at": now_dubai(),
    }
    user.setdefault("calendar_events", []).append(event)
    save_database(data)
    return event


def list_calendar_events(current_user: dict[str, Any] | None) -> list[dict[str, Any]]:
    _, user = _get_user_record(current_user)
    if not user:
        return []
    return user.get("calendar_events", [])


def group_calendar_events_by_type(current_user: dict[str, Any] | None) -> dict[str, int]:
    grouped: dict[str, int] = {}
    for event in list_calendar_events(current_user):
        event_type = str(event.get("event_type", "general")).lower()
        grouped[event_type] = grouped.get(event_type, 0) + 1
    return grouped


def list_upcoming_deadlines(current_user: dict[str, Any] | None) -> dict[str, list[dict[str, str]]]:
    _, user = _get_user_record(current_user)
    if not user:
        return {"tasks": [], "projects": []}

    task_deadlines = [
        {
            "id": str(task.get("id", "")),
            "name": task.get("task_name", "untitled"),
            "deadline": task.get("task_deadline"),
        }
        for task in user.get("tasks", [])
        if task.get("task_deadline")
    ]

    project_deadlines = [
        {
            "id": str(project.get("id", "")),
            "name": project.get("project_title", "untitled"),
            "deadline": project.get("project_deadline"),
        }
        for project in user.get("projects", [])
        if project.get("project_deadline")
    ]

    return {"tasks": task_deadlines, "projects": project_deadlines}


def get_calendar_overview(current_user: dict[str, Any] | None) -> dict[str, Any] | None:
    _, user = _get_user_record(current_user)
    if not user:
        return None

    events = list_calendar_events(current_user)
    deadlines = list_upcoming_deadlines(current_user)
    return {
        "calendar_events_count": len(events),
        "tasks_count": len(user.get("tasks", [])),
        "projects_count": len(user.get("projects", [])),
        "events_by_type": group_calendar_events_by_type(current_user),
        "upcoming_task_deadlines": deadlines["tasks"],
        "upcoming_project_deadlines": deadlines["projects"],
    }


def get_reminder_placeholders(current_user: dict[str, Any] | None) -> dict[str, Any]:
    current_user = ensure_current_user(current_user)
    return {
        "current_user_id": str(current_user.get("id")) if current_user else None,
        "status": "not_implemented",
        "message": "Reminder creation and notifications will be implemented through routes/forms.",
    }
