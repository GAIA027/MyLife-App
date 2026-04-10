import json
import logging
from pathlib import Path
from typing import Any

from app.modules.MyLife_Tracker import (
    ensure_current_user,
    generate_id,
    now_dubai,
    validate_date_input,
)

logger = logging.getLogger("mylife_fitness")

fitness_database = Path(__file__).resolve().parents[2] / "data" / "fitness.json"


def load_fitness_database() -> dict[str, Any]:
    if not fitness_database.exists():
        return {
            "user_fitness_data": {
                "meal_system": {
                    "daily_calorie": 0,
                },
                "meal_system_by_user": {},
            },
            "meal_log": [],
            "workout_sessions": [],
            "routines": [],
            "meal_plans": [],
            "started_meal_plan_days": [],
        }

    with open(fitness_database, "r") as fitness_file:
        return json.load(fitness_file)


def save_fitness_database(fitness_data: dict[str, Any]) -> None:
    with open(fitness_database, "w") as fitness_file:
        json.dump(fitness_data, fitness_file, indent=4)


def _current_user_id(current_user: dict | None) -> str | None:
    current_user = ensure_current_user(current_user)
    if not current_user:
        return None
    return str(current_user.get("id"))


def _fitness_record_belongs_to_user(record: dict[str, Any], current_user_id: str) -> bool:
    record_user_id = record.get("user_id")
    return record_user_id is None or str(record_user_id) == current_user_id


def _matches_identifier(record: dict[str, Any], identifier: str, *keys: str) -> bool:
    for key in keys:
        value = str(record.get(key, "")).strip().lower()
        if value and value == identifier.strip().lower():
            return True
    return False


class CalorieTracker:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database):
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def set_calorie_goal(self, current_user: dict | None, goal: int) -> None:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")

        user_fitness_data = fitness_data.setdefault("user_fitness_data", {})
        meal_system = user_fitness_data.setdefault("meal_system", {})
        meal_system_by_user = user_fitness_data.setdefault("meal_system_by_user", {})
        meal_system_by_user[current_user_id] = {
            "daily_calorie": int(goal),
            "user_id": current_user_id,
        }
        meal_system.setdefault("daily_calorie", int(goal))
        self.save_fitness_data(fitness_data)

    def get_daily_calorie_goal(self, current_user: dict | None) -> int:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        user_fitness_data = fitness_data.get("user_fitness_data", {})
        meal_system_by_user = user_fitness_data.get("meal_system_by_user", {})
        if current_user_id and meal_system_by_user.get(current_user_id):
            return int(meal_system_by_user[current_user_id].get("daily_calorie", 0))
        meal_system = user_fitness_data.get("meal_system", {})
        return int(meal_system.get("daily_calorie", 0))

    def get_consumed_calories_for_day(self, current_user: dict | None, target_date: str) -> int:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return 0

        consumed_today = 0
        for meal in fitness_data.get("meal_log", []):
            if not _fitness_record_belongs_to_user(meal, current_user_id):
                continue
            if meal.get("completion_date") == target_date:
                consumed_today += int(meal.get("calories", 0))
        return consumed_today

    def get_remaining_calories_for_day(self, current_user: dict | None, target_date: str) -> int:
        return self.get_daily_calorie_goal(current_user) - self.get_consumed_calories_for_day(current_user, target_date)

    def show_daily_calorie(self, current_user: dict | None, target_date: str) -> dict[str, int]:
        return {
            "daily_goal": self.get_daily_calorie_goal(current_user),
            "consumed_today": self.get_consumed_calories_for_day(current_user, target_date),
            "remaining_calories": self.get_remaining_calories_for_day(current_user, target_date),
        }


