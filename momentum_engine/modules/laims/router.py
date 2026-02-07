"""
L-AIMS Module - Low-Stakes Mock Tests & Leaderboards
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from momentum_engine.database import get_db
from momentum_engine.modules.laims.service import LAIMSService
from momentum_engine.modules.laims.schemas import MockTestSubmission

router = APIRouter()


@router.get("/laims/competitions")
async def list_competitions(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all L-AIMS competitions."""
    service = LAIMSService(db)
    return await service.list_competitions(status)


@router.get("/laims/competitions/{competition_id}")
async def get_competition(competition_id: str, db: AsyncSession = Depends(get_db)):
    """Get competition details."""
    service = LAIMSService(db)
    return await service.get_competition(competition_id)


@router.post("/laims/competitions/{competition_id}/submit")
async def submit_mock_test(
    competition_id: str,
    submission: MockTestSubmission,
    db: AsyncSession = Depends(get_db)
):
    """Submit mock test results."""
    service = LAIMSService(db)
    return await service.submit_mock_test(competition_id, submission)


@router.get("/laims/competitions/{competition_id}/leaderboard")
async def get_competition_leaderboard(
    competition_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get competition leaderboard."""
    service = LAIMSService(db)
    return await service.get_leaderboard(competition_id, limit)
