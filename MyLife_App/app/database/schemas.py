from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ACCOUNT_TYPES = {"cash", "bank", "savings", "ewallet"}
CATEGORY_TYPES = {"income", "expense"}
MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack"}
GOAL_TYPES = {"fat_loss", "maintenance", "muscle_gain"}
BLOCK_TYPES = {"strength", "cardio", "mobility", "conditioning"}
TASK_PRIORITIES = {"low", "medium", "high"}
RECURRENCE_FREQUENCIES = {"daily", "weekly", "monthly"}


class AppBaseSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class LoginSchema(AppBaseSchema):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class SignupSchema(LoginSchema):
    first_name: str = Field(min_length=2, max_length=80)
    last_name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Enter a valid email address")
        return value.lower()

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower()


class PasswordChangeSchema(AppBaseSchema):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class DeleteAccountSchema(AppBaseSchema):
    current_password: str = Field(min_length=6, max_length=128)


class TaskRecurrenceSchema(AppBaseSchema):
    frequency: str
    interval: int = Field(default=1, ge=1, le=365)

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in RECURRENCE_FREQUENCIES:
            raise ValueError(f"Frequency must be one of: {sorted(RECURRENCE_FREQUENCIES)}")
        return normalized


class TaskCreateSchema(AppBaseSchema):
    task_name: str = Field(min_length=2, max_length=120)
    task_type: str = Field(min_length=2, max_length=50)
    task_description: str = Field(default="", max_length=500)
    task_deadline: date | None = None
    task_notes: str = Field(default="", max_length=500)
    recurring: bool = False
    rule: TaskRecurrenceSchema | None = None
    priority: str = Field(default="medium")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in TASK_PRIORITIES:
            raise ValueError(f"Priority must be one of: {sorted(TASK_PRIORITIES)}")
        return normalized

    @model_validator(mode="after")
    def validate_recurrence(self):
        if self.recurring and not self.rule:
            raise ValueError("Recurring tasks require a recurrence rule")
        return self


class TaskUpdateSchema(AppBaseSchema):
    task_name: str = Field(min_length=2, max_length=120)
    task_type: str = Field(min_length=2, max_length=50)
    task_description: str = Field(default="", max_length=500)
    task_deadline: date | None = None
    task_notes: str = Field(default="", max_length=500)


class TaskPrioritySchema(AppBaseSchema):
    priority: int = Field(ge=1, le=5)


class TaskStatusSchema(AppBaseSchema):
    task_name: str = Field(min_length=2, max_length=120)


class HabitCreateSchema(AppBaseSchema):
    habit_name: str = Field(min_length=2, max_length=120)
    habit_description: str = Field(default="", max_length=500)
    habit_frequency: str = Field(min_length=2, max_length=50)
    habit_start_date: date
    habit_notes: str = Field(default="", max_length=500)


class HabitUpdateSchema(AppBaseSchema):
    habit_name: str = Field(min_length=2, max_length=120)
    new_description: str | None = Field(default=None, max_length=500)
    new_frequency: str | None = Field(default=None, max_length=50)
    new_start_date: date | None = None
    new_notes: str | None = Field(default=None, max_length=500)


class HabitStatusSchema(AppBaseSchema):
    habit_name: str = Field(min_length=2, max_length=120)


class ProjectCreateSchema(AppBaseSchema):
    project_title: str = Field(min_length=2, max_length=120)
    project_description: str = Field(default="", max_length=1000)
    project_duration: int = Field(default=1, ge=1)
    project_deadline: date | None = None
    project_notes: str = Field(default="", max_length=500)


class ProjectUpdateSchema(AppBaseSchema):
    project_title: str = Field(min_length=2, max_length=120)
    project_description: str = Field(default="", max_length=1000)
    project_deadline: date | None = None
    project_notes: str = Field(default="", max_length=500)


class ProjectStatusSchema(AppBaseSchema):
    project_title: str = Field(min_length=2, max_length=120)


class AccountCreateSchema(AppBaseSchema):
    account_name: str = Field(min_length=2, max_length=120)
    account_type: str
    currency: str = Field(min_length=3, max_length=10)
    opening_balance: float = Field(ge=0)

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in ACCOUNT_TYPES:
            raise ValueError(f"Account type must be one of: {sorted(ACCOUNT_TYPES)}")
        return normalized

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        return value.upper()


class AccountUpdateSchema(AppBaseSchema):
    account_name: str = Field(min_length=2, max_length=120)
    account_type: str
    currency: str = Field(min_length=3, max_length=10)

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in ACCOUNT_TYPES:
            raise ValueError(f"Account type must be one of: {sorted(ACCOUNT_TYPES)}")
        return normalized

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        return value.upper()


class CategoryCreateSchema(AppBaseSchema):
    name: str = Field(min_length=2, max_length=80)
    category_type: str

    @field_validator("category_type")
    @classmethod
    def validate_category_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in CATEGORY_TYPES:
            raise ValueError(f"Category type must be one of: {sorted(CATEGORY_TYPES)}")
        return normalized


