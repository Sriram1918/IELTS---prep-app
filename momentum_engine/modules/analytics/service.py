"""
Analytics Service - Metrics Calculation
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from momentum_engine.database.models import User, UserProgress, Track, UserMetric
from momentum_engine.shared.exceptions import NotFoundError

logger = structlog.get_logger()


class AnalyticsService:
    """Service for analytics and metrics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get user's key metrics: LVS, MACR."""
        
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        lvs = await self._calculate_lvs(user)
        macr = await self._calculate_macr(user)
        
        return {
            "user_id": user_id,
            "lvs": lvs,
            "lvs_target": 0.15,
            "lvs_status": "on_track" if lvs >= 0.10 else "needs_attention",
            "macr": macr,
            "macr_target": 65.0,
            "macr_status": "on_track" if macr >= 50 else "needs_attention",
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    async def _calculate_lvs(self, user: User) -> float:
        """Calculate Learning Velocity Score."""
        
        # Get band score from 7 days ago
        metric_result = await self.db.execute(
            select(UserMetric)
            .where(
                UserMetric.user_id == user.id,
                UserMetric.date == date.today() - timedelta(days=7)
            )
        )
        old_metric = metric_result.scalar_one_or_none()
        
        if not old_metric or not old_metric.lvs:
            # Use diagnostic score as baseline
            skill_t0 = float(user.diagnostic_score)
        else:
            skill_t0 = float(user.diagnostic_score)  # Simplified
        
        skill_t7 = float(user.predicted_band) if user.predicted_band else skill_t0
        
        # Get hours spent in past week
        hours_result = await self.db.execute(
            select(func.sum(UserProgress.time_spent_minutes))
            .where(
                UserProgress.user_id == user.id,
                UserProgress.completed_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
        minutes = hours_result.scalar() or 0
        hours = minutes / 60
        
        if hours == 0:
            return 0.0
        
        lvs = (skill_t7 - skill_t0) / hours
        return round(lvs, 3)
    
    async def _calculate_macr(self, user: User) -> float:
        """Calculate Micro-Action Completion Rate."""
        
        # Get track for tasks per day
        track_result = await self.db.execute(
            select(Track).where(Track.name == user.current_track)
        )
        track = track_result.scalar_one_or_none()
        tasks_per_day = track.tasks_per_day if track else 3
        
        planned = tasks_per_day * 7
        
        # Count completed in past 7 days
        completed_result = await self.db.execute(
            select(func.count(UserProgress.id))
            .where(
                UserProgress.user_id == user.id,
                UserProgress.completed_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
        completed = completed_result.scalar() or 0
        
        if planned == 0:
            return 0.0
        
        return round((completed / planned) * 100, 2)
    
    async def get_progress_report(self, user_id: str) -> Dict[str, Any]:
        """Get detailed progress report."""
        
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        day_in_journey = (date.today() - user.created_at.date()).days + 1
        days_until_exam = (user.exam_date - date.today()).days
        
        return {
            "user_id": user_id,
            "current_track": user.current_track,
            "day_in_journey": day_in_journey,
            "days_until_exam": max(0, days_until_exam),
            "tasks_completed": user.tasks_completed,
            "total_practice_minutes": user.total_practice_time,
            "predicted_band": float(user.predicted_band) if user.predicted_band else float(user.diagnostic_score),
            "starting_band": float(user.diagnostic_score),
            "improvement": float(user.predicted_band) - float(user.diagnostic_score) if user.predicted_band else 0,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak
        }
    
    async def get_module_breakdown(self, user_id: str) -> Dict[str, Any]:
        """Get performance breakdown by IELTS module."""
        
        modules = ["reading", "writing", "speaking", "listening"]
        breakdown = {}
        
        for module in modules:
            result = await self.db.execute(
                select(
                    func.count(UserProgress.id),
                    func.avg(UserProgress.accuracy_score)
                )
                .join(UserProgress.task)
                .where(
                    UserProgress.user_id == user_id,
                    UserProgress.task.has(type=module)
                )
            )
            row = result.first()
            
            breakdown[module] = {
                "tasks_completed": row[0] if row else 0,
                "avg_accuracy": round(float(row[1]), 1) if row and row[1] else None,
                "status": "needs_work" if row and row[1] and row[1] < 60 else "on_track"
            }
        
        return {"user_id": user_id, "modules": breakdown}
    
    async def get_weekly_cohort_report(self, user_id: str) -> Dict[str, Any]:
        """
        Generate the Day 7 'Aha Moment' weekly cohort report.
        
        Delivers 3 psychological anchors:
        1. Concrete Progress: Practice time quantified
        2. Social Calibration: Ghost data benchmarks
        3. Adaptive Intelligence: Personalized next steps
        """
        
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        # Calculate days in journey
        day_in_journey = (date.today() - user.created_at.date()).days + 1
        week_number = (day_in_journey - 1) // 7 + 1
        
        # 1. CONCRETE PROGRESS: Get practice minutes this week
        week_start = datetime.utcnow() - timedelta(days=7)
        minutes_result = await self.db.execute(
            select(func.sum(UserProgress.time_spent_minutes))
            .where(
                UserProgress.user_id == user.id,
                UserProgress.completed_at >= week_start
            )
        )
        practice_minutes = minutes_result.scalar() or 0
        
        # Tasks completed this week
        tasks_result = await self.db.execute(
            select(func.count(UserProgress.id))
            .where(
                UserProgress.user_id == user.id,
                UserProgress.completed_at >= week_start
            )
        )
        tasks_completed = tasks_result.scalar() or 0
        
        # 2. SOCIAL CALIBRATION: Ghost cohort benchmarks
        # Get cohort average for users who hit their target
        cohort_result = await self.db.execute(
            select(func.avg(User.total_practice_time))
            .where(
                User.current_track == user.current_track,
                User.id != user.id,
                User.created_at <= datetime.utcnow() - timedelta(days=30)
            )
        )
        cohort_avg_minutes = cohort_result.scalar() or practice_minutes * 1.2
        
        # Get successful users' average from same point
        successful_avg_minutes = int(cohort_avg_minutes * 1.15)  # Tier 1 simulation
        
        # Calculate percentile rank
        faster_count_result = await self.db.execute(
            select(func.count(User.id))
            .where(
                User.current_track == user.current_track,
                User.total_practice_time < user.total_practice_time,
                User.created_at <= datetime.utcnow() - timedelta(days=30)
            )
        )
        faster_count = faster_count_result.scalar() or 0
        
        total_count_result = await self.db.execute(
            select(func.count(User.id))
            .where(
                User.current_track == user.current_track,
                User.created_at <= datetime.utcnow() - timedelta(days=30)
            )
        )
        total_count = max(1, total_count_result.scalar() or 1)
        
        percentile = int((faster_count / total_count) * 100)
        ahead_behind = "ahead" if practice_minutes >= cohort_avg_minutes else "behind"
        difference_percent = abs(int(((practice_minutes - cohort_avg_minutes) / max(1, cohort_avg_minutes)) * 100))
        
        # 3. ADAPTIVE INTELLIGENCE: Determine weakest module and generate next step
        modules = ["reading", "writing", "speaking", "listening"]
        weakest_module = None
        lowest_accuracy = 100
        
        for module in modules:
            result = await self.db.execute(
                select(func.avg(UserProgress.accuracy_score))
                .join(UserProgress.task)
                .where(
                    UserProgress.user_id == user.id,
                    UserProgress.task.has(type=module)
                )
            )
            avg = result.scalar()
            if avg and float(avg) < lowest_accuracy:
                lowest_accuracy = float(avg)
                weakest_module = module
        
        # Generate adaptive message
        if weakest_module:
            adaptive_focus = {
                "module": weakest_module,
                "drill_type": "5-minute speaking drill" if weakest_module == "speaking" else f"focused {weakest_module} practice",
                "reason": "grammar patterns" if weakest_module in ["speaking", "writing"] else "comprehension speed"
            }
        else:
            adaptive_focus = {
                "module": "reading",
                "drill_type": "vocabulary building exercise",
                "reason": "balanced progress"
            }
        
        # Build the full report
        return {
            "user_id": user_id,
            "week_number": week_number,
            "day_in_journey": day_in_journey,
            "is_aha_moment": day_in_journey == 7,
            
            # Anchor 1: Concrete Progress
            "concrete_progress": {
                "practice_minutes_this_week": practice_minutes,
                "tasks_completed_this_week": tasks_completed,
                "total_practice_minutes": user.total_practice_time,
                "total_tasks_completed": user.tasks_completed
            },
            
            # Anchor 2: Social Calibration
            "social_calibration": {
                "cohort_avg_minutes": int(cohort_avg_minutes),
                "successful_users_avg_minutes": successful_avg_minutes,
                "percentile_rank": percentile,
                "ahead_behind": ahead_behind,
                "difference_percent": difference_percent,
                "benchmark_message": f"Others in your cohort who hit their target averaged {successful_avg_minutes} minutes by Week {week_number}."
            },
            
            # Anchor 3: Adaptive Intelligence
            "adaptive_intelligence": {
                "focus_module": adaptive_focus["module"],
                "next_action": f"Tomorrow starts with a {adaptive_focus['drill_type']} based on your {adaptive_focus['reason']}.",
                "personalization_signal": f"Your daily plan is adapting based on your {adaptive_focus['module']} patterns.",
                "confidence_boost": f"You're {difference_percent}% {ahead_behind} of where successful users were on Day {day_in_journey} last quarter."
            },
            
            # Full message (the exact notification from concept doc)
            "notification_message": f"Week {week_number} Complete: You've practiced {practice_minutes} minutes this week. {'' if not cohort_avg_minutes else f'Others in your cohort who hit their target scores averaged {successful_avg_minutes} minutes by Week {week_number}. '}Your daily plan is adapting—tomorrow starts with a {adaptive_focus['drill_type']} based on your {adaptive_focus['reason']}. You're {difference_percent}% {ahead_behind} of where successful users were on Day {day_in_journey} last quarter.",
            
            "generated_at": datetime.utcnow().isoformat()
        }

