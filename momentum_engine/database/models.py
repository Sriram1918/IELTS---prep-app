"""
SQLAlchemy ORM Models
All database tables for the Momentum Engine.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    String, Integer, Boolean, DateTime, Date, 
    ForeignKey, Index, CheckConstraint, UniqueConstraint,
    Numeric, Text, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from momentum_engine.database.connection import Base


def generate_uuid():
    return str(uuid4())


class User(Base):
    """User model - core user data."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # IELTS specific
    diagnostic_score: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    current_track: Mapped[str] = mapped_column(String(50), nullable=False)
    # days_until_exam: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Progress tracking
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_practice_time: Mapped[int] = mapped_column(Integer, default=0)  # minutes
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    predicted_band: Mapped[Optional[Decimal]] = mapped_column(Numeric(2, 1))
    
    # Cohort & Ranking
    cohort_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("cohorts.id"))
    # cohort_key: Mapped[Optional[str]] = mapped_column(String(100))
    # cohort_joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # cohort_excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    cohort: Mapped[Optional["Cohort"]] = relationship(back_populates="members")
    progress: Mapped[List["UserProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    streak: Mapped[Optional["Streak"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    metrics: Mapped[List["UserMetric"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ai_budget: Mapped[Optional["UserAIBudget"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_users_cohort", "cohort_id"),
        Index("idx_users_rank", "rank", postgresql_where=rank.isnot(None)),
        Index("idx_users_track", "current_track"),
    )


class Track(Base):
    """Track model - standardized learning tracks."""
    __tablename__ = "tracks"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    focus: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks: Mapped[List["Task"]] = relationship(back_populates="track")


class Task(Base):
    """Task model - learning tasks within tracks."""
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    track_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tracks.id"))
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, writing, speaking, listening
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)  # easy, medium, hard
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    order_in_track: Mapped[int] = mapped_column(Integer, nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    track: Mapped["Track"] = relationship(back_populates="tasks")
    progress: Mapped[List["UserProgress"]] = relationship(back_populates="task")
    
    __table_args__ = (
        Index("idx_tasks_track", "track_id"),
        Index("idx_tasks_type", "type"),
    )


class UserProgress(Base):
    """User progress - tracks task completions."""
    __tablename__ = "user_progress"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"))
    task_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tasks.id"))
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accuracy_score: Mapped[Optional[int]] = mapped_column(Integer)  # 0-100
    time_spent_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="progress")
    task: Mapped["Task"] = relationship(back_populates="progress")
    
    __table_args__ = (
        Index("idx_user_progress_user", "user_id", "completed_at"),
    )


class Cohort(Base):
    """Cohort model - groups of similar learners."""
    __tablename__ = "cohorts"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    cohort_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    skill_tier: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    velocity_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    # track field removed to match DB schema
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    active_member_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_tasks_per_week: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    # avg_accuracy: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members: Mapped[List["User"]] = relationship(back_populates="cohort")
    ghost_data: Mapped[List["CohortGhostData"]] = relationship(back_populates="cohort")
    
    __table_args__ = (
        Index("idx_cohorts_key", "cohort_key"),
        Index("idx_cohorts_skill", "skill_tier"),
    )


class Competition(Base):
    """Competition model - L-AIMS mock tests."""
    __tablename__ = "competitions"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # L-AIMS
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")  # upcoming, active, completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    leaderboard_entries: Mapped[List["LeaderboardEntry"]] = relationship(back_populates="competition")


class LeaderboardEntry(Base):
    """Leaderboard entries for competitions."""
    __tablename__ = "leaderboard_entries"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    competition_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("competitions.id"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    module_scores: Mapped[Optional[dict]] = mapped_column(JSON)  # {"reading": 7.5, "writing": 6.5, ...}
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competition: Mapped["Competition"] = relationship(back_populates="leaderboard_entries")
    
    __table_args__ = (
        UniqueConstraint("competition_id", "user_id", name="uq_leaderboard_comp_user"),
        Index("idx_leaderboard_competition", "competition_id", "rank"),
    )


class Streak(Base):
    """Streak tracking for users."""
    __tablename__ = "streaks"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="streak")


