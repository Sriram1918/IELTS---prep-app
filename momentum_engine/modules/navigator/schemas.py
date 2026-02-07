"""Navigator module schemas - Pydantic models for request/response."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


class DiagnosticRequest(BaseModel):
    """Request for diagnostic test completion."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    diagnostic_score: float = Field(..., ge=4.0, le=9.0)
    days_until_exam: int = Field(..., ge=7)
    test_type: str = Field(default="academic")  # academic or general
    weak_module: Optional[str] = None  # reading, writing, speaking, listening
    daily_availability_minutes: int = Field(default=45, ge=10)
    weekend_availability: bool = True
    
    @field_validator("diagnostic_score")
    @classmethod
    def validate_band_score(cls, v):
        # IELTS scores are in 0.5 increments
        if v % 0.5 != 0:
            # Round to nearest 0.5
            v = round(v * 2) / 2
        return v


class TaskPreview(BaseModel):
    """Task preview for daily plan."""
    
    id: str
    title: str
    type: str
    difficulty: str
    estimated_minutes: int
    description: Optional[str] = None


class DiagnosticResponse(BaseModel):
    """Response after diagnostic completion."""
    
    user_id: str
    assigned_track: str
    track_duration_weeks: int
    daily_commitment_minutes: int
    exam_date: date
    predicted_band: float
    daily_plan_preview: List[TaskPreview]
    cohort_assigned: bool = False
    message: str


class StreakInfo(BaseModel):
    """Streak information."""
    
    current_streak: int
    longest_streak: int
    streak_status: str  # "active", "at_risk", "broken"
    days_until_rescue: Optional[int] = None


class ProgressSummary(BaseModel):
    """User progress summary."""
    
    tasks_completed: int
    total_practice_minutes: int
    predicted_band: float
    day_in_journey: int
    days_until_exam: int
    completion_percentage: float


class GhostComparison(BaseModel):
    """Ghost data comparison."""
    
    benchmark_type: str  # "success_benchmark" or "cohort"
    comparison_value: Optional[float]
    user_value: float
    message: str
    percentile: Optional[int] = None


class DashboardResponse(BaseModel):
    """Full dashboard response."""
    
    user_name: str
    current_track: str
    streak: StreakInfo
    progress: ProgressSummary
    todays_tasks: List[TaskPreview]
    ghost_comparison: Optional[GhostComparison] = None
    notifications: List[str] = []


class UserTasksResponse(BaseModel):
    """Tasks for a specific date."""
    
    date: date
    tasks: List[TaskPreview]
    completed_count: int
    total_count: int


class TrackInfo(BaseModel):
    """Track information."""
    
    id: str
    name: str
    duration_weeks: int
    daily_minutes: int
    tasks_per_day: int
    focus: str
    description: Optional[str]