class MealTracker:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database) -> None:
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def add_meal(
        self,
        current_user: dict | None,
        meal_name: str,
        meal_type: str,
        calorie_in_meal: int,
        completetion_date: str,
        time_of_log: str | None = None,
        notes: str = "",
        protein: int = 0,
        carbs: int = 0,
        fats: int = 0,
    ) -> dict[str, Any]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")

        meal = {
            "id": generate_id(),
            "user_id": current_user_id,
            "meal": meal_name,
            "meal_name": meal_name,
            "meal type": meal_type,
            "meal_type": meal_type,
            "calories": int(calorie_in_meal),
            "protein": int(protein),
            "carbs": int(carbs),
            "fats": int(fats),
            "time_of_log": time_of_log or now_dubai(),
            "completion_date": completetion_date,
            "notes": notes,
        }
        fitness_data.setdefault("meal_log", []).append(meal)
        self.save_fitness_data(fitness_data)
        logger.info("Meal added successfully")
        return meal

    def view_meal(self, current_user: dict | None) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        return [
            meal
            for meal in fitness_data.get("meal_log", [])
            if meal and _fitness_record_belongs_to_user(meal, current_user_id)
        ]

    def find_meal(self, current_user: dict | None, meal_choice: str) -> dict[str, Any] | None:
        meal_log = self.view_meal(current_user)
        if meal_choice.isdigit():
            meal_index = int(meal_choice) - 1
            if 0 <= meal_index < len(meal_log):
                return meal_log[meal_index]
            return None

        for meal in meal_log:
            if _matches_identifier(meal, meal_choice, "meal", "meal_name"):
                return meal
        return None

    def update_meal(
        self,
        current_user: dict | None,
        meal_id: str,
        updated_meal_name: str,
        updated_meal_type: str,
        updated_meal_in_calorie: int,
        updated_time_of_log: str,
        updated_completiton_date: str,
        updataed_notes: str,
        updated_protein: int = 0,
        updated_carbs: int = 0,
        updated_fats: int = 0,
    ) -> dict[str, Any] | None:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return None

        for meal in fitness_data.get("meal_log", []):
            if str(meal.get("id")) != str(meal_id):
                continue
            if not _fitness_record_belongs_to_user(meal, current_user_id):
                continue
            meal.update(
                {
                    "meal": updated_meal_name,
                    "meal_name": updated_meal_name,
                    "meal type": updated_meal_type,
                    "meal_type": updated_meal_type,
                    "calories": int(updated_meal_in_calorie),
                    "protein": int(updated_protein),
                    "carbs": int(updated_carbs),
                    "fats": int(updated_fats),
                    "time_of_log": updated_time_of_log,
                    "completion_date": updated_completiton_date,
                    "notes": updataed_notes,
                }
            )
            self.save_fitness_data(fitness_data)
            logger.info("Meal updated successfully")
            return meal
        return None

    def delete_meal(self, current_user: dict | None, meal_id: str) -> bool:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return False

        updated_meal_log = [
            meal
            for meal in fitness_data.get("meal_log", [])
            if not (
                str(meal.get("id")) == str(meal_id)
                and _fitness_record_belongs_to_user(meal, current_user_id)
            )
        ]

        if len(updated_meal_log) == len(fitness_data.get("meal_log", [])):
            return False

        fitness_data["meal_log"] = updated_meal_log
        self.save_fitness_data(fitness_data)
        logger.info("Meal deleted successfully")
        return True


