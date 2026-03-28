import json
from pathlib import Path
from app.modules.MyLife_Tracker import *

fitness_database = Path(__file__).resolve().parents[2] / "data" / "fitness.json"
def load_fitness_database():
    if not fitness_database.exists():
        return {
            "user_fitness_data": {
                "meal_system": {
                    "daily_calorie": 0
                },
                "meal_system_by_user": {}
            },
            "meal_log" : [],
            "workout_sessions" : [],
            "routines": [],
            "meal_plans" : [],
            "started_meal_plan_days": []
        }
    with open(fitness_database, "r") as fitness_file:
        return json.load(fitness_file) 

def save_fitness_database(fitness_data):
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
class CalorieTracker:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database):
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver
    
    def set_calorie_goal(self, current_user: dict | None, goal : int):
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

    def get_consumed_calories_for_day(self, current_user: dict | None, target_date : str) -> int:
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
        daily_goal = self.get_daily_calorie_goal(current_user)
        consumed_today = self.get_consumed_calories_for_day(current_user, target_date)
        return daily_goal - consumed_today

    def show_daily_calorie(self, current_user: dict | None, target_date: str):
        print(f"Daily goal : {self.get_daily_calorie_goal(current_user)} cal")
        print(f"Consumed today : {self.get_consumed_calories_for_day(current_user, target_date)} cal")
        print(f"Remaining calories for today : {self.get_remaining_calories_for_day(current_user, target_date)} cal")
class MealTracker:
    def __init__(self, data_saver=save_fitness_database, data_loader=load_fitness_database) -> None:
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def add_meal(self,
                current_user : dict | None,
                meal_name : str,
                meal_type : str,
                calorie_in_meal : int,
                completetion_date : str,
                time_of_log : str | None = None,
                notes : str = ""
                ) -> dict[str, Any]:

                fitness_data = self.load_fitness_data()
                current_user_id = _current_user_id(current_user)
                if not current_user_id:
                    raise ValueError("Current user not found")
                meal = {
                "id" : generate_id(),
                "user_id" : current_user_id,
                "meal" : meal_name,
                "meal type" : meal_type,
                "calories" : int(calorie_in_meal),
                "time_of_log" : time_of_log or now_dubai(),
                "completion_date" : completetion_date,
                "notes" : notes
                }
                fitness_data.setdefault("meal_log", []).append(meal)
                self.save_fitness_data(fitness_data)
                logging.info("Meal added successfully")
                return meal

    def find_meal(self, current_user: dict | None, meal_choice: str) -> dict[str, Any] | None:
        meal_log = self.view_meal(current_user)

        if meal_choice.isdigit():
            meal_index = int(meal_choice) - 1
            if 0 <= meal_index < len(meal_log):
                return meal_log[meal_index]
            return None

        meal_choice_normalized = meal_choice.strip().lower()
        for meal in meal_log:
            meal_name = meal.get("meal", meal.get("meal_name", "")).strip().lower()
            if meal_name == meal_choice_normalized:
                return meal
        return None

    def update_meal(self,
                    current_user : dict | None,
                    meal_id : str,
                    updated_meal_name : str,
                    updated_meal_type : str,
                    updated_meal_in_calorie : int,
                    updated_time_of_log : str,
                    updated_completiton_date : str,
                    updataed_notes : str  ) -> dict[str, Any] | None:
                    fitness_data = self.load_fitness_data()
                    current_user_id = _current_user_id(current_user)
                    if not current_user_id:
                        return None
                    for meal in fitness_data.get("meal_log", []):
                        if str(meal.get("id")) == str(meal_id) and _fitness_record_belongs_to_user(meal, current_user_id):
                            meal.update({
                            "meal" : updated_meal_name,
                            "meal type" : updated_meal_type,
                            "calories" : int(updated_meal_in_calorie),
                            "time_of_log" : updated_time_of_log,
                            "completion_date" : updated_completiton_date,
                            "notes" : updataed_notes
                        })
                        logging.info("Meal updated successfully")
                        self.save_fitness_data(fitness_data)
                        return meal
                    return None

    def delete_meal(self, current_user : dict | None, meal_id : str) -> bool:
         fitness_data = self.load_fitness_data()
         current_user_id = _current_user_id(current_user)
         if not current_user_id:
              return False

         meal_log = [
             meal for meal in fitness_data.get("meal_log", [])
             if _fitness_record_belongs_to_user(meal, current_user_id)
         ]

         updated_meal_log = [
             meal for meal in fitness_data.get("meal_log", [])
             if not (str(meal.get("id")) == str(meal_id) and _fitness_record_belongs_to_user(meal, current_user_id))
         ]

         if len(updated_meal_log) == len(fitness_data.get("meal_log", [])):
              return False

         fitness_data["meal_log"] = updated_meal_log
         self.save_fitness_data(fitness_data)
         logging.info("Meal deleted successfully")
         return True

    def view_meal(self, current_user : dict | None):
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        return [meal for meal in fitness_data.get("meal_log", []) if meal and _fitness_record_belongs_to_user(meal, current_user_id)]


