import json
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.dependencies import require_user
from app.modules.MyLife_Tracker import (
    ArchiveStore as TrackerArchiveService,
    HabitService as TrackerHabitService,
    ProductivityOverviewDashboard,
    Tracker_search_engine,
    now_dubai,
    project as TrackerProjectService,
    task as Trackertask,
    validate_deadline_input,
)

router = APIRouter(prefix="/tracker", tags=["tracker"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _parse_json_object(payload: str | None, field_name: str) -> dict[str, Any] | None:
    if not payload:
        return None
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def _find_item_by_name(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    target = value.strip().lower()
    for item in items:
        if str(item.get(key, "")).strip().lower() == target:
            return item
    return None


@router.get("/dashboard", response_class=HTMLResponse)
def tracker_dashboard_page(request: Request, current_user=Depends(require_user)):
    dashboard = ProductivityOverviewDashboard(current_user)
    task_service = Trackertask()
    habit_service = TrackerHabitService()
    project_service = TrackerProjectService()

    tasks = task_service.view_tasks(current_user)
    habits = habit_service.list_habits(current_user)
    projects = project_service.show_projects(current_user)

    return templates.TemplateResponse(
        "tracker/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "tasks": tasks,
            "habits": habits,
            "projects": projects,
            "task_metrics": dashboard.task_metrics(tasks),
            "habit_metrics": dashboard.habits_metrics(habits),
            "project_metrics": dashboard.projects_metrics(projects),
        },
    )


@router.get("/tasks", response_class=HTMLResponse)
def create_tasks_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "tracker/create_task.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/tasks", response_class=HTMLResponse)
def create_tasks_post(
    request: Request,
    task_name: str = Form(...),
    task_type: str = Form(...),
    task_description: str = Form(...),
    task_deadline: str = Form(...),
    task_notes: str = Form(""),
    recurring: bool = Form(False),
    recurrence_rule_json: str = Form(""),
    current_user=Depends(require_user),
):
    task_service = Trackertask()

    normalized_deadline, deadline_error = validate_deadline_input(task_deadline)
    if deadline_error:
        return templates.TemplateResponse(
            "tracker/create_task.html",
            {
                "request": request,
                "current_user": current_user,
                "task": {
                    "task_name": task_name,
                    "task_type": task_type,
                    "task_description": task_description,
                    "task_deadline": task_deadline,
                    "task_notes": task_notes,
                    "recurring": recurring,
                    "recurrence_rule_json": recurrence_rule_json,
                },
                "error": deadline_error,
            },
            status_code=400,
        )

    try:
        rule = _parse_json_object(recurrence_rule_json, "recurrence_rule") if recurring else None
        created_task = task_service.create_task(
            current_user=current_user,
            task_name=task_name,
            task_type=task_type,
            task_description=task_description,
            created_at=now_dubai(),
            task_deadline=normalized_deadline or task_deadline,
            task_notes=task_notes,
            recurring=recurring,
            rule=rule,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "tracker/create_task.html",
            {
                "request": request,
                "current_user": current_user,
                "task": {
                    "task_name": task_name,
                    "task_type": task_type,
                    "task_description": task_description,
                    "task_deadline": task_deadline,
                    "task_notes": task_notes,
                    "recurring": recurring,
                    "recurrence_rule_json": recurrence_rule_json,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not created_task:
        return RedirectResponse(
            url="/tracker/tasks/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/tracker/tasks/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/tasks/list", response_class=HTMLResponse)
def tasks_list_page(request: Request, current_user=Depends(require_user)):
    task_service = Trackertask()
    tasks = task_service.view_tasks(current_user)

    return templates.TemplateResponse(
        "tracker/tasks_list.html",
        {
            "request": request,
            "current_user": current_user,
            "tasks": tasks,
            "error": None,
        },
    )


@router.get("/tasks/{task_name}/edit", response_class=HTMLResponse)
def edit_task_page(request: Request, task_name: str, current_user=Depends(require_user)):
    task_service = Trackertask()
    task_item = _find_item_by_name(task_service.view_tasks(current_user), "task_name", task_name)

    if not task_item:
        return RedirectResponse(
            url="/tracker/tasks/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "tracker/edit_task.html",
        {
            "request": request,
            "current_user": current_user,
            "task": task_item,
            "error": None,
        },
    )


@router.post("/tasks/{task_name}/edit", response_class=HTMLResponse)
def edit_tasks_submit(
    request: Request,
    task_name: str,
    updated_task_name: str = Form(...),
    updated_task_type: str = Form(...),
    updated_task_description: str = Form(...),
    updated_task_deadline: str = Form(...),
    updated_task_notes: str = Form(""),
    current_user=Depends(require_user),
):
    task_service = Trackertask()
    normalized_deadline, deadline_error = validate_deadline_input(updated_task_deadline)
    if deadline_error:
        return templates.TemplateResponse(
            "tracker/edit_task.html",
            {
                "request": request,
                "current_user": current_user,
                "task": {
                    "task_name": updated_task_name,
                    "task_type": updated_task_type,
                    "task_description": updated_task_description,
                    "task_deadline": updated_task_deadline,
                    "task_notes": updated_task_notes,
                },
                "error": deadline_error,
            },
            status_code=400,
        )

    update_result = task_service.update_task(
        current_user=current_user,
        user_update_request=task_name,
        updated_task_name=updated_task_name,
        updated_task_type=updated_task_type,
        updated_task_description=updated_task_description,
        updated_task_deadline=normalized_deadline or updated_task_deadline,
        updated_task_notes=updated_task_notes,
    )

    if update_result != "Task updated successfully!":
        return templates.TemplateResponse(
            "tracker/edit_task.html",
            {
                "request": request,
                "current_user": current_user,
                "task": {
                    "task_name": updated_task_name,
                    "task_type": updated_task_type,
                    "task_description": updated_task_description,
                    "task_deadline": updated_task_deadline,
                    "task_notes": updated_task_notes,
                },
                "error": update_result,
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/tracker/tasks/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_name}/delete")
def delete_task_submit(task_name: str, current_user=Depends(require_user)):
    task_service = Trackertask()
    task_service.delete_task(current_user, task_name)

    return RedirectResponse(
        url="/tracker/tasks/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_name}/complete")
def task_complete_submit(task_name: str, current_user=Depends(require_user)):
    tasks_service = Trackertask()
    tasks_service.mark_task_as_complete(current_user, task_name)

    return RedirectResponse(
        url="/tracker/tasks/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tasks/{task_id}/priority")
def set_priority_post(
    task_id: str,
    priority: int = Form(...),
    current_user=Depends(require_user),
):
    task_service = Trackertask()
    task_service.set_priority(current_user, task_id, priority)

    return RedirectResponse(
        url="/tracker/tasks/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/habits", response_class=HTMLResponse)
def create_habit_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "tracker/create_habit.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/habits", response_class=HTMLResponse)
def create_habit_post(
    request: Request,
    current_user=Depends(require_user),
    habit_name: str = Form(...),
    habit_description: str = Form(...),
    habit_frequency: str = Form(...),
    habit_start_date: str = Form(...),
    habit_notes: str = Form(""),
):
    habit_service = TrackerHabitService()

    habit = habit_service.create_habit(
        current_user=current_user,
        habit_name=habit_name,
        habit_description=habit_description,
        habit_frequency=habit_frequency,
        habit_start_date=habit_start_date,
        habit_notes=habit_notes,
    )

    if not habit:
        return templates.TemplateResponse(
            "tracker/create_habit.html",
            {
                "request": request,
                "current_user": current_user,
                "habit": {
                    "habit_name": habit_name,
                    "habit_description": habit_description,
                    "habit_frequency": habit_frequency,
                    "habit_start_date": habit_start_date,
                    "habit_notes": habit_notes,
                },
                "error": "Unable to create habit.",
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/tracker/habits/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/habits/list", response_class=HTMLResponse)
def habits_list_page(request: Request, current_user=Depends(require_user)):
    habit_service = TrackerHabitService()
    habits = habit_service.list_habits(current_user)
    return templates.TemplateResponse(
        "tracker/habits_list.html",
        {
            "request": request,
            "current_user": current_user,
            "habits": habits,
            "error": None,
        },
    )


@router.get("/habits/{habit_name}/edit", response_class=HTMLResponse)
def edit_habit_page(request: Request, habit_name: str, current_user=Depends(require_user)):
    habit_service = TrackerHabitService()
    habit = _find_item_by_name(habit_service.list_habits(current_user), "habit_name", habit_name)
    if not habit:
        return RedirectResponse(
            url="/tracker/habits/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "tracker/edit_habit.html",
        {
            "request": request,
            "current_user": current_user,
            "habit": habit,
            "error": None,
        },
    )


@router.post("/habits/{habit_name}/edit", response_class=HTMLResponse)
def edit_habit_submit(
    request: Request,
    habit_name: str,
    habit_description: str = Form(""),
    habit_frequency: str = Form(""),
    habit_start_date: str = Form(""),
    habit_notes: str = Form(""),
    current_user=Depends(require_user),
):
    habit_service = TrackerHabitService()
    updated = habit_service.update_habit(
        current_user=current_user,
        updated_habit_name=habit_name,
        updated_description=habit_description,
        updated_frequency=habit_frequency,
        updated_start_date=habit_start_date,
        updated_notes=habit_notes,
    )

    if not updated:
        return templates.TemplateResponse(
            "tracker/edit_habit.html",
            {
                "request": request,
                "current_user": current_user,
                "habit": {
                    "habit_name": habit_name,
                    "habit_description": habit_description,
                    "habit_frequency": habit_frequency,
                    "habit_start_date": habit_start_date,
                    "habit_notes": habit_notes,
                },
                "error": "Unable to update habit.",
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/tracker/habits/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/habits/{habit_name}/delete")
def delete_habit_submit(habit_name: str, current_user=Depends(require_user)):
    habit_service = TrackerHabitService()
    habit_service.delete_habit(current_user, habit_name)
    return RedirectResponse(
        url="/tracker/habits/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/habits/{habit_name}/complete")
def complete_habit_submit(habit_name: str, current_user=Depends(require_user)):
    habit_service = TrackerHabitService()
    habit_service.mark_habit_as_complete(current_user, habit_name)
    return RedirectResponse(
        url="/tracker/habits/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/projects", response_class=HTMLResponse)
def create_project_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "tracker/create_project.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/projects", response_class=HTMLResponse)
def create_project_post(
    request: Request,
    current_user=Depends(require_user),
    project_title: str = Form(...),
    project_description: str = Form(...),
    project_duration: int = Form(...),
    project_deadline: str = Form(...),
    project_notes: str = Form(""),
):
    project_service = TrackerProjectService()
    normalized_deadline, deadline_error = validate_deadline_input(project_deadline)
    if deadline_error:
        return templates.TemplateResponse(
            "tracker/create_project.html",
            {
                "request": request,
                "current_user": current_user,
                "project": {
                    "project_title": project_title,
                    "project_description": project_description,
                    "project_duration": project_duration,
                    "project_deadline": project_deadline,
                    "project_notes": project_notes,
                },
                "error": deadline_error,
            },
            status_code=400,
        )

    project_record = project_service.create_projects(
        current_user=current_user,
        project_title=project_title,
        project_description=project_description,
        project_duration=project_duration,
        project_created_at=now_dubai(),
        project_deadline=normalized_deadline or project_deadline,
        project_notes=project_notes,
    )

    if not project_record:
        return templates.TemplateResponse(
            "tracker/create_project.html",
            {
                "request": request,
                "current_user": current_user,
                "project": {
                    "project_title": project_title,
                    "project_description": project_description,
                    "project_duration": project_duration,
                    "project_deadline": project_deadline,
                    "project_notes": project_notes,
                },
                "error": "Unable to create project.",
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/tracker/projects/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/projects/list", response_class=HTMLResponse)
def projects_list_page(request: Request, current_user=Depends(require_user)):
    project_service = TrackerProjectService()
    projects = project_service.show_projects(current_user)
    return templates.TemplateResponse(
        "tracker/projects_list.html",
        {
            "request": request,
            "current_user": current_user,
            "projects": projects,
            "error": None,
        },
    )


@router.get("/projects/{project_title}/edit", response_class=HTMLResponse)
def edit_project_page(request: Request, project_title: str, current_user=Depends(require_user)):
    project_service = TrackerProjectService()
    project = _find_item_by_name(project_service.show_projects(current_user), "project_title", project_title)
    if not project:
        return RedirectResponse(
            url="/tracker/projects/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "tracker/edit_project.html",
        {
            "request": request,
            "current_user": current_user,
            "project": project,
            "error": None,
        },
    )


@router.post("/projects/{project_title}/edit", response_class=HTMLResponse)
def edit_project_submit(
    request: Request,
    project_title: str,
    updated_project_title: str = Form(...),
    updated_project_description: str = Form(...),
    updated_project_deadline: str = Form(...),
    updated_project_notes: str = Form(""),
    current_user=Depends(require_user),
):
    project_service = TrackerProjectService()
    normalized_deadline, deadline_error = validate_deadline_input(updated_project_deadline)
    if deadline_error:
        return templates.TemplateResponse(
            "tracker/edit_project.html",
            {
                "request": request,
                "current_user": current_user,
                "project": {
                    "project_title": updated_project_title,
                    "project_description": updated_project_description,
                    "project_deadline": updated_project_deadline,
                    "project_notes": updated_project_notes,
                },
                "error": deadline_error,
            },
            status_code=400,
        )

    update_result = project_service.update_project(
        current_user=current_user,
        project_update_request=project_title,
        project_title=updated_project_title,
        project_description=updated_project_description,
        project_deadline=normalized_deadline or updated_project_deadline,
        project_notes=updated_project_notes,
    )

    if update_result != "Project updated successfully":
        return templates.TemplateResponse(
            "tracker/edit_project.html",
            {
                "request": request,
                "current_user": current_user,
                "project": {
                    "project_title": updated_project_title,
                    "project_description": updated_project_description,
                    "project_deadline": updated_project_deadline,
                    "project_notes": updated_project_notes,
                },
                "error": update_result,
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/tracker/projects/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/projects/{project_title}/delete")
def delete_project_submit(project_title: str, current_user=Depends(require_user)):
    project_service = TrackerProjectService()
    project_service.delete_project(current_user, project_title)
    return RedirectResponse(
        url="/tracker/projects/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/projects/{project_title}/complete")
def complete_project_submit(project_title: str, current_user=Depends(require_user)):
    project_service = TrackerProjectService()
    project_service.mark_project_as_complete(current_user, project_title)
    return RedirectResponse(
        url="/tracker/projects/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/archive", response_class=HTMLResponse)
def archive_page(request: Request, current_user=Depends(require_user)):
    archive_service = TrackerArchiveService()
    archive = archive_service.view_archive(current_user)
    return templates.TemplateResponse(
        "tracker/archive.html",
        {
            "request": request,
            "current_user": current_user,
            "archive": archive,
        },
    )


@router.post("/tasks/{task_name}/archive")
def archive_task_submit(task_name: str, current_user=Depends(require_user)):
    archive_service = TrackerArchiveService()
    archive_service.archive_tasks(current_user, task_name)
    archive_service.save_archive(current_user)
    return RedirectResponse(
        url="/tracker/archive",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/habits/{habit_name}/archive")
def archive_habit_submit(habit_name: str, current_user=Depends(require_user)):
    archive_service = TrackerArchiveService()
    archive_service.archive_habits(current_user, habit_name)
    archive_service.save_archive(current_user)
    return RedirectResponse(
        url="/tracker/archive",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/projects/{project_title}/archive")
def archive_project_submit(project_title: str, current_user=Depends(require_user)):
    archive_service = TrackerArchiveService()
    archive_service.archive_projects(current_user, project_title)
    archive_service.save_archive(current_user)
    return RedirectResponse(
        url="/tracker/archive",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/search", response_class=HTMLResponse)
def tracker_search_page(request: Request, keyword: str = "", current_user=Depends(require_user)):
    search_engine = Tracker_search_engine()
    keyword = keyword.strip()
    return templates.TemplateResponse(
        "tracker/search.html",
        {
            "request": request,
            "current_user": current_user,
            "keyword": keyword,
            "tasks": search_engine.search_tasks_engine(current_user, keyword),
            "habits": search_engine.search_habits_engine(current_user, keyword),
            "projects": search_engine.search_projects_engine(current_user, keyword),
        },
    )
