"""
Celery Application Configuration
"""

from celery import Celery
from celery.schedules import crontab

from momentum_engine.config import settings

# Create Celery app
celery_app = Celery(
    "momentum_engine",
    broker=settings.redis_connection_url,
    backend=settings.redis_connection_url,
    include=[
        "momentum_engine.workers.tasks.streak_tasks",
        "momentum_engine.workers.tasks.cohort_tasks",
        "momentum_engine.workers.tasks.ai_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Update streaks at midnight UTC
    "update-streaks-daily": {
        "task": "momentum_engine.workers.tasks.streak_tasks.update_all_streaks",
        "schedule": crontab(hour=0, minute=5),
    },
    # Update cohort ghost data hourly
    "update-cohort-ghost-data": {
        "task": "momentum_engine.workers.tasks.cohort_tasks.update_cohort_ghost_data",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Calculate daily metrics
    "calculate-daily-metrics": {
        "task": "momentum_engine.workers.tasks.cohort_tasks.calculate_daily_metrics",
        "schedule": crontab(hour=1, minute=0),  # 1 AM UTC
    },
    # Recalculate cohorts weekly
    "recalculate-cohorts": {
        "task": "momentum_engine.workers.tasks.cohort_tasks.recalculate_cohorts",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
    },
}