class MealPlanService:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database) -> None:
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def create_meal_plan(
        self,
        current_user: dict | None,
        plan_name: str,
        goal: str,
        daily_target_calories: int,
        daily_target_protein: int,
        daily_target_carbs: int,
        daily_target_fats: int,
        meals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")
        if not meals:
            raise ValueError("Meal plan must contain at least one meal slot")

        fitness_data = self.load_fitness_data()
        existing_plans = [
            plan
            for plan in fitness_data.get("meal_plans", [])
            if _fitness_record_belongs_to_user(plan, current_user_id)
        ]
        for plan in existing_plans:
            if _matches_identifier(plan, plan_name, "plan_name", "meal_plan_name"):
                raise ValueError("A meal plan with this name already exists")

        meal_plan = {
            "id": generate_id(),
            "user_id": current_user_id,
            "entry_type": "meal_plan",
            "plan_name": plan_name.strip(),
            "goal": goal,
            "daily_target_calories": int(daily_target_calories),
            "daily_target_protein": int(daily_target_protein),
            "daily_target_carbs": int(daily_target_carbs),
            "daily_target_fats": int(daily_target_fats),
            "meals": meals,
            "created_at": now_dubai(),
            "updated_at": now_dubai(),
        }
        fitness_data.setdefault("meal_plans", []).append(meal_plan)
        self.save_fitness_data(fitness_data)
        return meal_plan

    def list_meal_plans(self, current_user: dict | None) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        return [
            plan
            for plan in fitness_data.get("meal_plans", [])
            if _fitness_record_belongs_to_user(plan, current_user_id)
        ]

    def get_meal_plan(self, current_user: dict | None, identifier: str) -> dict[str, Any] | None:
        meal_plan_log = self.list_meal_plans(current_user)
        if identifier.isdigit():
            index = int(identifier) - 1
            if 0 <= index < len(meal_plan_log):
                return meal_plan_log[index]
            return None

        for plan in meal_plan_log:
            if _matches_identifier(plan, identifier, "id", "plan_name", "meal_plan_name"):
                return plan
        return None

    def start_meal_plan_day(self, current_user: dict | None, identifier: str) -> dict[str, Any]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")

        selected_meal_plan = self.get_meal_plan(current_user, identifier)
        if not selected_meal_plan:
            raise ValueError("Meal plan not found")

        started_meal_day = {
            "id": generate_id(),
            "user_id": current_user_id,
            "entry_type": "started_meal_plan_day",
            "source_plan_id": selected_meal_plan.get("id"),
            "plan_name": selected_meal_plan.get("plan_name"),
            "goal": selected_meal_plan.get("goal"),
            "date_started": now_dubai().split("T")[0],
            "started_at": now_dubai(),
            "daily_target_calories": selected_meal_plan.get("daily_target_calories"),
            "daily_target_protein": selected_meal_plan.get("daily_target_protein"),
            "daily_target_carbs": selected_meal_plan.get("daily_target_carbs"),
            "daily_target_fats": selected_meal_plan.get("daily_target_fats"),
            "meals": selected_meal_plan.get("meals", []),
        }
        fitness_data.setdefault("started_meal_plan_days", []).append(started_meal_day)
        self.save_fitness_data(fitness_data)
        return started_meal_day


class NutritionSummaryService:
    def __init__(self, data_loader=load_fitness_database) -> None:
        self.load_fitness_data = data_loader

    def calculate_daily_nutrition_summary(
        self,
        current_user: dict | None,
        calculation_date: str,
    ) -> dict[str, Any] | None:
        if not validate_date_input(calculation_date):
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return None

        fitness_data = self.load_fitness_data()
        meal_log = fitness_data.get("meal_log", [])
        matching_meals = [
            meal
            for meal in meal_log
            if meal.get("completion_date") == calculation_date
            and _fitness_record_belongs_to_user(meal, current_user_id)
        ]
        if not matching_meals:
            return None

        calorie_tracker = CalorieTracker(data_loader=self.load_fitness_data)
        total_calories = calorie_tracker.get_consumed_calories_for_day(current_user, calculation_date)
        remaining_calories = calorie_tracker.get_remaining_calories_for_day(current_user, calculation_date)
        total_protein = sum(int(meal.get("protein", 0)) for meal in matching_meals)
        total_carbs = sum(int(meal.get("carbs", 0)) for meal in matching_meals)
        total_fats = sum(int(meal.get("fats", 0)) for meal in matching_meals)

        meal_plan_days = [
            meal_plan_day
            for meal_plan_day in fitness_data.get("started_meal_plan_days", [])
            if _fitness_record_belongs_to_user(meal_plan_day, current_user_id)
        ]
        matching_plan_day = next(
            (meal_plan_day for meal_plan_day in meal_plan_days if meal_plan_day.get("date_started") == calculation_date),
            None,
        )

        summary = {
            "date": calculation_date,
            "calories_consumed": total_calories,
            "protein_consumed": total_protein,
            "carbs_consumed": total_carbs,
            "fats_consumed": total_fats,
            "daily_calorie_goal": calorie_tracker.get_daily_calorie_goal(current_user),
            "remaining_calories": remaining_calories,
        }

        if matching_plan_day:
            summary.update(
                {
                    "remaining_protein": int(matching_plan_day.get("daily_target_protein", 0)) - total_protein,
                    "remaining_carbs": int(matching_plan_day.get("daily_target_carbs", 0)) - total_carbs,
                    "remaining_fats": int(matching_plan_day.get("daily_target_fats", 0)) - total_fats,
                }
            )

        return summary


class Workout_Repository:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database):
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def log_workout_entry(self, current_user: dict | None, entry_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []

        workout_sessions = fitness_data.setdefault("workout_sessions", [])
        for entry in entry_list:
            entry.setdefault("user_id", current_user_id)
            workout_sessions.append(entry)
        self.save_fitness_data(fitness_data)
        return entry_list

    def list_workout_entries(self, current_user: dict | None) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        return [
            entry
            for entry in fitness_data.get("workout_sessions", [])
            if _fitness_record_belongs_to_user(entry, current_user_id)
        ]

    def list_worout_entries(self, current_user: dict | None) -> list[dict[str, Any]]:
        return self.list_workout_entries(current_user)

    def get_entry(self, current_user: dict | None, entry_id: str) -> dict[str, Any] | None:
        for entry in self.list_workout_entries(current_user):
            if str(entry.get("id")) == str(entry_id):
                return entry
        return None


class WorkoutSessionService:
    def create_session(
        self,
        user_id: str,
        name: str,
        workout_details: list[dict[str, Any]],
        notes: str,
    ) -> dict[str, Any]:
        session = {
            "id": generate_id(),
            "user_id": user_id,
            "entry_type": "session",
            "name": name.strip(),
            "blocks": workout_details,
            "notes": notes,
            "created_at": now_dubai(),
            "updated_at": now_dubai(),
        }
        self.validate_session(session)
        return session

    def add_strength_exercise(self, label: str, name: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "block_type": "strength",
            "label": label,
            "name": name,
            "exercises": exercises,
        }

    def add_cardio_exercise(self, label: str, minutes: int, intensity: str) -> dict[str, Any]:
        return {
            "block_type": "cardio",
            "label": label,
            "minutes": int(minutes),
            "intensity": intensity,
        }

    def add_exercise(self, name: str, sets: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "name": name,
            "sets": sets,
        }

    def validate_session(self, session: dict[str, Any]) -> None:
        if not session.get("name"):
            raise ValueError("Session name is required")
        if not session.get("blocks"):
            raise ValueError("Session must have at least one block")

    def format_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": session.get("id"),
            "name": session.get("name"),
            "block_count": len(session.get("blocks", [])),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
        }

    def log_session(
        self,
        current_user: dict | None,
        session_name: str,
        workout_blocks: list[dict[str, Any]],
        notes: str = "",
    ) -> dict[str, Any]:
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")

        session = self.create_session(
            user_id=current_user_id,
            name=session_name,
            workout_details=workout_blocks,
            notes=notes,
        )
        Workout_Repository().log_workout_entry(current_user, [session])
        return session


