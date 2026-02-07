"""
Navigator Module - Track Assignment & Daily Planning
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timedelta

from momentum_engine.database import get_db
from momentum_engine.modules.navigator.schemas import (
    DiagnosticRequest,
    DiagnosticResponse,
    DashboardResponse,
    UserTasksResponse,
)
from momentum_engine.modules.navigator.service import NavigatorService

router = APIRouter()


@router.post("/onboarding/diagnostic", response_model=DiagnosticResponse)
async def complete_diagnostic(
    request: DiagnosticRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete diagnostic test and assign user to track.
    
    This is a Tier 1 (rule-based) operation - $0 AI cost.
    """
    service = NavigatorService(db)
    return await service.process_diagnostic(request)


@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
async def get_dashboard(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's daily dashboard with plan, streak, and progress.
    """
    service = NavigatorService(db)
    return await service.get_dashboard(user_id)


@router.get("/users/{user_id}/tasks", response_model=UserTasksResponse)
async def get_user_tasks(
    user_id: str,
    date_str: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's tasks for a specific date (default: today).
    """
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.now().date()
    
    service = NavigatorService(db)
    return await service.get_tasks_for_date(user_id, target_date)


@router.get("/tracks")
async def list_tracks(db: AsyncSession = Depends(get_db)):
    """
    List all available tracks with their specifications.
    """
    service = NavigatorService(db)
    return await service.list_tracks()


@router.get("/tracks/{track_name}")
async def get_track(track_name: str, db: AsyncSession = Depends(get_db)):
    """
    Get details for a specific track including success metrics.
    """
    service = NavigatorService(db)
    track = await service.get_track_by_name(track_name)
    if not track:
        raise HTTPException(404, f"Track '{track_name}' not found")
    return track


@router.get("/tracks/{track_name}/users/count")
async def get_track_user_count(track_name: str, db: AsyncSession = Depends(get_db)):
    """
    Get count of users currently on a track.
    """
    service = NavigatorService(db)
    count = await service.count_users_on_track(track_name)
    return {"track": track_name, "count": count}


class TaskCompletionRequest(BaseModel):
    """Request for completing a task with score."""
    task_id: str
    score: int  # 0-100
    module: str  # reading, writing, speaking, listening


@router.post("/tasks/complete/{user_id}")
async def complete_task_with_swap_check(
    user_id: str,
    request: TaskCompletionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete a task and check if a swap is needed.
    If score < 60%, the next day's task will be swapped for an intervention.
    """
    service = NavigatorService(db)
    swap_result = await service.check_performance_and_swap(
        user_id=user_id,
        completed_task_id=request.task_id,
        score=request.score,
        module=request.module
    )
    
    return {
        "completed": True,
        "task_id": request.task_id,
        "score": request.score,
        "swap": swap_result
    }


@router.get("/swaps/{user_id}")
async def get_swap_history(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the task swap history for a user.
    """
    service = NavigatorService(db)
    history = await service.get_user_swap_history(user_id)
    return {"user_id": user_id, "swaps": history}
