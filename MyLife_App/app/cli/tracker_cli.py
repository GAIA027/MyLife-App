from app.modules import MyLife_Tracker as tracker_module


def _prompt_deadline(prompt: str, allow_past: bool = False) -> str | None:
    raw_value = input(prompt).strip()
    value, error = tracker_module.validate_deadline_input(raw_value, allow_past=allow_past)
    if error:
        print(error)
        return None
    return value


def user_create_account():
    print("\n===Signup===")
    try:
        return tracker_module.create_user_account(
            username=input("username : ").strip().lower(),
            email=input("Email : ").strip().lower(),
            password=input("Password : "),
            first_name=input("First name : "),
            last_name=input("Last name : "),
        )
    except ValueError as error:
        print(str(error))
        return None


def user_login():
    print("\n===Log-in===")
    user, token = tracker_module.authenticate_user(
        input("\nEmail or Username : ").strip().lower(),
        input("\nPassword : "),
    )
    if not user:
        print("User not found. Please check your email/username and try again.")
        return None, None
    print("\nLogin Successful. Welcome to MyLife")
    return user, token


def show_tasks(current_user):
    tasks = tracker_module.task_main.view_tasks(current_user)
    if not tasks:
        print("No tasks found for this user.")
        return
    print("\n===Tasks===")
    for task_item in tasks:
        print(
            f"- {task_item.get('task_name', 'Untitled')} "
            f"[{task_item.get('status', 'pending')}] "
            f"(deadline: {task_item.get('task_deadline', 'N/A')})"
        )


def remove_task(current_user):
    delete_request = input("Enter the title of the task you want to delete: ")
    print(tracker_module.task_main.delete_task(current_user, delete_request))


def record_task(current_user):
    task_title = input("\nTask title: ").strip()
    task_description = input("\nDescription: ").strip()
    task_type = input("\nTask type: ").strip()
    task_deadline = _prompt_deadline("\nTask deadline (YYYY-MM-DD HH:MM): ")
    if not task_deadline:
        return
    task_notes = input("\nTask notes: ").strip()
    recurring = input("Recurring ? (y/n) : ").strip().lower() in ("y", "yes")
    rule = None
    if recurring:
        rule = {
            "frequency": input("Frequency (daily/weekly/monthly) : ").strip().lower(),
            "interval": int(input("Every how many? (e.g. 1) : ").strip() or "1"),
        }
    if tracker_module.task_main.create_task(
        current_user,
        task_title,
        task_type,
        task_description,
        tracker_module.now_dubai(),
        task_deadline,
        task_notes,
        recurring=recurring,
        rule=rule,
    ):
        print("\n===Task Recorded Successfully===")


def update_task(current_user):
    task_title = input("Enter the title of the task you want to update: ")
    print("Task found! Enter the new details:")
    task_deadline = _prompt_deadline("Task deadline (YYYY-MM-DD HH:MM): ")
    if not task_deadline:
        return
    result = tracker_module.task_main.update_task(
        current_user,
        task_title,
        input("New task title: ").strip() or task_title,
        input("New description: ").strip(),
        input("New task type: ").strip(),
        task_deadline,
        input("New task notes: ").strip(),
    )
    print(result)


def mark_task_as_complete(current_user):
    task_name = input("Enter task name to mark complete: ").strip().lower()
    print("Task marked as completed." if tracker_module.task_main.mark_task_as_complete(current_user, task_name) else "Task not found")


def create_habit(current_user):
    habit_start_date = _prompt_deadline("Start date (YYYY-MM-DD or MM/DD/YYYY): ", allow_past=True)
    if not habit_start_date:
        return
    habit = tracker_module.create_habit(
        current_user,
        input("Habit name: ").lower(),
        input("Description: ").strip(),
        input("Habit frequency (e.g., daily, weekly): ").strip(),
        habit_start_date,
        input("Habit notes: ").strip(),
    )
    if habit:
        print("\n===Habit Created successfully")


def update_habit(current_user):
    habit_name = input("Enter habit name to upadate: ").lower()
    updated = tracker_module.update_habit(
        current_user,
        habit_name,
        new_description=input("New description: ").strip(),
        new_frequency=input("New frequency: ").strip(),
        new_start_date=input("New start date: ").strip(),
        new_notes=input("New notes: ").strip(),
    )
    print("Habit updated successfully!" if updated else "Habit not found.")


def show_habits(current_user):
    habits = tracker_module.show_habits(current_user)
    if not habits:
        print("No habits found for this user")
        return
    print("\n===Habits===")
    for habit in habits:
        print(f"- {habit.get('habit_name', 'untitled')} [{habit.get('status', 'pending')}]")