class RoutineService:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database):
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def create_routine(self, current_user: dict | None, name: str, days: list[dict[str, Any]]) -> dict[str, Any]:
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")
        if not name.strip():
            raise ValueError("Routine name is required")
        if not days:
            raise ValueError("Routine must contain at least one day")

        routine = {
            "id": generate_id(),
            "user_id": current_user_id,
            "entry_type": "routine",
            "name": name.strip(),
            "days": days,
            "created_at": now_dubai(),
            "updated_at": now_dubai(),
        }
        fitness_data = self.load_fitness_data()
        fitness_data.setdefault("routines", []).append(routine)
        self.save_fitness_data(fitness_data)
        return routine

    @staticmethod
    def add_routine_day(day_name: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
        if not day_name.strip():
            raise ValueError("Day name is required")
        return {
            "day_name": day_name.strip(),
            "blocks": blocks,
        }

    @staticmethod
    def format_routine(routine: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": routine.get("id"),
            "name": routine.get("name"),
            "day_count": len(routine.get("days", [])),
            "created_at": routine.get("created_at"),
            "updated_at": routine.get("updated_at"),
        }

    def list_routines(self, current_user: dict | None) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        return [
            routine
            for routine in fitness_data.get("routines", [])
            if _fitness_record_belongs_to_user(routine, current_user_id)
        ]

    def get_routine(self, current_user: dict | None, identifier: str) -> dict[str, Any] | None:
        routines = self.list_routines(current_user)
        if identifier.isdigit():
            index = int(identifier) - 1
            if 0 <= index < len(routines):
                return routines[index]
            return None

        for routine in routines:
            if _matches_identifier(routine, identifier, "id", "name"):
                return routine
        return None

    def build_session_from_routine(
        self,
        current_user: dict | None,
        day_name: str,
        routine_name: str | None = None,
    ) -> dict[str, Any]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            raise ValueError("Current user not found")

        routines = [
            routine
            for routine in fitness_data.get("routines", [])
            if _fitness_record_belongs_to_user(routine, current_user_id)
        ]
        matching_routine = None
        matching_day = None

        for routine in routines:
            if routine_name and routine.get("name", "").strip().lower() != routine_name.strip().lower():
                continue
            for day in routine.get("days", []):
                if day.get("day_name", "").strip().lower() == day_name.strip().lower():
                    matching_routine = routine
                    matching_day = day
                    break
            if matching_day:
                break

        if not matching_routine or not matching_day:
            raise ValueError("Routine day not found")

        session = WorkoutSessionService().create_session(
            user_id=current_user_id,
            name=f"{matching_routine.get('name')} - {matching_day.get('day_name')}",
            workout_details=matching_day.get("blocks", []),
            notes=f"Built from routine: {matching_routine.get('name')}",
        )
        fitness_data.setdefault("workout_sessions", []).append(session)
        self.save_fitness_data(fitness_data)
        return session
