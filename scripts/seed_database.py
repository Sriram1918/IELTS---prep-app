
"""
Database Seeding Script
Generates realistic test data for Momentum Engine development.
"""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict
import argparse
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select, text
from momentum_engine.database.connection import async_session_maker
from momentum_engine.database.models import (
    User, Track, Task, UserProgress, Cohort, Competition, Streak, 
    UserMetric, CohortGhostData, GhostBenchmark
)
from momentum_engine.config import settings
print(f"DEBUG: POSTGRES_HOST env: {os.environ.get('POSTGRES_HOST')}")
print(f"DEBUG: settings.postgres_host: {settings.postgres_host}")
print(f"DEBUG: settings.async_database_url: {settings.async_database_url}")


# Configuration
DEFAULT_NUM_USERS = 100
DEFAULT_NUM_TASKS_PER_TRACK = 50

# Realistic distributions
DIAGNOSTIC_SCORE_DIST = [
    (5.0, 0.10), (5.5, 0.15), (6.0, 0.25), (6.5, 0.25),
    (7.0, 0.15), (7.5, 0.08), (8.0, 0.02)
]

DAYS_UNTIL_EXAM_DIST = [
    (14, 0.10), (30, 0.20), (45, 0.30),
    (60, 0.20), (90, 0.15), (120, 0.05)
]

TRACKS = [
    {"name": "sprint", "duration_weeks": 2, "daily_minutes": 50, "tasks_per_day": 3},
    {"name": "professional_marathon", "duration_weeks": 8, "daily_minutes": 25, "tasks_per_day": 2},
    {"name": "foundation", "duration_weeks": 12, "daily_minutes": 40, "tasks_per_day": 2},
    {"name": "intensive", "duration_weeks": 4, "daily_minutes": 100, "tasks_per_day": 5},
    {"name": "balanced", "duration_weeks": 6, "daily_minutes": 50, "tasks_per_day": 3},
    {"name": "weekend_warrior", "duration_weeks": 10, "daily_minutes": 15, "tasks_per_day": 1},
    {"name": "writing_focus", "duration_weeks": 6, "daily_minutes": 50, "tasks_per_day": 3},
    {"name": "speaking_focus", "duration_weeks": 6, "daily_minutes": 50, "tasks_per_day": 3},
    {"name": "academic_fast_track", "duration_weeks": 3, "daily_minutes": 65, "tasks_per_day": 4},
    {"name": "general_fast_track", "duration_weeks": 3, "daily_minutes": 65, "tasks_per_day": 4},
]

TASK_TYPES = ["reading", "writing", "speaking", "listening", "vocabulary", "grammar"]
DIFFICULTIES = ["easy", "medium", "hard"]


def sample_from_dist(distribution: List[tuple]) -> float:
    """Sample a value from a weighted distribution."""
    values = [v for v, _ in distribution]
    weights = [w for _, w in distribution]
    return random.choices(values, weights=weights)[0]


def assign_track(diagnostic_score: float, days_until_exam: int) -> str:
    """Rule-based track assignment."""
    if days_until_exam < 21 or diagnostic_score >= 6.5:
        return "sprint"
    elif diagnostic_score < 5.5 or days_until_exam > 90:
        return "foundation"
    else:
        return "professional_marathon"


def generate_users(n: int) -> List[Dict]:
    """Generate realistic user profiles."""
    users = []
    
    for i in range(n):
        diagnostic_score = sample_from_dist(DIAGNOSTIC_SCORE_DIST)
        days_until_exam = int(sample_from_dist(DAYS_UNTIL_EXAM_DIST))
        track = assign_track(diagnostic_score, days_until_exam)
        
        # Simulate varying activity levels
        days_active = random.randint(1, min(30, days_until_exam))
        tasks_completed = random.randint(0, days_active * 3)
        practice_minutes = tasks_completed * random.randint(8, 15)
        current_streak = random.randint(0, min(14, days_active))
        
        users.append({
            "id": str(uuid4()),
            "name": f"User_{i+1}",
            "email": f"user{i+1}@test.com",
            "diagnostic_score": diagnostic_score,
            "current_track": track,
            "days_until_exam": days_until_exam,
            "exam_date": (datetime.now() + timedelta(days=days_until_exam)).date(),
            "tasks_completed": tasks_completed,
            "total_practice_time": practice_minutes,
            "current_streak": current_streak,
            "longest_streak": max(current_streak, random.randint(0, 14)),
            "predicted_band": min(9.0, diagnostic_score + random.uniform(-0.3, 0.8)),
            "created_at": datetime.now() - timedelta(days=days_active),
            "last_activity_date": (datetime.now() - timedelta(hours=random.randint(0, 72))).date()
        })
    
    return users