def delete_habit(current_user):
    request = input("Enter the name of the habit you want to delete: ")
    print("Habit deleted successfully!" if tracker_module.delete_habit(current_user, request) else "Habit not found! Please check the title and try again.")


def record_project(current_user):
    try:
        project_duration = int(input("Project duration in days: "))
    except ValueError:
        print("Project duration must be a whole number.")
        return
    project_deadline = _prompt_deadline("Project deadline (YYYY-MM-DD HH:MM): ")
    if not project_deadline:
        return
    project_record = tracker_module.project_main.create_projects(
        current_user,
        input("Project title: ").strip().lower(),
        input("Description: ").strip(),
        project_duration,
        tracker_module.now_dubai(),
        project_deadline,
        input("Project notes: ").strip(),
    )
    if project_record:
        print("Project created successfully")


def view_projects(current_user):
    print(tracker_module.project_main.show_projects(current_user))


def update_project_task(current_user):
    project_update_request = input("Project title : ")
    project_deadline = _prompt_deadline("Project deadline (YYYY-MM-DD HH:MM): ")
    if not project_deadline:
        return
    result = tracker_module.project_main.update_project(
        current_user,
        project_update_request,
        input("New project title: ").strip() or project_update_request,
        input("New description: ").strip(),
        project_deadline,
        input("Project notes: ").strip(),
    )
    print(result)


def delete_project(current_user):
    request = input("Enter the title of the project you want to delete: ")
    print(tracker_module.project_main.delete_project(current_user, request))


def mark_project_as_complete(current_user):
    project_title = input("Enter the project name you want to mark complete: ").strip().lower()
    print("Project marked as completed." if tracker_module.project_main.mark_project_as_complete(current_user, project_title) else "Project not found.")


def change_password(current_user):
    try:
        updated = tracker_module.change_password(
            current_user,
            input("Enter your current password to change"),
            input("Enter your new password : "),
        )
    except ValueError as error:
        print(str(error))
        return
    print("Password changed successfully" if updated else "Incorrect password")


def delete_account(current_user):
    confirmed = input("\nAre you sure you want to delete your account? yes/no").lower() == "yes"
    deleted = tracker_module.delete_account(
        current_user,
        input("Enter your password to confirm account deletion"),
        confirm=confirmed,
    )
    print("User deleted successfully" if deleted else "Password incorrect or deletion cancelled")


def display_tag_color():
    print("\n1. Black")
    print("\n2. White")
    print("\n3. Blue")
    print("\n4. Red")
    print("\n5. Purple")
    print("\n6. yellow")
    print("\n7. Green")


def get_items():
    print("\n1. Tasks")
    print("\n2. Habits")
    print("\n3. Projects")


def create_tag(current_user):
    tag_name = input("\nTag name : ").lower()
    display_tag_color()
    try:
        tag = tracker_module.create_tag(
            current_user,
            tag_name,
            int(input("\nEnter a color for yout current tag")),
            input("Description : "),
        )
    except (ValueError, TypeError) as error:
        print(str(error))
        return
    if tag:
        print("Tag created successfully")


def view_tag(current_user):
    tags = tracker_module.view_tag(current_user)
    print("\nTags")
    for tag in tags:
        print(f"- {tag.get('tag_name', 'untitled')}")


def edit_tag(current_user):
    tag_name = input("Enter the name of the tag you want to edit : ").strip().lower()
    display_tag_color()
    updated = tracker_module.edit_tag(
        current_user,
        tag_name,
        new_tag_name=input("New tag name: ").strip(),
        new_tag_color=int(input("New tag color: ").strip()),
        new_tag_description=input("New tag description: ").strip(),
    )
    print("Tag updated successfully!" if updated else "Tag not found! Please check the name and try again.")


def delete_tag(current_user):
    removed = tracker_module.delete_tag(current_user, input("Enter the name of the tag you want to remove"))
    print("Tag removed successfully" if removed else "Tag not found")


def attach_tag_to_item(current_user):
    get_items()
    try:
        item_type = int(input("\n 1. Task. 2. habit 3. projects"))
    except ValueError:
        print("Enter a valid number")
        return
    attached = tracker_module.attach_tag_to_item(
        current_user,
        item_type,
        input("Tag name : ").strip().lower(),
        input("Item name : ").strip().lower(),
    )
    print("Item updated successfully" if attached else "Item or tag not found")


def remove_tag_to_item(current_user):
    get_items()
    try:
        item_type = int(input("\n 1. Task. 2. habit 3. projects"))
    except ValueError:
        print("Enter a valid number")
        return
    removed = tracker_module.remove_tag_to_item(
        current_user,
        item_type,
        input("Tag name : ").strip().lower(),
        input("Item name : ").strip().lower(),
    )
    print("Tag removed successfully" if removed else "Tag not found in the specified item.")


