"""
Pods Service - Challenge Pods for Peer Accountability
Auto-groups users by track + start week.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from momentum_engine.database.models import User, Pod, PodMember

logger = structlog.get_logger()


class PodsService:
    """Service for managing Challenge Pods."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_pod(self, track_name: str, user_id: str) -> Pod:
        """Get existing pod with space or create a new one."""
        current_week = datetime.now().isocalendar()[1]
        
        # Find an active pod for this track/week with space
        result = await self.db.execute(
            select(Pod)
            .where(
                Pod.track_name == track_name,
                Pod.start_week == current_week,
                Pod.is_active == True
            )
        )
        pods = result.scalars().all()
        
        # Check each pod for available space
        for pod in pods:
            member_count_result = await self.db.execute(
                select(func.count(PodMember.id)).where(PodMember.pod_id == pod.id)
            )
            member_count = member_count_result.scalar() or 0
            
            if member_count < pod.max_members:
                return pod
        
        # Create a new pod
        pod_number = len(pods) + 1
        new_pod = Pod(
            name=f"{track_name.replace('_', ' ').title()} Pod #{pod_number} - Week {current_week}",
            track_name=track_name,
            start_week=current_week,
            max_members=10
        )
        self.db.add(new_pod)
        await self.db.flush()
        
        logger.info("Created new pod", pod_id=new_pod.id, track=track_name, week=current_week)
        return new_pod
    
    async def join_pod(self, user_id: str, track_name: str) -> dict:
        """Join a user to an appropriate pod."""
        # Check if already in a pod for this track
        existing = await self.db.execute(
            select(PodMember)
            .join(Pod)
            .where(
                PodMember.user_id == user_id,
                Pod.track_name == track_name,
                Pod.is_active == True
            )
        )
        existing_membership = existing.scalar_one_or_none()
        
        if existing_membership:
            return {"already_member": True, "pod_id": existing_membership.pod_id}
        
        # Get or create pod
        pod = await self.get_or_create_pod(track_name, user_id)
        
        # Add user to pod
        member = PodMember(
            pod_id=pod.id,
            user_id=user_id,
            rank=0,
            points=0
        )
        self.db.add(member)
        await self.db.commit()
        
        return {
            "joined": True,
            "pod_id": str(pod.id),
            "pod_name": pod.name
        }
    
    async def get_user_pod(self, user_id: str) -> Optional[dict]:
        """Get the user's current pod with members and rankings."""
        result = await self.db.execute(
            select(PodMember, Pod)
            .join(Pod)
            .where(
                PodMember.user_id == user_id,
                Pod.is_active == True
            )
        )
        row = result.first()
        
        if not row:
            return None
        
        membership, pod = row
        
        # Get all members with their rankings
        members_result = await self.db.execute(
            select(PodMember, User)
            .join(User, PodMember.user_id == User.id)
            .where(PodMember.pod_id == pod.id)
            .order_by(PodMember.points.desc())
        )
        members_data = members_result.all()
        
        members = []
        user_rank = 0
        for i, (member, user) in enumerate(members_data):
            rank = i + 1
            if member.user_id == user_id:
                user_rank = rank
            members.append({
                "user_id": str(member.user_id),
                "name": user.name,
                "rank": rank,
                "points": member.points,
                "tasks_completed": member.tasks_completed,
                "streak_days": member.streak_days,
                "is_current_user": member.user_id == user_id
            })
        
        return {
            "pod_id": str(pod.id),
            "pod_name": pod.name,
            "track": pod.track_name,
            "member_count": len(members),
            "max_members": pod.max_members,
            "user_rank": user_rank,
            "members": members
        }
    
    async def update_member_points(self, user_id: str, points_delta: int = 10, tasks_delta: int = 1):
        """Update a member's points when they complete a task."""
        result = await self.db.execute(
            select(PodMember)
            .join(Pod)
            .where(
                PodMember.user_id == user_id,
                Pod.is_active == True
            )
        )
        membership = result.scalar_one_or_none()
        
        if membership:
            membership.points += points_delta
            membership.tasks_completed += tasks_delta
            await self.db.commit()
            return True
        return False
    
    async def list_pods_for_track(self, track_name: str) -> List[dict]:
        """List all active pods for a track."""
        result = await self.db.execute(
            select(Pod)
            .where(Pod.track_name == track_name, Pod.is_active == True)
            .order_by(Pod.created_at.desc())
        )
        pods = result.scalars().all()
        
        pod_list = []
        for pod in pods:
            member_count_result = await self.db.execute(
                select(func.count(PodMember.id)).where(PodMember.pod_id == pod.id)
            )
            member_count = member_count_result.scalar() or 0
            
            pod_list.append({
                "id": str(pod.id),
                "name": pod.name,
                "track": pod.track_name,
                "week": pod.start_week,
                "member_count": member_count,
                "max_members": pod.max_members,
                "is_full": member_count >= pod.max_members
            })
        
        return pod_list
