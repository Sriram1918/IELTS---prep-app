"""
Gamification Service - Streak and Leaderboard Logic
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from momentum_engine.database.models import (
    User, Streak, Cohort, CohortGhostData, GhostBenchmark,
    Competition, LeaderboardEntry
)
from momentum_engine.shared.exceptions import NotFoundError

logger = structlog.get_logger()


class GamificationService:
    """Service for gamification features."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_streak(self, user_id: str) -> Dict[str, Any]:
        """Get user's streak information."""
        
        result = await self.db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        
        if not streak:
            raise NotFoundError("Streak", user_id)
        
        # Determine streak status
        status = "active"
        days_until_rescue = None
        
        if streak.last_activity_date:
            days_since = (date.today() - streak.last_activity_date).days
            if days_since == 0:
                status = "active"
            elif days_since == 1:
                status = "at_risk"
                days_until_rescue = 1
            else:
                status = "broken"
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "last_activity_date": str(streak.last_activity_date) if streak.last_activity_date else None,
            "status": status,
            "days_until_rescue": days_until_rescue
        }
    
    async def update_streak(self, user_id: str) -> Dict[str, Any]:
        """Update streak after task completion."""
        
        result = await self.db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        
        if not streak:
            raise NotFoundError("Streak", user_id)
        
        today = date.today()
        previous_streak = streak.current_streak
        
        if streak.last_activity_date is None:
            # First activity
            streak.current_streak = 1
        elif streak.last_activity_date == today:
            # Already active today - no change
            pass
        elif (today - streak.last_activity_date).days == 1:
            # Consecutive day - increment
            streak.current_streak += 1
        else:
            # Streak broken - reset
            streak.current_streak = 1
        
        # Update longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        streak.last_activity_date = today
        streak.updated_at = datetime.utcnow()
        
        # Check for streak milestones
        milestone_reached = None
        milestones = [7, 14, 30, 60, 90]
        for m in milestones:
            if previous_streak < m <= streak.current_streak:
                milestone_reached = m
                break
        
        logger.info(
            "Streak updated",
            user_id=user_id,
            previous=previous_streak,
            current=streak.current_streak
        )
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "milestone_reached": milestone_reached,
            "message": f"🔥 {streak.current_streak} day streak!" if streak.current_streak > 1 else "Great start!"
        }
    
    async def get_cohort_info(self, user_id: str) -> Dict[str, Any]:
        """Get user's cohort information."""
        
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        if not user.cohort_id:
            return {
                "cohort_assigned": False,
                "message": "Cohort will be assigned after 3 days of activity"
            }
        
        cohort_result = await self.db.execute(
            select(Cohort).where(Cohort.id == user.cohort_id)
        )
        cohort = cohort_result.scalar_one_or_none()
        
        if not cohort:
            return {"cohort_assigned": False}
        
        return {
            "cohort_assigned": True,
            "cohort_key": cohort.cohort_key,
            "member_count": cohort.member_count,
            "active_member_count": cohort.active_member_count,
            "skill_tier": float(cohort.skill_tier),
            "velocity_tier": cohort.velocity_tier,
            "avg_tasks_per_week": float(cohort.avg_tasks_per_week) if cohort.avg_tasks_per_week else None
        }
    
    async def get_ghost_data(self, user_id: str) -> Dict[str, Any]:
        """Get peer comparison ghost data."""
        
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        day_number = (date.today() - user.created_at.date()).days + 1
        starting_skill = round(float(user.diagnostic_score) * 2) / 2
        
        # Get benchmark
        benchmark_result = await self.db.execute(
            select(GhostBenchmark).where(
                GhostBenchmark.target_band == Decimal("7.5"),
                GhostBenchmark.starting_skill == Decimal(str(starting_skill)),
                GhostBenchmark.day_number == min(day_number, 90),
                GhostBenchmark.success_percentile == 25
            )
        )
        benchmark = benchmark_result.scalar_one_or_none()
        
        # Get cohort data
        cohort_data = None
        if user.cohort_id:
            cohort_result = await self.db.execute(
                select(CohortGhostData).where(
                    CohortGhostData.cohort_id == user.cohort_id,
                    CohortGhostData.snapshot_date == date.today()
                )
            )
            cohort_data = cohort_result.scalar_one_or_none()
        
        response = {
            "user_stats": {
                "tasks_completed": user.tasks_completed,
                "practice_minutes": user.total_practice_time,
                "current_streak": user.current_streak,
                "day_in_journey": day_number
            },
            "success_benchmark": None,
            "cohort_comparison": None
        }
        
        if benchmark:
            response["success_benchmark"] = {
                "target_band": 7.5,
                "day_number": day_number,
                "benchmark_tasks": benchmark.avg_tasks_completed,
                "message": self._format_benchmark_message(
                    user.tasks_completed,
                    benchmark.avg_tasks_completed,
                    day_number
                )
            }
        
        if cohort_data:
            response["cohort_comparison"] = {
                "cohort_size": cohort_data.active_member_count,
                "avg_tasks_completed": float(cohort_data.avg_tasks_completed) if cohort_data.avg_tasks_completed else None,
                "message": self._format_cohort_message(
                    user.tasks_completed,
                    float(cohort_data.avg_tasks_completed) if cohort_data.avg_tasks_completed else 0
                )
            }
        
        return response
    
    def _format_benchmark_message(self, user_tasks: int, benchmark_tasks: int, day: int) -> str:
        """Format ghost message for success benchmark."""
        if not benchmark_tasks:
            return None
        
        if user_tasks >= benchmark_tasks:
            return f"Great progress! Users who scored 7.5+ had completed {benchmark_tasks} tasks by Day {day}. You're at {user_tasks}! 🎯"
        else:
            return f"Users who scored 7.5+ had completed {benchmark_tasks} tasks by Day {day}. You're at {user_tasks}."
    
    def _format_cohort_message(self, user_tasks: int, cohort_avg: float) -> str:
        """Format ghost message for cohort comparison."""
        if not cohort_avg:
            return None
        
        cohort_avg = int(cohort_avg)
        if user_tasks >= cohort_avg:
            return f"You're ahead of your cohort! Average is {cohort_avg} tasks, you're at {user_tasks}. 💪"
        else:
            return f"Your cohort is averaging {cohort_avg} tasks. You're at {user_tasks}. Catch up?"
    
    async def get_leaderboard(self, competition_id: Optional[str], limit: int) -> Dict[str, Any]:
        """Get leaderboard rankings."""
        
        if competition_id:
            result = await self.db.execute(
                select(LeaderboardEntry)
                .where(LeaderboardEntry.competition_id == competition_id)
                .order_by(LeaderboardEntry.rank)
                .limit(limit)
            )
        else:
            # Get latest active competition
            comp_result = await self.db.execute(
                select(Competition)
                .where(Competition.status == "active")
                .order_by(Competition.start_date.desc())
                .limit(1)
            )
            competition = comp_result.scalar_one_or_none()
            
            if not competition:
                return {"leaderboard": [], "competition": None}
            
            result = await self.db.execute(
                select(LeaderboardEntry)
                .where(LeaderboardEntry.competition_id == competition.id)
                .order_by(LeaderboardEntry.rank)
                .limit(limit)
            )
        
        entries = result.scalars().all()
        
        return {
            "leaderboard": [
                {
                    "rank": e.rank,
                    "user_id": e.user_id,
                    "score": float(e.score),
                    "module_scores": e.module_scores
                }
                for e in entries
            ]
        }
    
    async def get_user_rank(self, user_id: str, competition_id: Optional[str]) -> Dict[str, Any]:
        """Get user's rank in leaderboard."""
        
        if not competition_id:
            comp_result = await self.db.execute(
                select(Competition)
                .where(Competition.status == "active")
                .order_by(Competition.start_date.desc())
                .limit(1)
            )
            competition = comp_result.scalar_one_or_none()
            competition_id = competition.id if competition else None
        
        if not competition_id:
            return {"rank": None, "message": "No active competition"}
        
        result = await self.db.execute(
            select(LeaderboardEntry)
            .where(
                LeaderboardEntry.competition_id == competition_id,
                LeaderboardEntry.user_id == user_id
            )
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            return {"rank": None, "message": "User has not participated"}
        
        return {
            "rank": entry.rank,
            "score": float(entry.score),
            "module_scores": entry.module_scores
        }
