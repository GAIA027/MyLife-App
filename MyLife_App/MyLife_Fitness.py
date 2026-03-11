#Fitness tracker for MyLife app
from MyLife_Tracker import *


def _get_user_record(current_user):
    data = load_database()
    user = next(
        (u for u in data.get("users", []) if str(u.get("id")) == str(current_user.get("id"))),
        None,
    )
    return data, user


def _add_workout(current_user):
    data, user = _get_user_record(current_user)
    if not user:
        print("Current user not found.")
        return

    workout_type = input("Workout type (e.g. cardio, strength): ").strip().lower()
    duration = input("Duration in minutes: ").strip()
    notes = input("Workout notes: ").strip()

    user.setdefault("fitness", []).append(
        {
            "id": generate_id(),
            "entry_type": "workout",
            "workout_type": workout_type or "general",
            "duration_minutes": duration or "0",
            "notes": notes,
            "status": "completed",
            "created_at": now_dubai(),
            "updated_at": now_dubai(),
        }
    )
    save_database(data)
    print("Workout log added.")


def _view_workouts(current_user):
    _, user = _get_user_record(current_user)
    if not user:
        print("Current user not found.")
        return
    workouts = [w for w in user.get("fitness", []) if w.get("entry_type") == "workout"]
    if not workouts:
        print("No workout logs found.")
        return

    print("\n=== Workout History ===")
    for index, item in enumerate(workouts, start=1):
        print(
            f"{index}. {item.get('workout_type', 'general')} - "
            f"{item.get('duration_minutes', '0')} min ({item.get('created_at', '')})"
        )
        if item.get("notes"):
            print(f"   notes: {item.get('notes')}")


def _group_workouts_by_type(current_user):
    _, user = _get_user_record(current_user)
    if not user:
        print("Current user not found.")
        return

    grouped = {}
    for item in user.get("fitness", []):
        if item.get("entry_type") != "workout":
            continue
        workout_type = str(item.get("workout_type", "general")).lower()
        grouped[workout_type] = grouped.get(workout_type, 0) + 1

    if not grouped:
        print("No workouts to group.")
        return

    print("\n=== Workouts Grouped By Type ===")
    for workout_type, total in grouped.items():
        print(f"- {workout_type}: {total}")


def workout_menu(current_user):
    while True:
        print("\n=== Workout Menu ===")
        print("1. Add workout log")
        print("2. View all workouts")
        print("3. Group workouts by type")
        print("4. Back")
        user_request = input("Choose an option: ").strip()

        if user_request == "1":
            _add_workout(current_user)
        elif user_request == "2":
            _view_workouts(current_user)
        elif user_request == "3":
            _group_workouts_by_type(current_user)
        elif user_request == "4":
            return
        else:
            print("Enter a valid option.")


def _add_body_metric(current_user):
    data, user = _get_user_record(current_user)
    if not user:
        print("Current user not found.")
        return

    metric_type = input("Metric type (e.g. weight, body_fat): ").strip().lower()
    metric_value = input("Metric value: ").strip()

    user.setdefault("fitness", []).append(
        {
            "id": generate_id(),
            "entry_type": "metric",
            "metric_type": metric_type or "general",
            "value": metric_value,
            "created_at": now_dubai(),
            "updated_at": now_dubai(),
        }
    )
    save_database(data)
    print("Body metric added.")


def _view_body_metrics(current_user):
    _, user = _get_user_record(current_user)
    if not user:
        print("Current user not found.")
        return

    metrics = [m for m in user.get("fitness", []) if m.get("entry_type") == "metric"]
    if not metrics:
        print("No body metrics found.")
        return

    print("\n=== Body Metrics ===")
    for index, item in enumerate(metrics, start=1):
        print(f"{index}. {item.get('metric_type', 'general')}: {item.get('value', '')}")


def metrics_menu(current_user):
    while True:
        print("\n=== Body Metrics Menu ===")
        print("1. Add body metric")
        print("2. View all body metrics")
        print("3. Back")
        user_request = input("Choose an option: ").strip()

        if user_request == "1":
            _add_body_metric(current_user)
        elif user_request == "2":
            _view_body_metrics(current_user)
        elif user_request == "3":
            return
        else:
            print("Enter a valid option.")


def MyFitness_dashboard(current_user):
    current_user = ensure_current_user(current_user)
    if not current_user:
        return False

    while True:
        _, user = _get_user_record(current_user)
        if not user:
            print("Current user not found.")
            return False
        total_logs = len(user.get("fitness", []))
        print("\n=== MyFitness Dashboard ===")
        print(f"Total fitness logs: {total_logs}")
        print("\n1. Workout menu")
        print("2. Body metrics menu")
        print("3. Fitness summary")
        print("4. Back to main menu")
        user_request = input("Choose an option: ").strip()

        if user_request == "1":
            workout_menu(current_user)
        elif user_request == "2":
            metrics_menu(current_user)
        elif user_request == "3":
            _view_workouts(current_user)
            _view_body_metrics(current_user)
        elif user_request == "4":
            app_dashboard(current_user)
            return True
        else:
            print("Enter a valid option.")


# Features to be implemented in MyFitness:
# 1. Edit and delete workout/body metric records.
# 2. Goal target tracking with deadlines.
# 3. Weekly/monthly charts and progress trends.
# 4. Smart reminders for missed workout days.