def generate_tracks() -> List[Dict]:
    """Generate track definitions."""
    return [
        {
            "id": str(uuid4()),
            "name": t["name"],
            "duration_weeks": t["duration_weeks"],
            "daily_minutes": t["daily_minutes"],
            "tasks_per_day": t["tasks_per_day"],
            "focus": f"Focus area for {t['name']} track",
            "description": f"Description for {t['name']} track"
        }
        for t in TRACKS
    ]


def generate_tasks(tracks: List[Dict], tasks_per_track: int = 50) -> List[Dict]:
    """Generate task library for each track."""
    tasks = []
    
    for track in tracks:
        for i in range(tasks_per_track):
            task_type = random.choice(TASK_TYPES)
            difficulty = random.choice(DIFFICULTIES)
            
            tasks.append({
                "id": str(uuid4()),
                "track_id": track["id"],
                "type": task_type,
                "difficulty": difficulty,
                "estimated_minutes": random.randint(5, 25),
                "order_in_track": i,
                "content_url": f"https://content.example.com/{task_type}/{i}",
                "title": f"{task_type.title()} Practice {i+1}",
                "description": f"{difficulty.title()} {task_type} exercise"
            })
    
    return tasks


def generate_user_progress(users: List[Dict], tasks: List[Dict]) -> List[Dict]:
    """Generate task completion history for users."""
    progress = []
    
    # Map track names to task lists for faster lookup
    track_tasks = {}
    for task in tasks:
        # We need to look up track name from ID, but for now let's just use track_id
        if task["track_id"] not in track_tasks:
            track_tasks[task["track_id"]] = []
        track_tasks[task["track_id"]].append(task)
            
    # Need to map user track name to track ID
    # Since we don't have that map easily, we'll build it.
    # Actually, simpler: just grab random tasks for progress simulation
    # but strictly we should filter by track.
    # Let's skip strict track matching for seed simplicity and just pick random tasks.
    
    for user in users:
        if user["tasks_completed"] == 0:
            continue
            
        completed_count = min(user["tasks_completed"], len(tasks))
        # Pick random tasks
        completed_tasks = random.sample(tasks, completed_count)
        
        for task in completed_tasks:
            progress.append({
                "id": str(uuid4()),
                "user_id": user["id"],
                "task_id": task["id"],
                "completed_at": user["created_at"] + timedelta(
                    days=random.randint(0, max(1, (datetime.now() - user["created_at"]).days))
                ),
                "accuracy_score": random.randint(40, 100),
                "time_spent_minutes": task["estimated_minutes"] + random.randint(-5, 10)
            })
    
    return progress


def generate_cohorts(users: List[Dict]) -> tuple:
    """Generate cohorts and assign users."""
    cohorts = {}
    
    for user in users:
        skill_tier = round(user["diagnostic_score"] * 2) / 2
        velocity = "medium"  # Simplified for seeding
        track = user["current_track"]
        
        key = f"skill_{skill_tier}_velocity_{velocity}_track_{track}"
        
        if key not in cohorts:
            cohorts[key] = {
                "id": str(uuid4()),
                "cohort_key": key,
                "skill_tier": skill_tier,
                "velocity_tier": velocity,
                "track": track, # This is just a string in generated user, not valid for model if model expects relation? 
                                # Cohort model doesn't link to Track model, usually.
                "member_count": 0,
                "members": []
            }
        
        cohorts[key]["member_count"] += 1
        cohorts[key]["members"].append(user["id"])
    
    return list(cohorts.values())


def generate_competitions() -> List[Dict]:
    """Generate L-AIMS competitions."""
    return [
        {
            "id": str(uuid4()),
            "type": "L-AIMS",
            "name": "February 2026 Mock Test",
            "start_date": datetime.now().date(),
            "end_date": (datetime.now() + timedelta(days=14)).date(),
            "status": "active"
        },
        {
            "id": str(uuid4()),
            "type": "L-AIMS",
            "name": "March 2026 Mock Test",
            "start_date": (datetime.now() + timedelta(days=30)).date(),
            "end_date": (datetime.now() + timedelta(days=44)).date(),
            "status": "upcoming"
        }
    ]


