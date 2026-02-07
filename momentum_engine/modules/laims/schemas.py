"""L-AIMS module schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional, Dict
from pydantic import BaseModel, Field


class MockTestSubmission(BaseModel):
    """Mock test submission."""
    
    user_id: str
    reading_score: float = Field(..., ge=0, le=9)
    writing_score: float = Field(..., ge=0, le=9)
    speaking_score: float = Field(..., ge=0, le=9)
    listening_score: float = Field(..., ge=0, le=9)
    
    @property
    def overall_score(self) -> float:
        """Calculate overall band score."""
        avg = (self.reading_score + self.writing_score + 
               self.speaking_score + self.listening_score) / 4
        # Round to nearest 0.5
        return round(avg * 2) / 2


class CompetitionInfo(BaseModel):
    """Competition information."""
    
    id: str
    name: str
    type: str
    start_date: date
    end_date: date
    status: str
    participant_count: Optional[int] = None


class LeaderboardEntryResponse(BaseModel):
    """Leaderboard entry."""
    
    rank: int
    user_id: str
    score: float
    module_scores: Optional[Dict[str, float]] = None