class CategoryUpdateSchema(CategoryCreateSchema):
    pass


class TransactionCreateSchema(AppBaseSchema):
    account_id: str = Field(min_length=1)
    category_id: str = Field(min_length=1)
    txn_type: str = Field(min_length=1)
    amount: float = Field(gt=0)
    txn_date: datetime | date
    description: str = Field(default="", max_length=300)


class TransactionUpdateSchema(TransactionCreateSchema):
    pass


class IncomeCreateSchema(TransactionCreateSchema):
    pass


class ExpenseCreateSchema(TransactionCreateSchema):
    pass


class CalorieGoalSchema(AppBaseSchema):
    goal: int = Field(gt=0)


class MealCreateSchema(AppBaseSchema):
    meal_name: str = Field(min_length=2, max_length=120)
    meal_type: str
    calories: int = Field(gt=0)
    completion_date: date
    time_of_log: datetime | None = None
    notes: str = Field(default="", max_length=500)
    protein: int = Field(default=0, ge=0)
    carbs: int = Field(default=0, ge=0)
    fats: int = Field(default=0, ge=0)

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in MEAL_TYPES:
            raise ValueError(f"Meal type must be one of: {sorted(MEAL_TYPES)}")
        return normalized


class MealUpdateSchema(MealCreateSchema):
    pass


class MealPlanMealSchema(AppBaseSchema):
    meal_type: str
    foods: list[str] = Field(min_length=1)
    notes: str = Field(default="", max_length=500)

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in MEAL_TYPES:
            raise ValueError(f"Meal type must be one of: {sorted(MEAL_TYPES)}")
        return normalized

    @field_validator("foods")
    @classmethod
    def validate_foods(cls, value: list[str]) -> list[str]:
        cleaned = [food.strip() for food in value if str(food).strip()]
        if not cleaned:
            raise ValueError("At least one food item is required")
        return cleaned


class MealPlanCreateSchema(AppBaseSchema):
    plan_name: str = Field(min_length=3, max_length=120)
    goal: str
    daily_target_calories: int = Field(gt=0)
    daily_target_protein: int = Field(ge=0)
    daily_target_carbs: int = Field(ge=0)
    daily_target_fats: int = Field(ge=0)
    meals: list[MealPlanMealSchema] = Field(min_length=1)

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in GOAL_TYPES:
            raise ValueError(f"Goal must be one of: {sorted(GOAL_TYPES)}")
        return normalized


class MealPlanSchema(MealPlanCreateSchema):
    pass


class StartMealPlanDaySchema(AppBaseSchema):
    identifier: str = Field(min_length=1)


class NutritionSummaryQuerySchema(AppBaseSchema):
    calculation_date: date


class WorkoutSetSchema(AppBaseSchema):
    reps: int | None = Field(default=None, ge=1)
    weight: str | None = Field(default=None, max_length=30)


class WorkoutExerciseSchema(AppBaseSchema):
    name: str = Field(min_length=2, max_length=120)
    target_sets: int | None = Field(default=None, ge=1)
    target_reps: str | None = Field(default=None, max_length=30)
    sets: list[WorkoutSetSchema] = Field(default_factory=list)


class WorkoutBlockSchema(AppBaseSchema):
    block_type: str
    label: str = Field(min_length=2, max_length=120)
    name: str | None = Field(default=None, max_length=120)
    exercises: list[WorkoutExerciseSchema] = Field(default_factory=list)
    minutes: int | None = Field(default=None, ge=1)
    intensity: str | None = Field(default=None, max_length=30)

    @field_validator("block_type")
    @classmethod
    def validate_block_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in BLOCK_TYPES:
            raise ValueError(f"Block type must be one of: {sorted(BLOCK_TYPES)}")
        return normalized


class WorkoutSessionCreateSchema(AppBaseSchema):
    name: str = Field(min_length=2, max_length=120)
    blocks: list[WorkoutBlockSchema] = Field(min_length=1)
    notes: str = Field(default="", max_length=500)


class RoutineDaySchema(AppBaseSchema):
    day_name: str = Field(min_length=2, max_length=40)
    blocks: list[WorkoutBlockSchema] = Field(min_length=1)


class RoutineCreateSchema(AppBaseSchema):
    name: str = Field(min_length=2, max_length=120)
    days: list[RoutineDaySchema] = Field(min_length=1)


class RoutineSessionBuildSchema(AppBaseSchema):
    day_name: str = Field(min_length=2, max_length=40)
    routine_name: str | None = Field(default=None, max_length=120)


class CalendarEventCreateSchema(AppBaseSchema):
    title: str = Field(min_length=2, max_length=120)
    event_type: str = Field(min_length=2, max_length=50)
    event_date: datetime | date
    notes: str = Field(default="", max_length=500)

    @field_validator("event_type")
    @classmethod
    def normalize_event_type(cls, value: str) -> str:
        return value.lower()


class MonthSummaryQuerySchema(AppBaseSchema):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)


class YearSummaryQuerySchema(AppBaseSchema):
    year: int = Field(ge=2000, le=2100)