async def seed_database(num_users: int = DEFAULT_NUM_USERS, reset: bool = False):
    """Main seeding function."""
    print(f"🌱 Generating seed data for {num_users} users...")
    
    tracks_data = generate_tracks()
    users_data = generate_users(num_users)
    tasks_data = generate_tasks(tracks_data, DEFAULT_NUM_TASKS_PER_TRACK)
    progress_data = generate_user_progress(users_data, tasks_data)
    cohorts_data = generate_cohorts(users_data)
    competitions_data = generate_competitions()
    
    print(f"  📊 Generated:")
    print(f"     - {len(tracks_data)} tracks")
    print(f"     - {len(users_data)} users")
    print(f"     - {len(tasks_data)} tasks")
    print(f"     - {len(progress_data)} progress records")
    print(f"     - {len(cohorts_data)} cohorts")
    
    async with async_session_maker() as session:
        if reset:
            print("  ⚠️ Resetting database (truncating tables)...")
            # Order matters for foreign keys
            await session.execute(text("TRUNCATE TABLE user_progress CASCADE"))
            await session.execute(text("TRUNCATE TABLE tasks CASCADE"))
            await session.execute(text("TRUNCATE TABLE streaks CASCADE"))
            await session.execute(text("TRUNCATE TABLE users CASCADE"))
            await session.execute(text("TRUNCATE TABLE cohorts CASCADE"))
            await session.execute(text("TRUNCATE TABLE tracks CASCADE"))
            await session.execute(text("TRUNCATE TABLE competitions CASCADE"))
            await session.commit()
    
        print("  💾 Inserting data into database...")
        
        # 1. Tracks
        print("     ... inserting tracks")
        for t in tracks_data:
            track = Track(
                id=t["id"], name=t["name"], duration_weeks=t["duration_weeks"],
                daily_minutes=t["daily_minutes"], tasks_per_day=t["tasks_per_day"],
                focus=t["focus"], description=t["description"]
            )
            session.add(track)
        await session.flush()
        
        # 2. Cohorts
        print("     ... inserting cohorts")
        cohort_map = {} # Key -> ID
        for c in cohorts_data:
            skill_tier_val = round(float(c["skill_tier"]), 1)
            if skill_tier_val >= 10.0:
                skill_tier_val = 9.9
                
            try:
                cohort = Cohort(
                    id=c["id"], cohort_key=c["cohort_key"], skill_tier=skill_tier_val,
                    velocity_tier=c["velocity_tier"], member_count=c["member_count"],
                    active_member_count=int(c["member_count"] * 0.8)
                )
                session.add(cohort)
            except Exception as e:
                print(f"ERROR inserting cohort: {c}")
                raise e
            cohort_map[c["id"]] = c
        await session.flush()
        
        # 3. Users & Streaks
        print("     ... inserting users")
        user_to_cohort = {}
        for c in cohorts_data:
            for uid in c["members"]:
                user_to_cohort[uid] = c["id"]
        
        for u in users_data:
            cohort_id = user_to_cohort.get(u["id"])
            user = User(
                id=u["id"], name=u["name"], email=u["email"],
                diagnostic_score=u["diagnostic_score"], current_track=u["current_track"],
                exam_date=u["exam_date"], tasks_completed=u["tasks_completed"],
                total_practice_time=u["total_practice_time"],
                cohort_id=cohort_id
            )
            session.add(user)
            
            # Create streak
            streak = Streak(
                user_id=u["id"], current_streak=u["current_streak"],
                longest_streak=u["longest_streak"], last_activity_date=u["last_activity_date"]
            )
            session.add(streak)
        await session.flush()
        
        # 4. Tasks
        print("     ... inserting tasks")
        for t in tasks_data:
            task = Task(
                id=t["id"], track_id=t["track_id"], type=t["type"],
                difficulty=t["difficulty"], estimated_minutes=t["estimated_minutes"],
                order_in_track=t["order_in_track"], content_url=t["content_url"],
                title=t["title"], description=t["description"]
            )
            session.add(task)
        await session.flush()
        
        # 5. User Progress
        print("     ... inserting progress (this might take a moment)")
        # Batch insert progress
        progress_buffer = []
        for p in progress_data:
            progress_buffer.append(UserProgress(
                id=p["id"], user_id=p["user_id"], task_id=p["task_id"],
                completed_at=p["completed_at"], accuracy_score=p["accuracy_score"],
                time_spent_minutes=p["time_spent_minutes"]
            ))
            if len(progress_buffer) >= 1000:
                session.add_all(progress_buffer)
                progress_buffer = []
        
        if progress_buffer:
            session.add_all(progress_buffer)
            
        # 6. Competitions
        print("     ... inserting competitions")
        for c in competitions_data:
            comp = Competition(
                id=c["id"], type=c["type"], name=c["name"],
                start_date=c["start_date"], end_date=c["end_date"],
                status=c["status"]
            )
            session.add(comp)

        await session.commit()
        print("✅ Database populated successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Momentum Engine database")
    parser.add_argument("--users", type=int, default=DEFAULT_NUM_USERS, help="Number of users")
    parser.add_argument("--reset", action="store_true", help="Reset database first")
    args = parser.parse_args()
    
    asyncio.run(seed_database(args.users, args.reset))