def _log_meal(current_user : ensure_current_user):
    if not current_user:
        print("Current user not found")
        return

    meal_tracker = MealTracker()
    while True:
        meal_name = input("\nEnter meal name : ").strip().lower()
        if not meal_name:
            print("\nMeal name cannot be empty")
            continue
        if len(meal_name) < 2:
            print("\nMeal name cannot be less than two characters")
            continue
        break

    while True:
        meal_type = input("\nEnter meal type (breakfast/lunch/dinner/snack) : ").strip().lower()
        if not meal_type:
            print("Meal type cannot be empty")
            continue
        meal_type_registry : list[str] = [
            "breakfast",
            "lunch",
            "dinner",
            "snack"
            ]
        if meal_type not in meal_type_registry:
                print(f"\nMeal type should be one of the following {meal_type_registry}")
                continue
        break
        
    while True:
        calories = input("\nEnter calories for this meal : ").strip()
        if not calories:
            print("Calories cannot be empty")
            continue
        if not calories.isdigit():
            print("Calories must be a number")
            continue
        calories = int(calories)
        if calories <= 0:
            print("Calories must be above 0")
            continue
        break
        
    while True:
        completion_date = input("\nEnter a completion date (YYYY-MM-DD) or press enter for today : ").strip()
        if not completion_date:
            completion_date = now_dubai().split("T")[0]
        try:
            datetime.strptime(completion_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format")
            continue
        break

    notes = input("\nEnter notes (optional) : ").strip()

    meal = meal_tracker.add_meal(
        current_user=current_user,
        meal_name=meal_name,
        meal_type=meal_type,
        calorie_in_meal=calories,
        completetion_date=completion_date,
        time_of_log=now_dubai(),
        notes=notes,
    )
    print("\nMeal logged successfully")
    logging.info(f"\nMeal logged successfully for {current_user}")
    print("\nMeal summary")
    calorie_tracker = CalorieTracker()
    print(f"\nMeal name : {meal.get('meal', meal_name)}")
    print(f"\nCalories for meal : {meal.get('calories', calories)}")
    print(f"\nDaily goal : {calorie_tracker.get_daily_calorie_goal(current_user)} calories")
    print(f"\nRemaining today : {calorie_tracker.get_remaining_calories_for_day(current_user, completion_date)} calories")
    print(f"\n consumed today : {calorie_tracker.get_consumed_calories_for_day(current_user, completion_date)} calories ")
        
def _view_meals(current_user : ensure_current_user) -> list[dict[str, Any]]:
    if not current_user:
        print("Current user not found")
        return

    meal_tracker = MealTracker()
    meal_log = meal_tracker.view_meal(current_user)
    if not meal_log:
        print("meal log not found")
        return []

    print("===Meal history===")
    for index, meal in enumerate(meal_log, start=1):
        print(
            f"{index}. {meal.get('id')} | {meal.get('meal_name', meal.get('meal'))} | "
            f"{meal.get('meal_type', meal.get('meal type'))} | {meal.get('calories')} | "
            f"{meal.get('completion_date')}"
        )
    return meal_log 
    
def _view_meal_details(current_user : ensure_current_user):
    if not current_user:
        print("Current user not found")
        return
    meal_tracker = MealTracker()
    meal_log = meal_tracker.view_meal(current_user)
    if not meal_log:
        print("meal log not found")
        return []
    
    while True:
        meal_choice = input("Enter a meal name or number : ").strip()
        selected_meal = meal_tracker.find_meal(current_user, meal_choice)

        if selected_meal:
            break

        print("meal not found. Please enter a valid meal name or 3-digit number.") 
    
    print("\n=== Meal Details ===")
    print(f"\nMeal ID: {selected_meal.get('id')}")
    print(f"\nMeal Name: {selected_meal.get('meal_name', selected_meal.get('meal'))}")
    print(f"\nMeal Type: {selected_meal.get('meal_type', selected_meal.get('meal type'))}")
    print(f"\nCalories: {selected_meal.get('calories')}")
    print(f"\nCompletion Date: {selected_meal.get('completion_date')}")
    print(f"\nTime of Log: {selected_meal.get('time_of_log')}")
    print(f"\nNotes: {selected_meal.get('notes')}")

    return selected_meal

    
def create_meal_plan(current_user : ensure_current_user):
    if not current_user:
        print("Current user not found")
        return
    
    fitness_data = load_fitness_database()
    current_user_id = _current_user_id(current_user)
    if not current_user_id:
        print("Current user not found")
        return
    while True:
        meal_plan_name = input("\nEnter meal plan name : ").strip()
        if not meal_plan_name:
            print("Name required")
            continue

        if len(meal_plan_name) <= 2:
            print("Name has to be at least 3 characters")
            continue

        duplicate_found = False
        for plan in fitness_data.get("meal_plans", []):
            if not _fitness_record_belongs_to_user(plan, current_user_id):
                continue
            existing_name = plan.get("plan_name", plan.get("meal_plan_name", "")).strip().lower()
            if existing_name == meal_plan_name.lower():
                duplicate_found = True
                break

        if duplicate_found:
            print("A meal plan with this name already exists")
            continue
        break

    allowed_options: list[str] = [
        "fat loss",
        "maintenance",
        "muscle gain"
    ]
    while True:
        plan_goal = input("\nGoal (fat loss / maintenance / muscle gain) : ").strip().lower()
        if not plan_goal:
            print("Goal required")
            continue

        if plan_goal not in allowed_options:
            print(f"Plan goal should be one of the following {allowed_options}")
            continue
        break

    while True:
        daily_target_calories = input("\nDaily Target Calories : ").strip()
        if not daily_target_calories:
            print("Target calories required")
            continue

        if not daily_target_calories.isdigit():
            print("Calories must be a number")
            continue

        daily_target_calories = int(daily_target_calories)
        if daily_target_calories <= 0:
            print("Daily calories must be above zero")
            continue
        break

    while True:
        daily_target_proteins = input("\nDaily Target Proteins : ").strip()
        if not daily_target_proteins:
            print("Target proteins required")
            continue

        if not daily_target_proteins.isdigit():
            print("Target proteins must be a number")
            continue
        
        daily_target_proteins = int(daily_target_proteins)
        break

    while True:
        daily_target_carbs = input("\nDaily target carbs : ").strip()
        if not daily_target_carbs:
            print("Target carbs is required")
            continue

        if not daily_target_carbs.isdigit():
            print("Carbs must be a number")
            continue

        daily_target_carbs = int(daily_target_carbs)
        if daily_target_carbs <= 0:
            print("Daily carbs must be above zero")
            continue
        break

    while True:
        daily_target_fats = input("\nDaily target fats : ").strip()
        if not daily_target_fats:
            print("Target fats is required")
            continue

        if not daily_target_fats.isdigit():
            print("Target fats must be a number")
            continue

        daily_target_fats = int(daily_target_fats)
        if daily_target_fats <= 0:
            print("Daily fats must be above zero")
            continue
        break
    
    # line(380 - 430 )This needs to be checked (Potential bad UX for user)
    meals = []
    meal_type_registry = ["breakfast", "lunch", "dinner", "snack"]

    while True:
        while True:
            meal_type = input("\nEnter meal type for this slot (breakfast/lunch/dinner/snack) : ").strip().lower()
            if not meal_type:
                print("Meal type required")
                continue

            if meal_type not in meal_type_registry:
                print(f"Meal type must be one of the following: {meal_type_registry}")
                continue
            break

        foods = []
        while True:
            food_item = input("Enter food item for this meal slot (or type 'done') : ").strip()
            if not food_item:
                print("Food item cannot be empty")
                continue

            if food_item.lower() == "done":
                if not foods:
                    print("Add at least one food item before finishing this meal slot")
                    continue
                break

            foods.append(food_item)

        meal_notes = input("Enter notes for this meal slot (optional) : ").strip()
        meals.append({
            "meal_type": meal_type,
            "foods": foods,
            "notes": meal_notes
        })

        add_another_meal = input("\nAdd another meal slot? (y/n) : ").strip().lower()
        while add_another_meal not in ["y", "n"]:
            print("Enter 'y' or 'n'")
            add_another_meal = input("Add another meal slot? (y/n) : ").strip().lower()

        if add_another_meal == "n":
            break

    if not meals:
        print("Meal plan must contain at least one meal slot")
        return

    meal_plan = {
        "id": generate_id(),
        "user_id": current_user_id,
        "entry_type": "meal_plan",
        "plan_name": meal_plan_name,
        "goal": plan_goal,
        "daily_target_calories": daily_target_calories,
        "daily_target_protein": daily_target_proteins,
        "daily_target_carbs": daily_target_carbs,
        "daily_target_fats": daily_target_fats,
        "meals": meals,
        "created_at": now_dubai(),
        "updated_at": now_dubai()
    }

    fitness_data.setdefault("meal_plans", []).append(meal_plan)
    save_fitness_database(fitness_data)

    print("\nMeal plan created successfully")
    print(f"Plan name: {meal_plan_name}")
    print(f"Goal: {plan_goal}")
    print(
        f"Targets: {daily_target_calories} cal | "
        f"{daily_target_proteins} protein | "
        f"{daily_target_carbs} carbs | "
        f"{daily_target_fats} fats"
    )
    print(f"Meal slots added: {len(meals)}")

def view_meal_plans(current_user : ensure_current_user) -> list[dict[str, Any]]:
    if not current_user:
        print("Current user not found")
        return
    
    fitness_data = load_fitness_database()
    current_user_id = _current_user_id(current_user)
    meal_plan_log = [plan for plan in fitness_data.get("meal_plans", []) if _fitness_record_belongs_to_user(plan, current_user_id)]
    if not meal_plan_log:
        print("You do not have any meal plan")
        return []
    
    print(f"===Meal plans===")

    for index, meal_plan in enumerate(meal_plan_log, start=1):
        print(
            f"\n{index}. {meal_plan.get('plan_name')} | {meal_plan.get('goal')} | "
            f"{meal_plan.get('daily_target_calories')} cal | "
            f"{meal_plan.get('daily_target_protein')} protein | "
            f"{meal_plan.get('daily_target_carbs')} carbs | "
            f"{meal_plan.get('daily_target_fats')} fats"
        )
    return meal_plan_log

def view_meal_plan_structure(current_user : ensure_current_user):
    if not current_user:
        print("Current user not found")
        return
    fitness_data = load_fitness_database()
    current_user_id = _current_user_id(current_user)
    meal_plan_log = [plan for plan in fitness_data.get("meal_plans", []) if _fitness_record_belongs_to_user(plan, current_user_id)]
    if not meal_plan_log:
        print("Meal plan log not found")
        return []
    
    while True:
        plan_choice = input("\nEnter a meal plan name or number").strip()
        if not plan_choice:
            print("\nEnter a name or number to view a meal plan")
            continue
        selected_plan = None

        if plan_choice.isdigit():
            plan_number = int(plan_choice)
            plan_index = plan_number - 1

            if 0 <= plan_index < len(meal_plan_log):
                selected_plan = meal_plan_log[plan_index]
        
        else:
            for plan in meal_plan_log:
                if plan.get("plan_name", "").strip().lower() == plan_choice.lower():
                    selected_plan = plan
        
        if selected_plan:
            break

        print("plan name not found. Please enter a valid plan name or number")
    
    print("\n===meal plan details===")
    print(f"Meal plan ID : {selected_plan.get('id')}")
    print(f"entry type : {selected_plan.get('entry_type')}")
    print(f"Meal plan name : {selected_plan.get('plan_name')}")
    print(f"Goal : {selected_plan.get('goal')}")
    print(f"Daily Target calories : {selected_plan.get('daily_target_calories')} calories")
    print(f"Daily Target Carbs : {selected_plan.get('daily_target_carbs')} carbs")
    print(f"Daily Target Proteins : {selected_plan.get('daily_target_protein')} proteins")
    print(f"Daily Target fats : {selected_plan.get('daily_target_fats')} fats")
    print(f"Created at : {selected_plan.get('created_at')}")
    meal_slots = selected_plan.get("meals", [])

    if not meal_slots:
        print("No meal slots found in this meal plan.")
        return selected_plan

    print("\n=== Meal Slots ===")
    for index, meal in enumerate(meal_slots, start=1):
        print(f"\n{index}. Meal Type: {meal.get('meal_type')}")
        print(f"Foods: {', '.join(meal.get('foods', []))}")
        print(f"Notes: {meal.get('notes')}")


    return selected_plan

    

def _start_meal_plan_day(current_user : ensure_current_user):
    if not current_user:
        print("Current user not found")
        return

    fitness_data = load_fitness_database()
    current_user_id = _current_user_id(current_user)
    meal_plan_log = [plan for plan in fitness_data.get("meal_plans", []) if _fitness_record_belongs_to_user(plan, current_user_id)]
    if not meal_plan_log:
        print("No meal plans found. Create one first")
        return

    print(f"===Meal plans===")

    for index, meal_plan in enumerate(meal_plan_log, start=1):
        print(
            f"\n{index}. {meal_plan.get('plan_name')} | {meal_plan.get('goal')} | "
            f"{meal_plan.get('daily_target_calories')} cal | "
            f"{meal_plan.get('daily_target_protein')} protein | "
            f"{meal_plan.get('daily_target_carbs')} carbs | "
            f"{meal_plan.get('daily_target_fats')} fats"
        )
    
    while True:
        meal_plan_choice = input("Enter a meal plan name or number : ").strip()
        if not meal_plan_choice:
            print("Enter a meal plan name or number to add")
            continue
        
        selected_meal_plan = None

        if meal_plan_choice.isdigit():
            meal_plan_number = int(meal_plan_choice)
            meal_plan_index = meal_plan_number - 1

            if 0 <= meal_plan_index < len(meal_plan_log):
                selected_meal_plan = meal_plan_log[meal_plan_index]
        
        else:
            for plan in meal_plan_log:
                if plan.get("plan_name", "").strip().lower() == meal_plan_choice.lower():
                    selected_meal_plan = plan
                    break
        
        if selected_meal_plan:
            break

        print("Plan not found. Enter a valid name or number to add")

    started_meal_day = {
        "id" : generate_id(),
        "user_id" : current_user_id,
        "entry_type" : "started_meal_plan_day",
        "source_plan_id" : selected_meal_plan.get("id"),
        "plan_name" : selected_meal_plan.get("plan_name"),
        "goal" : selected_meal_plan.get("goal"),
        "date_started" : now_dubai().split("T")[0],
        "started_at" : now_dubai(),
        "daily_target_calories" : selected_meal_plan.get("daily_target_calories"),
        "daily_target_protein" : selected_meal_plan.get("daily_target_protein"),
        "daily_target_carbs" : selected_meal_plan.get("daily_target_carbs"),
        "daily_target_fats" : selected_meal_plan.get("daily_target_fats"),
        "meals" : selected_meal_plan.get("meals", [])
    }
    fitness_data.setdefault("started_meal_plan_days", []).append(started_meal_day)
    save_fitness_database(fitness_data)

    print("\nMeal plan day started successfully")
    print(f"Plan Name: {started_meal_day.get('plan_name')}")
    print(f"Date Started: {started_meal_day.get('date_started')}")
    print(f"Meal Slots: {len(started_meal_day.get('meals', []))}")
    print(f"Target Calories: {started_meal_day.get('daily_target_calories')}")

    return started_meal_day
                
def _prompt_food_items() -> list[str]:
    foods: list[str] = []

    while True:
        food_item = input("Enter food item for this meal slot (or type 'done') : ").strip()

        if not food_item:
            print("Food item cannot be empty")
            continue

        if food_item.lower() == "done":
            if not foods:
                print("Add at least one food item before finishing this meal slot")
                continue
            break

        foods.append(food_item)

    return foods

def _calculate_daily_nutrition_summary(current_user : ensure_current_user):
    if not current_user:
        return
    
    fitness_data = load_fitness_database()
    meal_log = fitness_data.get("meal_log", [])
    calorie_tracker = CalorieTracker()

    while True:
        calculation_date = input("Enter a date to calculate nutrition summary (YYYY-MM-DD) or press Enter for today: ").strip()
        if not calculation_date:
            calculation_date = now_dubai().split("T")[0]
        
        while not validate_date_input(calculation_date):
            print("Invalid date format. Use YYYY-MM-DD. ")
            calculation_date = input("Enter a date to calculate nutrition summary (YYYY-MM-DD) or press Enter for today: ").strip()

        if not calculation_date:
            calculation_date = now_dubai().split("T")[0]

        matching_meals = [
            meal for meal in meal_log
            if meal.get("completion_date", "") == calculation_date
        ]
        if not matching_meals:
            print("No meals logged for this date")
            return
        
        total_calories = calorie_tracker.get_consumed_calories_for_day(current_user, calculation_date)
        remaining_calories = calorie_tracker.get_remaining_calories_for_day(current_user, calculation_date)
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        for meal in matching_meals:
            total_protein += int(meal.get("protein", 0))
            total_carbs += int(meal.get("carbs", 0))
            total_fats += int(meal.get("fats", 0))

        meal_plan_days = [meal_plan_day for meal_plan_day in fitness_data.get("started_meal_plan_days", []) if _fitness_record_belongs_to_user(meal_plan_day, current_user_id)]
        matching_plan_day = next(
            (
                meal_plan_day for meal_plan_day in meal_plan_days
                if meal_plan_day.get("date_started") == calculation_date
            ), None
        )
        if matching_plan_day:
            remaining_protein = int(matching_plan_day.get("daily_target_protein", 0)) - total_protein
            remaining_carbs = int(matching_plan_day.get("daily_target_carbs", 0)) - total_carbs
            remaining_fats = int(matching_plan_day.get("daily_target_fats", 0)) - total_fats
        else:
            remaining_protein = None
            remaining_carbs = None
            remaining_fats = None
        
        print("\n=== Daily Nutrition Summary ===")
        print(f"Date: {calculation_date}")
        print(f"Calories Consumed: {total_calories}")
        print(f"Protein Consumed: {total_protein}")
        print(f"Carbs Consumed: {total_carbs}")
        print(f"Fats Consumed: {total_fats}")
        print(f"Daily Calorie Goal: {calorie_tracker.get_daily_calorie_goal(current_user)}")
        print(f"Remaining Calories: {remaining_calories}")

        if matching_plan_day:
            print(f"Remaining Calories: {remaining_calories}")
            print(f"Remaining Protein: {remaining_protein}")
            print(f"Remaining Carbs: {remaining_carbs}")
            print(f"Remaining Fats: {remaining_fats}")
        else:
            print("No started meal plan day found for this date.")
        break
    
class Workout_Repository:
    def __init__(
        self,
        data_saver=save_fitness_database,
        data_loader=load_fitness_database,
    ):
        self.load_fitness_data = data_loader
        self.save_fitness_data = data_saver

    def log_workout_entry(self, current_user: dict | None, entry_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        workout_sessions = fitness_data.setdefault("workout_sessions", [])
        if isinstance(entry_list, list):
            for entry in entry_list:
                entry.setdefault("user_id", current_user_id)
                workout_sessions.append(entry)
        else:
            entry_list.setdefault("user_id", current_user_id)
            workout_sessions.append(entry_list)
        self.save_fitness_data(fitness_data)
        return entry_list

    def list_workout_entries(self, current_user: dict | None) -> list[dict[str, Any]]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        if not current_user_id:
            return []
        return [entry for entry in fitness_data.get("workout_sessions", []) if _fitness_record_belongs_to_user(entry, current_user_id)]

    def list_worout_entries(self, current_user: dict | None) -> list[dict[str, Any]]:
        return self.list_workout_entries(current_user)

    def get_entry(self, current_user: dict | None, entry_id: str) -> dict | None:
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

    def add_strength_exercise(
        self,
        label: str,
        name: str,
        exercises: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "block_type": "strength",
            "label": label,
            "name": name,
            "exercises": exercises,
        }

    def add_cardio_exercise(
        self,
        label: str,
        minutes: int,
        intensity: str,
    ) -> dict[str, Any]:
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

    def validate_session(self, session: dict) -> None:
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


class RoutineService:
   
    def __init__(
        self,
        data_saver=save_fitness_database,
        get_user=ensure_current_user,
        data_loader=load_fitness_database,
    ):
        self.get_user = get_user
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
    def format_routine(routine: dict) -> dict:
        return {
            "id": routine.get("id"),
            "name": routine.get("name"),
            "day_count": len(routine.get("days", [])),
            "created_at": routine.get("created_at"),
            "updated_at": routine.get("updated_at"),
        }

    def build_session_from_routine(self, current_user: dict | None, day_name: str, routine_name: str | None = None) -> dict[str, Any]:
        fitness_data = self.load_fitness_data()
        current_user_id = _current_user_id(current_user)
        routines = [routine for routine in fitness_data.get("routines", []) if _fitness_record_belongs_to_user(routine, current_user_id)]
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


def _collect_block_type() -> str:
    while True:
        block_type = input("Block type (strength/cardio) : ").strip().lower()
        if block_type in {"strength", "cardio"}:
            return block_type
        print("Block type must be strength or cardio")


def _log_workout_session(current_user: ensure_current_user):
    if not current_user:
        print("Current user not found")
        return

    workout_repository = Workout_Repository()
    workout_service = WorkoutSessionService()
    session_name = _prompt_session_name()
    workout_blocks = _prompt_workout_blocks()
    notes = input("Workout notes (optional) : ").strip()

    current_user_id = _current_user_id(current_user)
    session = workout_service.create_session(
        user_id=current_user_id,
        name=session_name,
        workout_details=workout_blocks,
        notes=notes,
    )
    workout_repository.log_workout_entry(current_user, [session])
    print("Workout session logged successfully")
    return session


def _create_routine(current_user: ensure_current_user):
    if not current_user:
        print("Current user not found")
        return

    routine_service = RoutineService()
    routine_name = _prompt_routine_name()
    days = _prompt_routine_days()
    routine = routine_service.create_routine(current_user, routine_name, days)
    print("Routine created successfully")
    return routine


def _start_routine_day(current_user: ensure_current_user):
    if not current_user:
        print("Current user not found")
        return

    routine_service = RoutineService()
    routine_name = _prompt_routine_name()
    day_name = input("Enter the routine day to start : ").strip()
    session = routine_service.build_session_from_routine(current_user, day_name, routine_name)
    print(f"Started routine session from {routine_name or session.get('name')}")
    return session


def _view_sessions(current_user: ensure_current_user) -> list[dict[str, Any]]:
    if not current_user:
        print("Current user not found")
        return []

    workout_repository = Workout_Repository()
    sessions = workout_repository.list_workout_entries(current_user)
    if not sessions:
        print("No workout sessions found")
        return []

    print("===Workout sessions===")
    for index, session in enumerate(sessions, start=1):
        print(f"{index}. {session.get('name')} | {session.get('created_at')}")
    return sessions


def _view_sessions_details(current_user: ensure_current_user) -> dict[str, Any] | None:
    if not current_user:
        print("Current user not found")
        return None

    sessions = _view_sessions(current_user)
    if not sessions:
        return None

    choice = input("Enter a session name or number : ").strip()
    selected_session = None
    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(sessions):
            selected_session = sessions[index]
    else:
        for session in sessions:
            if session.get("name", "").strip().lower() == choice.lower():
                selected_session = session
                break

    if not selected_session:
        print("Session not found")
        return None

    print("\n=== Session Details ===")
    print(f"Session ID: {selected_session.get('id')}")
    print(f"Name: {selected_session.get('name')}")
    print(f"Blocks: {len(selected_session.get('blocks', []))}")
    print(f"Created at: {selected_session.get('created_at')}")
    print(f"Notes: {selected_session.get('notes')}")
    return selected_session


def _view_routines(current_user: ensure_current_user) -> list[dict[str, Any]]:
    if not current_user:
        print("Current user not found")
        return []

    routine_service = RoutineService()
    fitness_data = routine_service.load_fitness_data()
    current_user_id = _current_user_id(current_user)
    routines = [routine for routine in fitness_data.get("routines", []) if _fitness_record_belongs_to_user(routine, current_user_id)]
    if not routines:
        print("No routines found")
        return []

    print("===Routines===")
    for index, routine in enumerate(routines, start=1):
        print(f"{index}. {routine.get('name')} | {len(routine.get('days', []))} days")
    return routines


def view_routine_structure(current_user: ensure_current_user):
    if not current_user:
        print("Current user not found")
        return

    routines = _view_routines(current_user)
    if not routines:
        return None

    choice = input("Enter a routine name or number : ").strip()
    selected_routine = None
    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(routines):
            selected_routine = routines[index]
    else:
        for routine in routines:
            if routine.get("name", "").strip().lower() == choice.lower():
                selected_routine = routine
                break

    if not selected_routine:
        print("Routine not found")
        return None

    print("\n=== Routine Details ===")
    print(f"Routine ID: {selected_routine.get('id')}")
    print(f"Routine Name: {selected_routine.get('name')}")
    print(f"Created at: {selected_routine.get('created_at')}")
    for day in selected_routine.get("days", []):
        print(f"- {day.get('day_name')}: {len(day.get('blocks', []))} blocks")
    return selected_routine


def _prompt_session_name():
    while True:
        session_name = input("Enter workout session name : ").strip()
        if session_name:
            return session_name
        print("Session name cannot be empty")


def _prompt_workout_blocks():
    blocks = []
    while True:
        block_type = _collect_block_type()
        if block_type == "strength":
            blocks.append(_prompt_strength_exercises())
        else:
            blocks.append(_prompt_cardio_block())

        add_another = input("Add another block? (y/n) : ").strip().lower()
        while add_another not in {"y", "n"}:
            add_another = input("Add another block? (y/n) : ").strip().lower()
        if add_another == "n":
            break
    return blocks


def _prompt_strength_exercises():
    label = input("Strength block label : ").strip()
    name = input("Strength block name : ").strip()
    exercises = []

    while True:
        exercise_name = input("Exercise name (or 'done') : ").strip()
        if not exercise_name:
            print("Exercise name cannot be empty")
            continue
        if exercise_name.lower() == "done":
            if not exercises:
                print("Add at least one exercise before finishing the block")
                continue
            break

        target_sets = input("Target sets (optional) : ").strip()
        target_reps = input("Target reps (optional) : ").strip()
        exercises.append({
            "name": exercise_name,
            "target_sets": int(target_sets) if target_sets.isdigit() else target_sets,
            "target_reps": target_reps,
        })

    return WorkoutSessionService().add_strength_exercise(label, name, exercises)


def _prompt_cardio_block():
    label = input("Cardio block label : ").strip()
    minutes = input("Minutes : ").strip()
    intensity = input("Intensity : ").strip()
    return WorkoutSessionService().add_cardio_exercise(
        label,
        int(minutes) if minutes.isdigit() else 0,
        intensity,
    )


def _prompt_routine_name():
    while True:
        routine_name = input("Enter routine name : ").strip()
        if routine_name:
            return routine_name
        print("Routine name cannot be empty")


def _prompt_routine_days():
    days = []
    while True:
        day_name = input("Enter routine day name (or 'done') : ").strip()
        if not day_name:
            print("Day name cannot be empty")
            continue
        if day_name.lower() == "done":
            if not days:
                print("Add at least one day before finishing the routine")
                continue
            break

        blocks = _prompt_workout_blocks()
        days.append(RoutineService.add_routine_day(day_name, blocks))

        add_another_day = input("Add another routine day? (y/n) : ").strip().lower()
        while add_another_day not in {"y", "n"}:
            add_another_day = input("Add another routine day? (y/n) : ").strip().lower()
        if add_another_day == "n":
            break
    return days


def _prompt_day_structure():
    day_name = input("Enter day name : ").strip()
    blocks = _prompt_workout_blocks()
    return RoutineService.add_routine_day(day_name, blocks)

     

def FitnessOverviewDashboard(current_user : ensure_current_user,) -> None:
    if not current_user:
        print("Current user not found")
        return None

    while True:
        print("\n=== Fitness Overview ===")
        print("1. Meals")
        print("2. Meal Plans")
        print("3. Nutrition Summary")
        print("4. Workout Sessions")
        print("5. Routines")
        print("6. Exit")

        choice = input("\nChoose an option : ").strip()

        if choice == "1":
            while True:
                print("\n=== Meals ===")
                print("1. Log meal")
                print("2. View meals")
                print("3. View meal details")
                print("4. Back")

                meal_choice = input("\nChoose an option : ").strip()
                if meal_choice == "1":
                    _log_meal(current_user)
                elif meal_choice == "2":
                    _view_meals(current_user)
                elif meal_choice == "3":
                    _view_meal_details(current_user)
                elif meal_choice == "4":
                    break
                else:
                    print("Invalid option")

        elif choice == "2":
            while True:
                print("\n=== Meal Plans ===")
                print("1. Create meal plan")
                print("2. View meal plans")
                print("3. View meal plan structure")
                print("4. Start meal plan day")
                print("5. Back")

                meal_plan_choice = input("\nChoose an option : ").strip()
                if meal_plan_choice == "1":
                    create_meal_plan(current_user)
                elif meal_plan_choice == "2":
                    view_meal_plans(current_user)
                elif meal_plan_choice == "3":
                    view_meal_plan_structure(current_user)
                elif meal_plan_choice == "4":
                    _start_meal_plan_day(current_user)
                elif meal_plan_choice == "5":
                    break
                else:
                    print("Invalid option")

        elif choice == "3":
            _calculate_daily_nutrition_summary(current_user)

        elif choice == "4":
            while True:
                print("\n=== Workout Sessions ===")
                print("1. Log workout session")
                print("2. View workout sessions")
                print("3. View workout session details")
                print("4. Back")

                workout_choice = input("\nChoose an option : ").strip()
                if workout_choice == "1":
                    _log_workout_session(current_user)
                elif workout_choice == "2":
                    _view_sessions(current_user)
                elif workout_choice == "3":
                    _view_sessions_details(current_user)
                elif workout_choice == "4":
                    break
                else:
                    print("Invalid option")

        elif choice == "5":
            while True:
                print("\n=== Routines ===")
                print("1. Create routine")
                print("2. View routines")
                print("3. View routine structure")
                print("4. Start routine day")
                print("5. Back")

                routine_choice = input("\nChoose an option : ").strip()
                if routine_choice == "1":
                    _create_routine(current_user)
                elif routine_choice == "2":
                    _view_routines(current_user)
                elif routine_choice == "3":
                    view_routine_structure(current_user)
                elif routine_choice == "4":
                    _start_routine_day(current_user)
                elif routine_choice == "5":
                    break
                else:
                    print("Invalid option")

        elif choice == "6":
            print("Returning to the main menu")
            return None
        else:
            print("Invalid option")

FitnessOverviewDashboard(current_user=ensure_current_user)


# Features to be implemented in MyFitness:
# 1. Edit and delete workout/body metric records.
# 2. Goal target tracking with deadlines.
# 3. Weekly/monthly charts and progress trends.
# 4. Smart reminders for missed workout days.
