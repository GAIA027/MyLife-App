from sqlalchemy import Boolean, Column, Float, Index, Integer, String, Text, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    daily_calorie_goal = Column(Integer, default=0)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    finance_accounts = relationship("FinanceAccount", back_populates="user", cascade="all, delete-orphan")
    finance_categories = relationship("FinanceCategory", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    workout_sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete-orphan")
    routines = relationship("Routine", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan" )
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    scheduled_activities = relationship("ScheduledActivity", back_populates="user", cascade="all, delete-orphan")



class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    task_name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    task_description = Column(Text, default="")
    task_deadline = Column(String, default="")
    task_notes = Column(Text, default="")
    status = Column(String, default="pending")
    priority = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence = Column(JSON, nullable=True)
    completion_log = Column(JSON, default=list)
    completed_at = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="tasks")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    habit_name = Column(String, nullable=False)
    habit_description = Column(Text, default="")
    habit_frequency = Column(String, default="")
    habit_start_date = Column(String, default="")
    habit_notes = Column(Text, default="")
    completion_log = Column(JSON, default=list)
    streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_completed_date = Column(String, nullable=True)
    status = Column(String, default="pending")
    completed_at = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="habits")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_title = Column(String, nullable=False)
    project_description = Column(Text, default="")
    project_duration = Column(Integer, default=0)
    project_deadline = Column(String, default="")
    project_notes = Column(Text, default="")
    status = Column(String, default="pending")
    completed_at = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="projects")


class FinanceAccount(Base):
    __tablename__ = "finance_accounts"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    currency = Column(String, default="USD")
    opening_balance = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    __table_args__ = (Index("ix_finance_accounts_user_id", "user_id"),)

    user = relationship("User", back_populates="finance_accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class FinanceCategory(Base):
    __tablename__ = "finance_categories"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(String, default="")

    __table_args__ = (Index("ix_finance_categories_user_id", "user_id"),)

    user = relationship("User", back_populates="finance_categories")
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, ForeignKey("finance_accounts.id"), nullable=False)
    category_id = Column(String, ForeignKey("finance_categories.id"), nullable=False)
    budget_id = Column(String, ForeignKey("budgets.id"), nullable=True)
    txn_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    txn_date = Column(String, default="")
    description = Column(Text, default="")

    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_account_id", "account_id"),
        Index("ix_transactions_budget_id", "budget_id"),
    )

    user = relationship("User", back_populates="transactions")
    account = relationship("FinanceAccount", back_populates="transactions")
    category = relationship("FinanceCategory", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("finance_categories.id"), nullable=True)
    name = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    period = Column(String, default="monthly")
    start_date = Column(String, default="")
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    __table_args__ = (Index("ix_budgets_user_id", "user_id"),)

    user = relationship("User", back_populates="budgets")
class Meal(Base):
    __tablename__ = "meals"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    meal_name = Column(String, nullable=False)
    meal_type = Column(String, nullable=False)
    calories = Column(Integer, default=0)
    protein = Column(Integer, default=0)
    carbs = Column(Integer, default=0)
    fats = Column(Integer, default=0)
    completion_date = Column(String, default="")
    time_of_log = Column(String, default="")
    notes = Column(Text, default="")

    user = relationship("User", back_populates="meals")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    entry_type = Column(String, default="meal_plan")
    plan_name = Column(String, nullable=False)
    goal = Column(String, default="")
    daily_target_calories = Column(Integer, default=0)
    daily_target_protein = Column(Integer, default=0)
    daily_target_carbs = Column(Integer, default=0)
    daily_target_fats = Column(Integer, default=0)
    meals = Column(JSON, default=list)
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="meal_plans")


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    entry_type = Column(String, default="workout_session")
    name = Column(String, nullable=False)
    blocks = Column(JSON, default=list)
    notes = Column(Text, default="")
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="workout_sessions")


class Routine(Base):
    __tablename__ = "routines"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    entry_type = Column(String, default="routine")
    name = Column(String, nullable=False)
    days = Column(JSON, default=list)
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="routines")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    event_date = Column(String, default="")
    notes = Column(Text, default="")
    created_at = Column(String, default="")

    user = relationship("User", back_populates="calendar_events")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(String, default="")
    updated_at = Column(String, default="")

    user = relationship("User", back_populates="schedules")
    activities = relationship("ScheduledActivity", back_populates="schedule", cascade="all, delete-orphan")


class ScheduledActivity(Base):
    __tablename__ = "scheduled_activities"

    id = Column(String, primary_key=True)
    schedule_id = Column(String, ForeignKey("schedules.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    activity_name = Column(String, nullable=False)
    date = Column(String, default="")
    start_time = Column(String, default="")
    end_time = Column(String, default="")

    schedule = relationship("Schedule", back_populates="activities")
    user = relationship("User", back_populates="scheduled_activities")


