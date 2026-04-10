import json
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.dependencies import require_user
from app.modules.MyLife_Fitness import (
    CalorieTracker,
    MealPlanService,
    MealTracker,
    NutritionSummaryService,
    RoutineService,
    Workout_Repository,
    WorkoutSessionService,
)

router = APIRouter(prefix="/fitness", tags=["fitness"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _parse_json_list(payload: str, field_name: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON") from exc

    if not isinstance(parsed, list):
        raise ValueError(f"{field_name} must be a JSON list")
    return parsed


@router.get("/dashboard", response_class=HTMLResponse)
def fitness_dashboard(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "fitness/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )


@router.get("/calories", response_class=HTMLResponse)
def calorie_goal_page(request: Request, current_user=Depends(require_user)):
    calorie_tracker = CalorieTracker()
    return templates.TemplateResponse(
        "fitness/calories.html",
        {
            "request": request,
            "current_user": current_user,
            "daily_goal": calorie_tracker.get_daily_calorie_goal(current_user),
            "error": None,
        },
    )


@router.post("/calories", response_class=HTMLResponse)
def calorie_goal_submit(
    request: Request,
    current_user=Depends(require_user),
    goal: int = Form(...),
):
    calorie_tracker = CalorieTracker()
    try:
        calorie_tracker.set_calorie_goal(current_user, goal)
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/calories.html",
            {
                "request": request,
                "current_user": current_user,
                "daily_goal": goal,
                "error": str(exc),
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/fitness/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/calories/{target_date}", response_class=HTMLResponse)
def calorie_goal_day_page(
    request: Request,
    target_date: str,
    current_user=Depends(require_user),
):
    calorie_tracker = CalorieTracker()
    try:
        calorie_summary = calorie_tracker.show_daily_calorie(current_user, target_date)
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/calorie_day.html",
            {
                "request": request,
                "current_user": current_user,
                "target_date": target_date,
                "calorie_summary": None,
                "error": str(exc),
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        "fitness/calorie_day.html",
        {
            "request": request,
            "current_user": current_user,
            "target_date": target_date,
            "calorie_summary": calorie_summary,
            "error": None,
        },
    )


@router.get("/meals", response_class=HTMLResponse)
def create_meal_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "fitness/create_meal.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/meals", response_class=HTMLResponse)
def create_meal_submit(
    request: Request,
    current_user=Depends(require_user),
    meal_name: str = Form(...),
    meal_type: str = Form(...),
    calorie_in_meal: int = Form(...),
    completion_date: str = Form(...),
    protein: int = Form(0),
    carbs: int = Form(0),
    fats: int = Form(0),
    notes: str = Form(""),
):
    meal_service = MealTracker()

    try:
        meal = meal_service.add_meal(
            current_user=current_user,
            meal_name=meal_name,
            meal_type=meal_type,
            calorie_in_meal=calorie_in_meal,
            completetion_date=completion_date,
            notes=notes,
            protein=protein,
            carbs=carbs,
            fats=fats,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/create_meal.html",
            {
                "request": request,
                "current_user": current_user,
                "meal": {
                    "meal_name": meal_name,
                    "meal_type": meal_type,
                    "calorie_in_meal": calorie_in_meal,
                    "completion_date": completion_date,
                    "protein": protein,
                    "carbs": carbs,
                    "fats": fats,
                    "notes": notes,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not meal:
        return RedirectResponse(
            url="/fitness/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/meals/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/meals/list", response_class=HTMLResponse)
def show_meals_page(request: Request, current_user=Depends(require_user)):
    meal_service = MealTracker()
    meals = meal_service.view_meal(current_user)

    return templates.TemplateResponse(
        "fitness/meals_list.html",
        {
            "request": request,
            "current_user": current_user,
            "meals": meals,
        },
    )


@router.get("/meals/{meal_id}/edit", response_class=HTMLResponse)
def edit_meal_page(
    request: Request,
    meal_id: str,
    current_user=Depends(require_user),
):
    meal_service = MealTracker()
    meal = meal_service.find_meal(current_user, meal_id)

    if not meal:
        return RedirectResponse(
            url="/fitness/meals/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "fitness/edit_meal.html",
        {
            "request": request,
            "current_user": current_user,
            "meal": meal,
            "error": None,
        },
    )


@router.post("/meals/{meal_id}/edit", response_class=HTMLResponse)
def edit_meal_post(
    request: Request,
    meal_id: str,
    current_user=Depends(require_user),
    meal_name: str = Form(...),
    meal_type: str = Form(...),
    calorie_in_meal: int = Form(...),
    protein: int = Form(0),
    carbs: int = Form(0),
    fats: int = Form(0),
    completion_date: str = Form(...),
    time_of_log: str = Form(...),
    notes: str = Form(""),
):
    meal_service = MealTracker()
    try:
        updated_meal = meal_service.update_meal(
            meal_id=meal_id,
            current_user=current_user,
            updated_meal_name=meal_name,
            updated_meal_type=meal_type,
            updated_meal_in_calorie=calorie_in_meal,
            updated_protein=protein,
            updated_carbs=carbs,
            updated_fats=fats,
            updated_time_of_log=time_of_log,
            updated_completiton_date=completion_date,
            updataed_notes=notes,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/edit_meal.html",
            {
                "request": request,
                "current_user": current_user,
                "meal": {
                    "id": meal_id,
                    "meal_name": meal_name,
                    "meal_type": meal_type,
                    "calories": calorie_in_meal,
                    "protein": protein,
                    "carbs": carbs,
                    "fats": fats,
                    "time_of_log": time_of_log,
                    "completion_date": completion_date,
                    "notes": notes,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not updated_meal:
        return RedirectResponse(
            url="/fitness/meals/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/meals/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/meals/{meal_id}/delete")
def delete_meal(meal_id: str, current_user=Depends(require_user)):
    meal_service = MealTracker()
    meal_service.delete_meal(current_user, meal_id)

    return RedirectResponse(
        url="/fitness/meals/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/meal-plans", response_class=HTMLResponse)
def create_meal_plan_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "fitness/create_meal_plan.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/meal-plans", response_class=HTMLResponse)
def create_meal_plan_submit(
    request: Request,
    current_user=Depends(require_user),
    plan_name: str = Form(...),
    goal: str = Form(...),
    daily_target_calories: int = Form(0),
    daily_target_protein: int = Form(0),
    daily_target_carbs: int = Form(0),
    daily_target_fats: int = Form(0),
    meals_json: str = Form(...),
):
    meal_plan_service = MealPlanService()

    try:
        meals = _parse_json_list(meals_json, "meals")
        meal_plan = meal_plan_service.create_meal_plan(
            current_user=current_user,
            plan_name=plan_name,
            goal=goal,
            daily_target_calories=daily_target_calories,
            daily_target_protein=daily_target_protein,
            daily_target_carbs=daily_target_carbs,
            daily_target_fats=daily_target_fats,
            meals=meals,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/create_meal_plan.html",
            {
                "request": request,
                "current_user": current_user,
                "meal_plan": {
                    "plan_name": plan_name,
                    "goal": goal,
                    "daily_target_calories": daily_target_calories,
                    "daily_target_protein": daily_target_protein,
                    "daily_target_carbs": daily_target_carbs,
                    "daily_target_fats": daily_target_fats,
                    "meals_json": meals_json,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not meal_plan:
        return RedirectResponse(
            url="/fitness/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/meal-plans/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/meal-plans/list", response_class=HTMLResponse)
def meal_plan_list_page(request: Request, current_user=Depends(require_user)):
    meal_plan_service = MealPlanService()
    meal_plans = meal_plan_service.list_meal_plans(current_user)
    return templates.TemplateResponse(
        "fitness/meal_plans_list.html",
        {
            "request": request,
            "current_user": current_user,
            "meal_plans": meal_plans,
        },
    )


@router.post("/meal-plans/{identifier}/start")
def start_meal_plan_day(identifier: str, current_user=Depends(require_user)):
    meal_plan_service = MealPlanService()
    try:
        meal_plan_service.start_meal_plan_day(current_user, identifier)
    except ValueError:
        return RedirectResponse(
            url="/fitness/meal-plans/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/meal-plans/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/nutrition/{calculation_date}", response_class=HTMLResponse)
def nutrition_summary_page(
    request: Request,
    calculation_date: str,
    current_user=Depends(require_user),
):
    nutrition_service = NutritionSummaryService()
    try:
        summary = nutrition_service.calculate_daily_nutrition_summary(current_user, calculation_date)
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/nutrition_summary.html",
            {
                "request": request,
                "current_user": current_user,
                "calculation_date": calculation_date,
                "summary": None,
                "error": str(exc),
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        "fitness/nutrition_summary.html",
        {
            "request": request,
            "current_user": current_user,
            "calculation_date": calculation_date,
            "summary": summary,
            "error": None,
        },
    )


@router.get("/workouts", response_class=HTMLResponse)
def create_workout_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "fitness/create_workout.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/workouts", response_class=HTMLResponse)
def create_workout_submit(
    request: Request,
    current_user=Depends(require_user),
    session_name: str = Form(...),
    workout_blocks_json: str = Form(...),
    notes: str = Form(""),
):
    workout_service = WorkoutSessionService()
    try:
        workout_blocks = _parse_json_list(workout_blocks_json, "workout_blocks")
        session = workout_service.log_session(
            current_user=current_user,
            session_name=session_name,
            workout_blocks=workout_blocks,
            notes=notes,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/create_workout.html",
            {
                "request": request,
                "current_user": current_user,
                "workout": {
                    "session_name": session_name,
                    "workout_blocks_json": workout_blocks_json,
                    "notes": notes,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not session:
        return RedirectResponse(
            url="/fitness/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/workouts/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/workouts/list", response_class=HTMLResponse)
def workout_list_page(request: Request, current_user=Depends(require_user)):
    workout_repository = Workout_Repository()
    workouts = workout_repository.list_workout_entries(current_user)
    return templates.TemplateResponse(
        "fitness/workouts_list.html",
        {
            "request": request,
            "current_user": current_user,
            "workouts": workouts,
        },
    )


@router.get("/routines", response_class=HTMLResponse)
def create_routine_page(request: Request, current_user=Depends(require_user)):
    return templates.TemplateResponse(
        "fitness/create_routine.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/routines", response_class=HTMLResponse)
def create_routine_submit(
    request: Request,
    current_user=Depends(require_user),
    name: str = Form(...),
    days_json: str = Form(...),
):
    routine_service = RoutineService()
    try:
        days = _parse_json_list(days_json, "days")
        routine = routine_service.create_routine(
            current_user=current_user,
            name=name,
            days=days,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "fitness/create_routine.html",
            {
                "request": request,
                "current_user": current_user,
                "routine": {
                    "name": name,
                    "days_json": days_json,
                },
                "error": str(exc),
            },
            status_code=400,
        )

    if not routine:
        return RedirectResponse(
            url="/fitness/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/routines/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/routines/list", response_class=HTMLResponse)
def routine_list_page(request: Request, current_user=Depends(require_user)):
    routine_service = RoutineService()
    routines = routine_service.list_routines(current_user)
    return templates.TemplateResponse(
        "fitness/routines_list.html",
        {
            "request": request,
            "current_user": current_user,
            "routines": routines,
        },
    )


@router.get("/routines/{identifier}", response_class=HTMLResponse)
def routine_detail_page(
    request: Request,
    identifier: str,
    current_user=Depends(require_user),
):
    routine_service = RoutineService()
    routine = routine_service.get_routine(current_user, identifier)
    if not routine:
        return RedirectResponse(
            url="/fitness/routines/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "fitness/routine_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "routine": routine,
        },
    )


@router.post("/routines/session-from-routine", response_class=HTMLResponse)
def session_from_routine_submit(
    request: Request,
    current_user=Depends(require_user),
    day_name: str = Form(...),
    routine_name: str = Form(""),
):
    routine_service = RoutineService()
    try:
        session = routine_service.build_session_from_routine(
            current_user=current_user,
            day_name=day_name,
            routine_name=routine_name or None,
        )
    except ValueError as exc:
        routines = routine_service.list_routines(current_user)
        return templates.TemplateResponse(
            "fitness/routines_list.html",
            {
                "request": request,
                "current_user": current_user,
                "routines": routines,
                "error": str(exc),
            },
            status_code=400,
        )

    if not session:
        return RedirectResponse(
            url="/fitness/workouts/list",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/fitness/workouts/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )
