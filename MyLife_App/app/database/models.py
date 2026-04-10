from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BaseRecord:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class User(BaseRecord):
    id: str
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    tasks: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    habits: list[dict[str, Any]] = field(default_factory=list)
    finance: list[dict[str, Any]] = field(default_factory=list)
    fitness: list[dict[str, Any]] = field(default_factory=list)
    archived_tasks_log: list[dict[str, Any]] = field(default_factory=list)
    archived_habits_log: list[dict[str, Any]] = field(default_factory=list)
    archived_projects_log: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TaskRecurrenceRule(BaseRecord):
    frequency: str
    interval: int = 1


@dataclass(slots=True)
class Task(BaseRecord):
    id: str
    user_id: str
    task_name: str
    task_type: str
    task_description: str
    created_at: str
    task_deadline: str
    task_notes: str
    updated_at: str
    status: str = "pending"
    completed_at: str | None = None
    is_recurring: bool = False
    recurrence: dict[str, Any] | None = None
    completion_log: list[str] = field(default_factory=list)
    priority: int | str | None = None


@dataclass(slots=True)
class Habit(BaseRecord):
    user_id: str
    habit_name: str
    habit_description: str
    habit_frequency: str
    habit_start_date: str
    habit_notes: str
    completion_log: list[str] = field(default_factory=list)
    streak: int = 0
    best_streak: int = 0
    last_completed_date: str | None = None
    created_at: str = ""
    updated_at: str = ""
    status: str = "pending"
    completed_at: str | None = None


@dataclass(slots=True)
class Project(BaseRecord):
    user_id: str
    project_title: str
    project_description: str
    project_duration: int
    project_created_at: str
    project_deadline: str
    project_notes: str
    created_at: str
    updated_at: str
    status: str = "pending"
    completed_at: str | None = None


@dataclass(slots=True)
class FinanceAccount(BaseRecord):
    id: str
    user_id: str
    account_name: str
    account_type: str
    currency: str
    opening_balance: float
    current_balance: float
    created_at: str
    updated_at: str


@dataclass(slots=True)
class FinanceCategory(BaseRecord):
    id: str
    user_id: str
    name: str
    type: str
    created_at: str


@dataclass(slots=True)
class Transaction(BaseRecord):
    id: str
    user_id: str
    account_id: str
    category_id: str
    txn_type: str
    amount: float
    txn_date: str
    description: str = ""


@dataclass(slots=True)
class Meal(BaseRecord):
    id: str
    user_id: str
    meal_name: str
    meal_type: str
    calories: int
    completion_date: str
    time_of_log: str
    notes: str = ""
    protein: int = 0
    carbs: int = 0
    fats: int = 0
    meal: str | None = None
    legacy_meal_type: str | None = None

    def __post_init__(self) -> None:
        if self.meal is None:
            self.meal = self.meal_name
        if self.legacy_meal_type is None:
            self.legacy_meal_type = self.meal_type

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["meal"] = self.meal_name
        data["meal_name"] = self.meal_name
        data["meal type"] = self.meal_type
        data["meal_type"] = self.meal_type
        data.pop("legacy_meal_type", None)
        return data


@dataclass(slots=True)
class MealPlanMeal(BaseRecord):
    meal_type: str
    foods: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(slots=True)
class MealPlan(BaseRecord):
    id: str
    user_id: str
    entry_type: str
    plan_name: str
    goal: str
    daily_target_calories: int
    daily_target_protein: int
    daily_target_carbs: int
    daily_target_fats: int
    meals: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class StartedMealPlanDay(BaseRecord):
    id: str
    user_id: str
    entry_type: str
    source_plan_id: str
    plan_name: str
    goal: str
    date_started: str
    started_at: str
    daily_target_calories: int
    daily_target_protein: int
    daily_target_carbs: int
    daily_target_fats: int
    meals: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class WorkoutSet(BaseRecord):
    reps: int | None = None
    weight: str | None = None


@dataclass(slots=True)
class WorkoutExercise(BaseRecord):
    name: str
    target_sets: int | None = None
    target_reps: str | None = None
    sets: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class WorkoutBlock(BaseRecord):
    block_type: str
    label: str
    name: str | None = None
    exercises: list[dict[str, Any]] = field(default_factory=list)
    minutes: int | None = None
    intensity: str | None = None


@dataclass(slots=True)
class WorkoutSession(BaseRecord):
    id: str
    user_id: str
    entry_type: str
    name: str
    blocks: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class RoutineDay(BaseRecord):
    day_name: str
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class Routine(BaseRecord):
    id: str
    user_id: str
    entry_type: str
    name: str
    days: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class CalendarEvent(BaseRecord):
    id: str
    user_id: str
    title: str
    event_type: str
    event_date: str
    notes: str = ""
    created_at: str = ""


@dataclass(slots=True)
class FinanceSummary(BaseRecord):
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_balance: float = 0.0
    account_balances: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class StatisticsSummary(BaseRecord):
    tasks: dict[str, Any] = field(default_factory=dict)
    habits: dict[str, Any] = field(default_factory=dict)
    finance: dict[str, Any] = field(default_factory=dict)
    fitness: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DashboardSection(BaseRecord):
    key: str
    title: str
    description: str


@dataclass(slots=True)
class DashboardContext(BaseRecord):
    user: dict[str, Any]
    sections: list[dict[str, Any]] = field(default_factory=list)
    calendar: dict[str, Any] = field(default_factory=dict)
    finance: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
