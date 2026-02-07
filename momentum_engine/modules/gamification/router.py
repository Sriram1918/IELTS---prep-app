"""
Gamification Module - Streaks, Leaderboards, Cohorts
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from momentum_engine.database import get_db
from momentum_engine.modules.gamification.service import GamificationService

router = APIRouter()


@router.get("/streaks/{user_id}")
async def get_streak(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's streak information."""
    service = GamificationService(db)
    return await service.get_streak(user_id)


@router.post("/streaks/{user_id}/update")
async def update_streak(user_id: str, db: AsyncSession = Depends(get_db)):
    """Update streak after task completion."""
    service = GamificationService(db)
    return await service.update_streak(user_id)


@router.get("/cohorts/{user_id}")
async def get_cohort_info(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's cohort information and ghost data."""
    service = GamificationService(db)
    return await service.get_cohort_info(user_id)


@router.get("/cohorts/{user_id}/ghost-data")
async def get_ghost_data(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get peer comparison ghost data for user."""
    service = GamificationService(db)
    return await service.get_ghost_data(user_id)


@router.get("/leaderboard")
async def get_leaderboard(
    competition_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get current leaderboard rankings."""
    service = GamificationService(db)
    return await service.get_leaderboard(competition_id, limit)


@router.get("/leaderboard/{user_id}/rank")
async def get_user_rank(
    user_id: str,
    competition_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get specific user's rank in leaderboard."""
    service = GamificationService(db)
    return await service.get_user_rank(user_id, competition_id)
