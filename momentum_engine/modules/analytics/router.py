"""
Analytics Module - Metrics & Progress Tracking
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from momentum_engine.database import get_db
from momentum_engine.modules.analytics.service import AnalyticsService

router = APIRouter()


@router.get("/analytics/{user_id}/metrics")
async def get_user_metrics(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's key metrics (LVS, MACR)."""
    service = AnalyticsService(db)
    return await service.get_user_metrics(user_id)


@router.get("/analytics/{user_id}/progress")
async def get_progress_report(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed progress report."""
    service = AnalyticsService(db)
    return await service.get_progress_report(user_id)


@router.get("/analytics/{user_id}/module-breakdown")
async def get_module_breakdown(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get performance breakdown by IELTS module."""
    service = AnalyticsService(db)
    return await service.get_module_breakdown(user_id)


@router.get("/analytics/{user_id}/weekly-report")
async def get_weekly_cohort_report(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the weekly cohort report - the "Aha Moment" notification.
    
    This report delivers 3 psychological anchors:
    1. Concrete Progress: Practice time quantified
    2. Social Calibration: Ghost data benchmarks  
    3. Adaptive Intelligence: Personalized next steps
    """
    service = AnalyticsService(db)
    return await service.get_weekly_cohort_report(user_id)
