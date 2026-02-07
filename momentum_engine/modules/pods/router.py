"""
Pods Router - API endpoints for Challenge Pods
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from momentum_engine.database import get_db
from momentum_engine.modules.pods.service import PodsService

router = APIRouter()


class JoinPodRequest(BaseModel):
    user_id: str
    track_name: str


@router.post("/pods/join")
async def join_pod(request: JoinPodRequest, db: AsyncSession = Depends(get_db)):
    """Join a user to an appropriate pod for their track."""
    service = PodsService(db)
    result = await service.join_pod(request.user_id, request.track_name)
    return result


@router.get("/pods/user/{user_id}")
async def get_user_pod(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get the user's current pod with leaderboard."""
    service = PodsService(db)
    pod = await service.get_user_pod(user_id)
    if not pod:
        return {"message": "User is not in a pod", "has_pod": False}
    return {"has_pod": True, **pod}


@router.get("/pods/track/{track_name}")
async def list_track_pods(track_name: str, db: AsyncSession = Depends(get_db)):
    """List all active pods for a track."""
    service = PodsService(db)
    pods = await service.list_pods_for_track(track_name)
    return {"track": track_name, "pods": pods}


@router.post("/pods/update-points/{user_id}")
async def update_points(
    user_id: str, 
    points: int = 10, 
    tasks: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Update a user's pod points (called when completing tasks)."""
    service = PodsService(db)
    success = await service.update_member_points(user_id, points, tasks)
    if success:
        return {"success": True, "message": "Points updated"}
    return {"success": False, "message": "User not in a pod"}
