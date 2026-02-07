"""
Navigator Service - Track Assignment & Planning Logic
Contains Tier 1 (rule-based) track assignment.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from momentum_engine.database.models import User, Track, Task, Streak, Cohort, ContentSwap
from momentum_engine.modules.navigator.schemas import (
    DiagnosticRequest,
    DiagnosticResponse,
    DashboardResponse,
    UserTasksResponse,
    TaskPreview,
    StreakInfo,
    ProgressSummary,
    TrackInfo,
)
from momentum_engine.shared.exceptions import NotFoundError, ValidationError

logger = structlog.get_logger()


class NavigatorService:
    """Service for track assignment and daily planning."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def assign_track(
        self,
        diagnostic_score: float,
        days_until_exam: int,
        test_type: str = "academic",
        weak_module: Optional[str] = None,
        daily_availability_minutes: int = 45,
        weekend_availability: bool = True
    ) -> str:
        """
        Tier 1 AI: Pure rule-based track assignment.
        $0 cost - no LLM calls.
        
        Rules defined in docs/tracks_definition.md
        """
        # Priority 1: Time-critical assignments
        if days_until_exam < 21:
            if test_type == "academic":
                return "academic_fast_track"
            else:
                return "general_fast_track"
        
        # Priority 2: Score-based assignments
        if diagnostic_score >= 6.5:
            return "sprint"
        
        if diagnostic_score < 5.5:
            return "foundation"
        
        # Priority 3: Module-specific weakness
        if weak_module == "writing":
            return "writing_focus"
        if weak_module == "speaking":
            return "speaking_focus"
        
        # Priority 4: Availability-based
        if daily_availability_minutes < 20 and weekend_availability:
            return "weekend_warrior"
        
        if daily_availability_minutes >= 90:
            return "intensive"
        
        if daily_availability_minutes < 30:
            return "professional_marathon"
        
        # Priority 5: Timeline-based defaults
        if days_until_exam > 90:
            return "foundation"
        
        if days_until_exam > 45:
            return "balanced"
        
        return "professional_marathon"
    
    async def process_diagnostic(self, request: DiagnosticRequest) -> DiagnosticResponse:
        """Process diagnostic and create user with assigned track."""
        
        # Check if user already exists - if so, return their existing data (simple login)
        existing_result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        existing_user = existing_result.scalar_one_or_none()
        if existing_user:
            # Return existing user data (acts as login)
            return DiagnosticResponse(
                user_id=existing_user.id,
                assigned_track=existing_user.current_track,
                track_duration_weeks=8,
                daily_commitment_minutes=45,
                exam_date=existing_user.exam_date,
                predicted_band=float(existing_user.predicted_band or request.diagnostic_score),
                daily_plan_preview=[],
                message=f"Welcome back! Continuing with your {existing_user.current_track.replace('_', ' ')} track."
            )
        
        # Assign track using Tier 1 rules
        track_name = self.assign_track(
            diagnostic_score=request.diagnostic_score,
            days_until_exam=request.days_until_exam,
            test_type=request.test_type,
            weak_module=request.weak_module,
            daily_availability_minutes=request.daily_availability_minutes,
            weekend_availability=request.weekend_availability
        )
        
        # Get track details
        track_result = await self.db.execute(
            select(Track).where(Track.name == track_name)
        )
        track = track_result.scalar_one_or_none()
        
        # If track doesn't exist in DB, use defaults
        track_duration = track.duration_weeks if track else 8
        daily_minutes = track.daily_minutes if track else 45
        
        # Calculate exam date
        exam_date = date.today() + timedelta(days=request.days_until_exam)
        
        # Create user
        user = User(
            name=request.name,
            email=request.email,
            diagnostic_score=Decimal(str(request.diagnostic_score)),
            current_track=track_name,
            exam_date=exam_date,
            predicted_band=Decimal(str(request.diagnostic_score)),
            created_at=datetime.utcnow(),
        )
        self.db.add(user)
        await self.db.flush()  # Flush to get user.id
        
        # Create streak record
        streak = Streak(
            user_id=user.id,
            current_streak=0,
            longest_streak=0
        )
        self.db.add(streak)
        
        await self.db.flush()
        
        # Get initial tasks for preview
        tasks_preview = await self._get_initial_tasks(track_name, 3)
        
        logger.info(
            "User created with track assignment",
            user_id=user.id,
            track=track_name,
            diagnostic_score=request.diagnostic_score
        )
        
        return DiagnosticResponse(
            user_id=user.id,
            assigned_track=track_name,
            track_duration_weeks=track_duration,
            daily_commitment_minutes=daily_minutes,
            exam_date=exam_date,
            predicted_band=request.diagnostic_score,
            daily_plan_preview=tasks_preview,
            cohort_assigned=False,
            message=f"Welcome! You've been assigned to the {track_name.replace('_', ' ').title()} track."
        )
    
    async def get_dashboard(self, user_id: str) -> DashboardResponse:
        """Get user's daily dashboard."""
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        
        # Get streak
        streak_result = await self.db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streak_record = streak_result.scalar_one_or_none()
        
        # Calculate streak status
        streak_status = "active"
        days_until_rescue = None
        if streak_record and streak_record.last_activity_date:
            days_since = (date.today() - streak_record.last_activity_date).days
            if days_since == 0:
                streak_status = "active"
            elif days_since == 1:
                streak_status = "at_risk"
                days_until_rescue = 1
            else:
                streak_status = "broken"
        
        # Calculate progress
        day_in_journey = (date.today() - user.created_at.date()).days + 1
        days_until_exam = (user.exam_date - date.today()).days
        
        # Get today's tasks
        todays_tasks = await self._get_tasks_for_user(user.current_track, day_in_journey)
        
        return DashboardResponse(
            user_name=user.name,
            current_track=user.current_track,
            streak=StreakInfo(
                current_streak=streak_record.current_streak if streak_record else 0,
                longest_streak=streak_record.longest_streak if streak_record else 0,
                streak_status=streak_status,
                days_until_rescue=days_until_rescue
            ),
            progress=ProgressSummary(
                tasks_completed=user.tasks_completed,
                total_practice_minutes=user.total_practice_time,
                predicted_band=float(user.predicted_band) if user.predicted_band else float(user.diagnostic_score),
                day_in_journey=day_in_journey,
                days_until_exam=max(0, days_until_exam),
                completion_percentage=min(100, (day_in_journey / max(1, day_in_journey + days_until_exam)) * 100)
            ),
            todays_tasks=todays_tasks,
            ghost_comparison=None,  # Will be populated by cohort service
            notifications=[]
        )
    
    async def get_tasks_for_date(self, user_id: str, target_date: date) -> UserTasksResponse:
        """Get tasks for a specific date."""
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        
        day_in_journey = (target_date - user.created_at.date()).days + 1
        tasks = await self._get_tasks_for_user(user.current_track, day_in_journey)
        
        return UserTasksResponse(
            date=target_date,
            tasks=tasks,
            completed_count=0,  # Would check user_progress
            total_count=len(tasks)
        )
    
    async def list_tracks(self) -> List[TrackInfo]:
        """List all available tracks."""
        
        result = await self.db.execute(select(Track))
        tracks = result.scalars().all()
        
        return [
            TrackInfo(
                id=t.id,
                name=t.name,
                duration_weeks=t.duration_weeks,
                daily_minutes=t.daily_minutes,
                tasks_per_day=t.tasks_per_day,
                focus=t.focus,
                description=t.description
            )
            for t in tracks
        ]
    
    async def _get_initial_tasks(self, track_name: str, limit: int = 3) -> List[TaskPreview]:
        """Get initial tasks for a track."""
        
        result = await self.db.execute(
            select(Task)
            .join(Track)
            .where(Track.name == track_name)
            .order_by(Task.order_in_track)
            .limit(limit)
        )
        tasks = result.scalars().all()
        
        return [
            TaskPreview(
                id=t.id,
                title=t.title,
                type=t.type,
                difficulty=t.difficulty,
                estimated_minutes=t.estimated_minutes,
                description=t.description
            )
            for t in tasks
        ]
    
    async def _get_tasks_for_user(self, track_name: str, day: int) -> List[TaskPreview]:
        """Get tasks for a specific day in the track."""
        
        # Get track to determine tasks per day
        track_result = await self.db.execute(
            select(Track).where(Track.name == track_name)
        )
        track = track_result.scalar_one_or_none()
        tasks_per_day = track.tasks_per_day if track else 3
        
        # Calculate which tasks to show based on day
        offset = ((day - 1) * tasks_per_day) % 50  # Cycle through tasks
        
        result = await self.db.execute(
            select(Task)
            .join(Track)
            .where(Track.name == track_name)
            .order_by(Task.order_in_track)
            .offset(offset)
            .limit(tasks_per_day)
        )
        tasks = result.scalars().all()
        
        return [
            TaskPreview(
                id=t.id,
                title=t.title,
                type=t.type,
                difficulty=t.difficulty,
                estimated_minutes=t.estimated_minutes,
                description=t.description
            )
            for t in tasks
        ]
    
    async def get_track_by_name(self, track_name: str) -> Optional[dict]:
        """Get detailed track information including success metrics."""
        result = await self.db.execute(
            select(Track).where(Track.name == track_name)
        )
        track = result.scalar_one_or_none()
        
        if not track:
            return None
        
        return {
            "name": track.name,
            "description": track.description,
            "duration_weeks": track.duration_weeks,
            "daily_minutes": track.daily_minutes,
            "tasks_per_day": track.tasks_per_day,
            "success_rate": float(getattr(track, 'success_rate', 0.85) or 0.85),
            "avg_band_improvement": float(getattr(track, 'avg_band_improvement', 1.0) or 1.0),
            "total_completions": getattr(track, 'total_completions', 0) or 0
        }
    
    async def count_users_on_track(self, track_name: str) -> int:
        """Count how many users are currently on a specific track."""
        result = await self.db.execute(
            select(func.count(User.id)).where(User.current_track == track_name)
        )
        count = result.scalar()
        return count or 0
    
    async def check_performance_and_swap(
        self, 
        user_id: str, 
        completed_task_id: str,
        score: int,  # Score out of 100
        module: str  # reading, writing, speaking, listening
    ) -> Optional[dict]:
        """
        Check if user is struggling and swap next task if needed.
        Tier 1 rule: If score < 60%, swap next day's task for intervention.
        """
        FAILING_THRESHOLD = 60
        
        if score >= FAILING_THRESHOLD:
            return None  # No swap needed
        
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return None
        
        # Find an intervention task for this module
        intervention_task = await self._get_intervention_task(module, user.current_track)
        
        if not intervention_task:
            logger.warning(
                "No intervention task found",
                module=module,
                track=user.current_track
            )
            return None
        
        # Log the swap
        swap = ContentSwap(
            user_id=user_id,
            module=module,
            weakness_type=f"low_score_{score}",
            original_task_id=completed_task_id,
            intervention_task_id=intervention_task.id
        )
        self.db.add(swap)
        await self.db.commit()
        
        logger.info(
            "Task swap triggered",
            user_id=user_id,
            module=module,
            score=score,
            intervention_id=intervention_task.id
        )
        
        return {
            "swapped": True,
            "reason": f"Score {score}% below threshold ({FAILING_THRESHOLD}%)",
            "module": module,
            "intervention_task": {
                "id": str(intervention_task.id),
                "title": intervention_task.title,
                "type": intervention_task.type,
                "description": intervention_task.description
            }
        }
    
    async def _get_intervention_task(self, module: str, track_name: str) -> Optional[Task]:
        """Get an intervention/remediation task for a specific module."""
        # First try to find a strategy task for this module
        result = await self.db.execute(
            select(Task)
            .join(Track)
            .where(
                Track.name == track_name,
                Task.type.in_(["strategy", "remediation", "practice"]),
                Task.title.ilike(f"%{module}%strategy%") | 
                Task.title.ilike(f"%{module}%intervention%") |
                Task.title.ilike(f"%{module}%practice%")
            )
            .limit(1)
        )
        task = result.scalar_one_or_none()
        
        if task:
            return task
        
        # Fallback: get any task for this module
        result = await self.db.execute(
            select(Task)
            .join(Track)
            .where(
                Track.name == track_name,
                Task.title.ilike(f"%{module}%")
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_user_swap_history(self, user_id: str) -> List[dict]:
        """Get history of task swaps for a user."""
        result = await self.db.execute(
            select(ContentSwap)
            .where(ContentSwap.user_id == user_id)
            .order_by(ContentSwap.created_at.desc())
            .limit(10)
        )
        swaps = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "module": s.module,
                "weakness_type": s.weakness_type,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "intervention_completed": s.intervention_completed,
                "improvement_delta": float(s.improvement_delta) if s.improvement_delta else None
            }
            for s in swaps
        ]