class UserMetric(Base):
    """Daily user metrics (LVS, MACR)."""
    __tablename__ = "user_metrics"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    lvs: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 3))  # Learning Velocity Score
    macr: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # Micro-Action Completion Rate
    crc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 3))  # Cohort Retention Coefficient
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="metrics")
    
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_metrics_date"),
    )


class GhostBenchmark(Base):
    """Historical benchmarks from successful users."""
    __tablename__ = "ghost_benchmarks"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    target_band: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    starting_skill: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_tasks_completed: Mapped[Optional[int]] = mapped_column(Integer)
    avg_practice_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    avg_speaking_tasks: Mapped[Optional[int]] = mapped_column(Integer)
    avg_writing_tasks: Mapped[Optional[int]] = mapped_column(Integer)
    avg_reading_tasks: Mapped[Optional[int]] = mapped_column(Integer)
    avg_listening_tasks: Mapped[Optional[int]] = mapped_column(Integer)
    success_percentile: Mapped[Optional[int]] = mapped_column(Integer)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("target_band", "starting_skill", "day_number", "success_percentile", 
                        name="uq_ghost_benchmark"),
        Index("idx_ghost_benchmarks_lookup", "target_band", "starting_skill", "day_number"),
    )


class CohortGhostData(Base):
    """Real-time cohort stats for ghost comparisons."""
    __tablename__ = "cohort_ghost_data"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    cohort_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("cohorts.id"))
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    active_member_count: Mapped[Optional[int]] = mapped_column(Integer)
    avg_tasks_completed: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    # avg_tasks_this_week: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    avg_practice_minutes: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2))
    # avg_streak: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    median_streak: Mapped[Optional[int]] = mapped_column(Integer)
    top_10_percent_tasks: Mapped[Optional[int]] = mapped_column(Integer)
    top_25_percent_tasks: Mapped[Optional[int]] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cohort: Mapped["Cohort"] = relationship(back_populates="ghost_data")
    
    __table_args__ = (
        UniqueConstraint("cohort_id", "snapshot_date", name="uq_cohort_ghost_date"),
        Index("idx_cohort_ghost_date", "cohort_id", "snapshot_date"),
    )


class AIUsageLog(Base):
    """AI API usage tracking for cost monitoring."""
    __tablename__ = "ai_usage_logs"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(50))
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_total: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("tier IN (2, 3)", name="ck_ai_usage_tier"),
        Index("idx_ai_usage_user_date", "user_id", "timestamp"),
        Index("idx_ai_usage_tier_date", "tier", "timestamp"),
    )


class UserAIBudget(Base):
    """Per-user AI budget tracking."""
    __tablename__ = "user_ai_budgets"
    
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), primary_key=True)
    monthly_budget_usd: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0.50)
    current_month_spend: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0.00)
    total_lifetime_spend: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    tier3_calls_this_week: Mapped[int] = mapped_column(Integer, default=0)
    tier3_calls_this_month: Mapped[int] = mapped_column(Integer, default=0)
    last_tier3_call: Mapped[Optional[datetime]] = mapped_column(DateTime)
    budget_exceeded: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="ai_budget")


class ContentSwap(Base):
    """Content swap history for analytics."""
    __tablename__ = "content_swaps"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    module: Mapped[str] = mapped_column(String(20), nullable=False)
    weakness_type: Mapped[Optional[str]] = mapped_column(String(50))
    original_task_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    intervention_task_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    intervention_completed: Mapped[Optional[bool]] = mapped_column(Boolean)
    intervention_accuracy: Mapped[Optional[int]] = mapped_column(Integer)
    post_swap_accuracy: Mapped[Optional[int]] = mapped_column(Integer)
    improvement_delta: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Pod(Base):
    """Challenge Pods - groups of users on the same track for peer accountability."""
    __tablename__ = "pods"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    track_name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_week: Mapped[int] = mapped_column(Integer, nullable=False)  # Week number of the year
    max_members: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    members: Mapped[List["PodMember"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_pods_track_week", "track_name", "start_week"),
    )


class PodMember(Base):
    """Pod membership with ranking within the pod."""
    __tablename__ = "pod_members"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    pod_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("pods.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pod: Mapped["Pod"] = relationship(back_populates="members")
    
    __table_args__ = (
        UniqueConstraint("pod_id", "user_id", name="uq_pod_member"),
        Index("idx_pod_members_rank", "pod_id", "rank"),
    )
