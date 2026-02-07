"""
L-AIMS Service - Low-Stakes Mock Test Management
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from momentum_engine.database.models import Competition, LeaderboardEntry
from momentum_engine.modules.laims.schemas import MockTestSubmission
from momentum_engine.shared.exceptions import NotFoundError

logger = structlog.get_logger()


class LAIMSService:
    """Service for L-AIMS mock tests."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_competitions(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List all competitions."""
        
        query = select(Competition).order_by(Competition.start_date.desc())
        
        if status:
            query = query.where(Competition.status == status)
        
        result = await self.db.execute(query)
        competitions = result.scalars().all()
        
        return {
            "competitions": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.type,
                    "start_date": str(c.start_date),
                    "end_date": str(c.end_date),
                    "status": c.status
                }
                for c in competitions
            ]
        }
    
    async def get_competition(self, competition_id: str) -> Dict[str, Any]:
        """Get competition details."""
        
        result = await self.db.execute(
            select(Competition).where(Competition.id == competition_id)
        )
        competition = result.scalar_one_or_none()
        
        if not competition:
            raise NotFoundError("Competition", competition_id)
        
        # Count participants
        count_result = await self.db.execute(
            select(func.count(LeaderboardEntry.id))
            .where(LeaderboardEntry.competition_id == competition_id)
        )
        participant_count = count_result.scalar() or 0
        
        return {
            "id": competition.id,
            "name": competition.name,
            "type": competition.type,
            "start_date": str(competition.start_date),
            "end_date": str(competition.end_date),
            "status": competition.status,
            "participant_count": participant_count
        }
    
    async def submit_mock_test(
        self, 
        competition_id: str, 
        submission: MockTestSubmission
    ) -> Dict[str, Any]:
        """Submit mock test results."""
        
        # Verify competition exists and is active
        comp_result = await self.db.execute(
            select(Competition).where(Competition.id == competition_id)
        )
        competition = comp_result.scalar_one_or_none()
        
        if not competition:
            raise NotFoundError("Competition", competition_id)
        
        if competition.status != "active":
            return {"error": "Competition is not active", "status": competition.status}
        
        # Check if user already submitted
        existing = await self.db.execute(
            select(LeaderboardEntry).where(
                LeaderboardEntry.competition_id == competition_id,
                LeaderboardEntry.user_id == submission.user_id
            )
        )
        entry = existing.scalar_one_or_none()
        
        overall_score = submission.overall_score
        module_scores = {
            "reading": submission.reading_score,
            "writing": submission.writing_score,
            "speaking": submission.speaking_score,
            "listening": submission.listening_score
        }
        
        if entry:
            # Update existing entry
            entry.score = Decimal(str(overall_score))
            entry.module_scores = module_scores
            entry.submitted_at = datetime.utcnow()
        else:
            # Create new entry
            entry = LeaderboardEntry(
                competition_id=competition_id,
                user_id=submission.user_id,
                score=Decimal(str(overall_score)),
                module_scores=module_scores
            )
            self.db.add(entry)
        
        await self.db.flush()
        
        # Update ranks
        await self._update_ranks(competition_id)
        
        logger.info(
            "Mock test submitted",
            competition_id=competition_id,
            user_id=submission.user_id,
            score=overall_score
        )
        
        return {
            "submitted": True,
            "overall_score": overall_score,
            "module_scores": module_scores,
            "message": f"Test submitted! Your score: {overall_score}"
        }
    
    async def _update_ranks(self, competition_id: str):
        """Update ranks for all entries in a competition."""
        
        # Get all entries sorted by score
        result = await self.db.execute(
            select(LeaderboardEntry)
            .where(LeaderboardEntry.competition_id == competition_id)
            .order_by(LeaderboardEntry.score.desc())
        )
        entries = result.scalars().all()
        
        for i, entry in enumerate(entries, 1):
            entry.rank = i
    
    async def get_leaderboard(
        self, 
        competition_id: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get competition leaderboard."""
        
        result = await self.db.execute(
            select(LeaderboardEntry)
            .where(LeaderboardEntry.competition_id == competition_id)
            .order_by(LeaderboardEntry.rank)
            .limit(limit)
        )
        entries = result.scalars().all()
        
        return {
            "competition_id": competition_id,
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
