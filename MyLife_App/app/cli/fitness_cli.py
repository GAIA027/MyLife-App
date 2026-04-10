from app.modules import MyLife_Fitness as fitness_module


def _prompt_food_items() -> list[str]:
    foods = []
    while True:
        food_item = input("Enter food item for this meal slot (or type 'done') : ").strip()
        if not food_item:
            print("Food item cannot be empty")
            continue
        if food_item.lower() == "done":
            if foods:
                return foods
            print("Add at least one food item before finishing this meal slot")
            continue
        foods.append(food_item)


def _collect_block_type() -> str:
    while True:
        block_type = input("Block type (strength/cardio) : ").strip().lower()
        if block_type in {"strength", "cardio"}:
            return block_type
        print("Block type must be strength or cardio")


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
            if exercises:
                return fitness_module.WorkoutSessionService().add_strength_exercise(label, name, exercises)
            print("Add at least one exercise before finishing the block")
            continue
        exercises.append(
            {
                "name": exercise_name,
                "target_sets": input("Target sets (optional) : ").strip(),
                "target_reps": input("Target reps (optional) : ").strip(),
            }
        )


def _prompt_cardio_block():
    return fitness_module.WorkoutSessionService().add_cardio_exercise(
        input("Cardio block label : ").strip(),
        int(input("Minutes : ").strip() or "0"),
        input("Intensity : ").strip(),
    )


def _prompt_workout_blocks():
    blocks = []
    while True:
        blocks.append(_prompt_strength_exercises() if _collect_block_type() == "strength" else _prompt_cardio_block())
        if input("Add another block? (y/n) : ").strip().lower() == "n":
            return blocks


def _prompt_routine_days():
    days = []
    while True:
        day_name = input("Enter routine day name (or 'done') : ").strip()
        if day_name.lower() == "done" and days:
            return days
        if not day_name:
            print("Day name cannot be empty")
            continue
        days.append(fitness_module.RoutineService.add_routine_day(day_name, _prompt_workout_blocks()))
        if input("Add another routine day? (y/n) : ").strip().lower() == "n":
            return days


def _log_meal(current_user):
    meal = fitness_module.MealTracker().add_meal(
        current_user=current_user,
        meal_name=input("\nEnter meal name : ").strip().lower(),
        meal_type=input("\nEnter meal type (breakfast/lunch/dinner/snack) : ").strip().lower(),
        calorie_in_meal=int(input("\nEnter calories for this meal : ").strip()),
        completetion_date=input("\nEnter a completion date (YYYY-MM-DD) or press enter for today : ").strip() or fitness_module.now_dubai().split("T")[0],
        time_of_log=fitness_module.now_dubai(),
        notes=input("\nEnter notes (optional) : ").strip(),
    )
    print("\nMeal logged successfully")
    print(meal)


def _view_meals(current_user):
    meals = fitness_module.list_meals(current_user)
    print("===Meal history===")
    for index, meal in enumerate(meals, start=1):
        print(f"{index}. {meal.get('meal', '')} | {meal.get('calories')} | {meal.get('completion_date')}")
    return meals


def _view_meal_details(current_user):
    selected = fitness_module.get_meal_details(current_user, input("Enter a meal name or number : ").strip())
    print(selected or "meal not found")
    return selected


def _create_meal_plan(current_user):
    meals = []
    while True:
        meals.append(
            {
                "meal_type": input("\nEnter meal type for this slot (breakfast/lunch/dinner/snack) : ").strip().lower(),
                "foods": _prompt_food_items(),
                "notes": input("Enter notes for this meal slot (optional) : ").strip(),
            }
        )
        if input("\nAdd another meal slot? (y/n) : ").strip().lower() == "n":
            break
    try:
        plan = fitness_module.create_meal_plan(
            current_user,
            input("\nEnter meal plan name : ").strip(),
            input("\nGoal (fat loss / maintenance / muscle gain) : ").strip().lower(),
            int(input("\nDaily Target Calories : ").strip()),
            int(input("\nDaily Target Proteins : ").strip()),
            int(input("\nDaily target carbs : ").strip()),
            int(input("\nDaily target fats : ").strip()),
            meals,
        )
    except ValueError as error:
        print(str(error))
        return
    print("\nMeal plan created successfully")
    print(plan)