def tag_dashboard(current_user):
    while True:
        print("\n===Tags===")
        print("\n1. Create Tag")
        print("\n2. View Tag")
        print("\n3. Edit Tag")
        print("\n4. Delete tag")
        print("\n5. Attach Tag to Item")
        print("\n6. Remove Tag to Item")
        print("\n7. Back to main menu")
        choice = input("\nSelect option : ").strip()
        if choice == "1":
            create_tag(current_user)
        elif choice == "2":
            view_tag(current_user)
        elif choice == "3":
            edit_tag(current_user)
        elif choice == "4":
            delete_tag(current_user)
        elif choice == "5":
            attach_tag_to_item(current_user)
        elif choice == "6":
            remove_tag_to_item(current_user)
        elif choice == "7":
            return


def app_settings(current_user):
    print("\n===Settings===")
    print("1. Change password")
    print("2. Delete account")
    print("3. View archive")
    print("4. Go back to main menu")
    choice = input().strip()
    if choice == "1":
        change_password(current_user)
    elif choice == "2":
        delete_account(current_user)
    elif choice == "3":
        print(tracker_module.archive_dashboard(current_user))


def task_dashboard(current_user):
    print("\n===Tasks===")
    print("\n1. Search Tasks")
    print("\n2. Create task")
    print("\n3. View tasks")
    print("\n4. Update task")
    print("\n5. Mark task as done")
    print("\n6. Delete task")
    print("\n7. Go back to main menu")
    choice = input().strip()
    if choice == "1":
        print(tracker_module.search_engine.search_tasks_engine(current_user, input("search keyword : ").lower()))
    elif choice == "2":
        record_task(current_user)
    elif choice == "3":
        show_tasks(current_user)
    elif choice == "4":
        update_task(current_user)
    elif choice == "5":
        mark_task_as_complete(current_user)
    elif choice == "6":
        remove_task(current_user)


def projects_dashboard(current_user):
    print("\n===Projects===")
    print("\n1. Search projects")
    print("\n2. Create Project")
    print("\n3. View Projects")
    print("\n4. Update Project")
    print("\n5. Delete Project")
    print("\n6. Go back to main menu")
    choice = input().strip()
    if choice == "1":
        print(tracker_module.search_engine.search_projects_engine(current_user, input("search keyword : ").lower()))
    elif choice == "2":
        record_project(current_user)
    elif choice == "3":
        view_projects(current_user)
    elif choice == "4":
        update_project_task(current_user)
    elif choice == "5":
        delete_project(current_user)


def habits_dashboard(current_user):
    print("\n===Habits===")
    print("\n1. Search Habits")
    print("\n2. Create Habit")
    print("\n3. Mark Habit")
    print("\n4. View Habits")
    print("\n5. Update Habit")
    print("\n6. Delete Habits")
    choice = input().strip()
    if choice == "1":
        print(tracker_module.search_engine.search_habits_engine(current_user, input("search keyword : ").lower()))
    elif choice == "2":
        create_habit(current_user)
    elif choice == "3":
        print("Habit marked complete." if tracker_module.mark_habit_as_complete(current_user, input("Enter the habit name you want to mark complete: ").strip().lower()) else "Habit not found")
    elif choice == "4":
        show_habits(current_user)
    elif choice == "5":
        update_habit(current_user)
    elif choice == "6":
        delete_habit(current_user)


def app_dashboard(current_user):
    current_user = tracker_module.ensure_current_user(current_user)
    if not current_user:
        return
    print(f"\nWelcome {current_user['username']} ")
    print("\n1. MyOverview")
    print("\n2. MyTasks")
    print("\n3. MyProjects")
    print("\n4. MyHabits")
    print("\n5. MyArchive")
    print("\n6. Settings")
    print("\n7. Tags")
    print("\n8. Log out")
    choice = input().strip()
    if choice == "1":
        print(tracker_module.ProductivityOverviewDashboard(current_user).render_user_information())
    elif choice == "2":
        task_dashboard(current_user)
    elif choice == "3":
        projects_dashboard(current_user)
    elif choice == "4":
        habits_dashboard(current_user)
    elif choice == "5":
        print(tracker_module.archive_dashboard(current_user))
    elif choice == "6":
        app_settings(current_user)
    elif choice == "7":
        tag_dashboard(current_user)


def app_UI():
    print("\n===MyLife===")
    print("\n1. Sign Up")
    print("\n2. Log In")
    print("\n3. Exit")
    choice = input().strip()
    if choice == "1":
        user = user_create_account()
        if user:
            from app.modules.MyLife_main import MyLife_dashboard

            MyLife_dashboard(user)
    elif choice == "2":
        user, _ = user_login()
        if user:
            from app.modules.MyLife_main import MyLife_dashboard

            MyLife_dashboard(user)