def _view_meal_plans(current_user):
    plans = fitness_module.view_meal_plans(current_user)
    print(plans)
    return plans


def _view_meal_plan_structure(current_user):
    print(fitness_module.view_meal_plan_structure(current_user, input("\nEnter a meal plan name or number").strip()))


def _start_meal_plan_day(current_user):
    print(fitness_module.start_meal_plan_day(current_user, input("Enter a meal plan name or number : ").strip()))


def _calculate_daily_nutrition_summary(current_user):
    try:
        summary = fitness_module.calculate_daily_nutrition_summary(
            current_user,
            input("Enter a date to calculate nutrition summary (YYYY-MM-DD) or press Enter for today: ").strip() or fitness_module.now_dubai().split("T")[0],
        )
    except ValueError as error:
        print(str(error))
        return
    print(summary or "No meals logged for this date")


def _log_workout_session(current_user):
    try:
        session = fitness_module.log_workout_session(
            current_user,
            input("Enter workout session name : ").strip(),
            _prompt_workout_blocks(),
            input("Workout notes (optional) : ").strip(),
        )
    except ValueError as error:
        print(str(error))
        return
    print("Workout session logged successfully")
    print(session)


def _create_routine(current_user):
    try:
        routine = fitness_module.create_routine(
            current_user,
            input("Enter routine name : ").strip(),
            _prompt_routine_days(),
        )
    except ValueError as error:
        print(str(error))
        return
    print("Routine created successfully")
    print(routine)


def _start_routine_day(current_user):
    try:
        session = fitness_module.start_routine_day(
            current_user,
            input("Enter the routine day to start : ").strip(),
            input("Enter routine name : ").strip(),
        )
    except ValueError as error:
        print(str(error))
        return
    print(session)


def _view_sessions(current_user):
    sessions = fitness_module.list_sessions(current_user)
    print(sessions)
    return sessions


def _view_sessions_details(current_user):
    print(fitness_module.get_session_details(current_user, input("Enter a session name or number : ").strip()))


def _view_routines(current_user):
    routines = fitness_module.list_routines(current_user)
    print(routines)
    return routines


def view_routine_structure(current_user):
    print(fitness_module.view_routine_structure(current_user, input("Enter a routine name or number : ").strip()))


def FitnessOverviewDashboard(current_user):
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
            print("\n=== Meals ===")
            meal_choice = input("1. Log meal\n2. View meals\n3. View meal details\n4. Back\n").strip()
            if meal_choice == "1":
                _log_meal(current_user)
            elif meal_choice == "2":
                _view_meals(current_user)
            elif meal_choice == "3":
                _view_meal_details(current_user)
        elif choice == "2":
            meal_plan_choice = input("1. Create meal plan\n2. View meal plans\n3. View meal plan structure\n4. Start meal plan day\n5. Back\n").strip()
            if meal_plan_choice == "1":
                _create_meal_plan(current_user)
            elif meal_plan_choice == "2":
                _view_meal_plans(current_user)
            elif meal_plan_choice == "3":
                _view_meal_plan_structure(current_user)
            elif meal_plan_choice == "4":
                _start_meal_plan_day(current_user)
        elif choice == "3":
            _calculate_daily_nutrition_summary(current_user)
        elif choice == "4":
            workout_choice = input("1. Log workout session\n2. View workout sessions\n3. View workout session details\n4. Back\n").strip()
            if workout_choice == "1":
                _log_workout_session(current_user)
            elif workout_choice == "2":
                _view_sessions(current_user)
            elif workout_choice == "3":
                _view_sessions_details(current_user)
        elif choice == "5":
            routine_choice = input("1. Create routine\n2. View routines\n3. View routine structure\n4. Start routine day\n5. Back\n").strip()
            if routine_choice == "1":
                _create_routine(current_user)
            elif routine_choice == "2":
                _view_routines(current_user)
            elif routine_choice == "3":
                view_routine_structure(current_user)
            elif routine_choice == "4":
                _start_routine_day(current_user)
        elif choice == "6":
            return
