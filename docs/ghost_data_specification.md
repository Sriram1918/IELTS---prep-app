# Ghost Data Specification

Complete specification for anonymized peer comparison benchmarks shown to users.

---

## Overview

"Ghost data" refers to **anonymized peer comparison benchmarks** that create social pressure and urgency without revealing user identities. Ghost data powers the "social proof" features that drive engagement.

---

## Ghost Message Examples

```
"Users who scored 7.5+ completed 15 speaking exercises by Day 12. You're at 8."
"Top 10% of users in your cohort practice 6 days/week. You're at 4 days."
"Users at your skill level who improved fastest spent 25 min/day. You're at 18 min."
"Your cohort averaged 12 tasks this week. You're at 8. Catch up?"
"85% of 7.0+ achievers maintained a 5+ day streak. You're on day 3! 🔥"
```

---

## Data Categories

### 1. Success Benchmarks (Historical Data)

Pre-calculated from past users who achieved target bands. **Static data**, updated monthly.

```python
GHOST_BENCHMARKS = {
    "band_7.0_achievers": {
        "starting_skill_5.5": {
            "day_7": {
                "tasks_completed": 14,
                "practice_minutes": 180,
                "speaking_tasks": 4,
                "writing_tasks": 3,
                "reading_tasks": 4,
                "listening_tasks": 3,
                "mock_tests": 0,
                "streak_avg": 5
            },
            "day_14": {
                "tasks_completed": 28,
                "practice_minutes": 360,
                "speaking_tasks": 8,
                "writing_tasks": 7,
                "reading_tasks": 7,
                "listening_tasks": 6,
                "mock_tests": 1,
                "streak_avg": 10
            },
            "day_28": {
                "tasks_completed": 55,
                "practice_minutes": 720,
                "mock_tests": 3
            }
        },
        "starting_skill_6.0": {
            # Similar structure...
        }
    },
    "band_7.5_achievers": {
        # Similar structure...
    },
    "band_8.0_achievers": {
        # Similar structure...
    }
}
```

### 2. Cohort Averages (Real-Time Data)

Calculated from current cohort members. **Dynamic data**, updated hourly.

```python
async def calculate_cohort_averages(cohort_id: str) -> dict:
    """
    Calculate real-time cohort statistics for ghost comparisons.
    """
    members = await get_active_cohort_members(cohort_id)
    
    if not members:
        return None
    
    return {
        "member_count": len(members),
        "avg_tasks_completed": mean([m.tasks_completed for m in members]),
        "avg_tasks_this_week": mean([m.tasks_this_week for m in members]),
        "avg_practice_minutes": mean([m.total_practice_time for m in members]),
        "avg_streak": mean([m.current_streak for m in members]),
        "median_streak": median([m.current_streak for m in members]),
        "top_10_percent_tasks": percentile([m.tasks_completed for m in members], 90),
        "top_25_percent_tasks": percentile([m.tasks_completed for m in members], 75),
        "avg_days_practiced_per_week": mean([count_practice_days(m, 7) for m in members])
    }
```

### 3. Percentile Rankings

User's position relative to their cohort or all users.

```python
async def calculate_user_percentile(user_id: str, metric: str) -> int:
    """
    Calculate user's percentile for a specific metric.
    """
    user = await get_user(user_id)
    cohort_members = await get_cohort_members(user.cohort_id)
    
    if metric == "tasks_completed":
        values = sorted([m.tasks_completed for m in cohort_members])
        user_value = user.tasks_completed
    elif metric == "streak":
        values = sorted([m.current_streak for m in cohort_members])
        user_value = user.current_streak
    elif metric == "practice_time":
        values = sorted([m.total_practice_time for m in cohort_members])
        user_value = user.total_practice_time
    
    # Calculate percentile
    count_below = sum(1 for v in values if v < user_value)
    percentile = int((count_below / len(values)) * 100)
    
    return percentile
```

---

## Database Schema

```sql
-- Historical benchmarks (pre-computed from successful users)
CREATE TABLE ghost_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_band DECIMAL(2,1) NOT NULL,      -- Goal band (7.0, 7.5, 8.0)
    starting_skill DECIMAL(2,1) NOT NULL,   -- User's starting level
    day_number INT NOT NULL,                -- Day in prep journey
    
    -- Aggregated metrics
    avg_tasks_completed INT,
    avg_practice_minutes INT,
    avg_speaking_tasks INT,
    avg_writing_tasks INT,
    avg_reading_tasks INT,
    avg_listening_tasks INT,
    avg_mock_tests INT,
    avg_streak INT,
    
    -- Percentile info
    success_percentile INT,                 -- Top 10%, 25%, 50%
    sample_size INT,                        -- How many users this was based on
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(target_band, starting_skill, day_number, success_percentile)
);

-- Real-time cohort stats (updated hourly by Cohort Worker)
CREATE TABLE cohort_ghost_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID REFERENCES cohorts(id),
    snapshot_date DATE NOT NULL,
    snapshot_hour INT DEFAULT 0,            -- For hourly snapshots
    
    -- Aggregate metrics
    active_member_count INT,
    avg_tasks_completed DECIMAL(5,2),
    avg_tasks_this_week DECIMAL(5,2),
    avg_practice_minutes DECIMAL(7,2),
    avg_streak DECIMAL(4,2),
    median_streak INT,
    top_10_percent_tasks INT,
    top_25_percent_tasks INT,
    avg_days_practiced_per_week DECIMAL(3,2),
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(cohort_id, snapshot_date)
);

-- Indexes
CREATE INDEX idx_ghost_benchmarks_lookup 
    ON ghost_benchmarks(target_band, starting_skill, day_number);
CREATE INDEX idx_cohort_ghost_date 
    ON cohort_ghost_data(cohort_id, snapshot_date DESC);
```

---

## Generation Logic

### Seeding Historical Benchmarks

```python
async def seed_ghost_benchmarks():
    """
    One-time seed of ghost_benchmarks table from historical data.
    
    Should be run during initial setup and refreshed monthly.
    """
    target_bands = [7.0, 7.5, 8.0]
    starting_skills = [5.0, 5.5, 6.0, 6.5]
    days_to_track = list(range(1, 91))  # Days 1-90
    percentiles = [10, 25, 50]  # Top 10%, top 25%, median
    
    for target_band in target_bands:
        # Get users who achieved this band
        successful_users = await db.fetch("""
            SELECT * FROM users 
            WHERE final_band_score >= %s 
            AND final_band_score < %s + 0.5
            AND diagnostic_score IS NOT NULL
        """, target_band, target_band)
        
        for starting_skill in starting_skills:
            # Filter to users who started at this level
            cohort = [u for u in successful_users 
                     if starting_skill <= u.diagnostic_score < starting_skill + 0.5]
            
            if len(cohort) < 50:  # Need minimum sample size
                continue
            
            for day in days_to_track:
                for percentile in percentiles:
                    # Calculate aggregates for this day in their journey
                    stats = calculate_day_aggregates(cohort, day, percentile)
                    
                    await db.execute("""
                        INSERT INTO ghost_benchmarks 
                        (target_band, starting_skill, day_number, success_percentile,
                         avg_tasks_completed, avg_practice_minutes, 
                         avg_speaking_tasks, avg_writing_tasks, sample_size)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (target_band, starting_skill, day_number, success_percentile)
                        DO UPDATE SET 
                            avg_tasks_completed = EXCLUDED.avg_tasks_completed,
                            updated_at = NOW()
                    """, target_band, starting_skill, day, percentile, 
                        stats["tasks"], stats["minutes"], 
                        stats["speaking"], stats["writing"], len(cohort))
    
    logger.info("Ghost benchmarks seeded successfully")
```

### Cohort Ghost Data (Hourly Update)

```python
async def update_cohort_ghost_data():
    """
    Cohort Worker runs this hourly.
    Updates cohort_ghost_data table with current aggregates.
    """
    cohorts = await db.fetch("SELECT id FROM cohorts WHERE member_count > 0")
    
    for cohort in cohorts:
        members = await db.fetch("""
            SELECT 
                tasks_completed,
                total_practice_time,
                current_streak,
                last_activity_date
            FROM users
            WHERE cohort_id = %s
            AND cohort_excluded = FALSE
            AND last_activity_date >= NOW() - INTERVAL '14 days'
        """, cohort.id)
        
        if not members:
            continue
        
        # Calculate weekly tasks
        weekly_tasks = []
        for m in members:
            tasks_7d = await db.fetchval("""
                SELECT COUNT(*) FROM user_progress
                WHERE user_id = %s 
                AND completed_at >= NOW() - INTERVAL '7 days'
            """, m.id)
            weekly_tasks.append(tasks_7d)
        
        stats = {
            "cohort_id": cohort.id,
            "snapshot_date": date.today(),
            "active_member_count": len(members),
            "avg_tasks_completed": mean([m.tasks_completed for m in members]),
            "avg_tasks_this_week": mean(weekly_tasks),
            "avg_practice_minutes": mean([m.total_practice_time for m in members]),
            "avg_streak": mean([m.current_streak for m in members]),
            "median_streak": median([m.current_streak for m in members]),
            "top_10_percent_tasks": percentile([m.tasks_completed for m in members], 90),
            "top_25_percent_tasks": percentile([m.tasks_completed for m in members], 75)
        }
        
        await db.execute("""
            INSERT INTO cohort_ghost_data (cohort_id, snapshot_date, ...)
            VALUES (%(cohort_id)s, %(snapshot_date)s, ...)
            ON CONFLICT (cohort_id, snapshot_date)
            DO UPDATE SET 
                avg_tasks_completed = %(avg_tasks_completed)s,
                updated_at = NOW()
        """, stats)
    
    logger.info(f"Updated ghost data for {len(cohorts)} cohorts")
```

---

## Display Rules

### When to Show Ghost Data

| Context | Show Ghost? | Type | Priority |
|---------|-------------|------|----------|
| Daily Dashboard | Always | 1 comparison | High |
| Task Completion | If behind | Motivational | Medium |
| Weekly Report | Always | 3 comparisons | High |
| Streak at risk | Always | Streak comparison | Critical |
| After inactivity | Always | Catch-up message | High |

### Message Template System

```python
GHOST_MESSAGE_TEMPLATES = {
    "success_benchmark": {
        "ahead": {
            "template": "Great progress! Users who scored {target_band}+ had completed {benchmark_value} {metric} by Day {day}. You're at {user_value}! 🎯",
            "tone": "celebration"
        },
        "close": {
            "template": "You're almost there! {target_band}+ achievers had {benchmark_value} {metric} by Day {day}. You're at {user_value}.",
            "tone": "encouraging"
        },
        "behind": {
            "template": "Users who scored {target_band}+ had completed {benchmark_value} {metric} by Day {day}. You're at {user_value}.",
            "tone": "neutral"
        }
    },
    "cohort_comparison": {
        "ahead": {
            "template": "You're ahead of your cohort! Average is {cohort_avg} {metric}, you're at {user_value}. 💪",
            "tone": "celebration"  
        },
        "close": {
            "template": "You're right with your cohort! Average is {cohort_avg} {metric}, you're at {user_value}.",
            "tone": "encouraging"
        },
        "behind": {
            "template": "Your cohort is averaging {cohort_avg} {metric}. You're at {user_value}. Catch up?",
            "tone": "motivating"
        }
    },
    "streak_comparison": {
        "template": "{percentage}% of {target_band}+ achievers maintained a {streak_threshold}+ day streak. You're on day {user_streak}! 🔥",
        "tone": "motivating"
    },
    "top_performers": {
        "template": "Top 10% of your cohort completed {top_10_value} {metric}. You're at {user_value}.",
        "tone": "challenging"
    }
}


def format_ghost_message(
    message_type: str, 
    user: User, 
    comparison_data: dict,
    metric: str = "tasks"
) -> str:
    """
    Generate formatted ghost message for user.
    """
    templates = GHOST_MESSAGE_TEMPLATES[message_type]
    
    # Determine user's relative position
    if message_type in ["success_benchmark", "cohort_comparison"]:
        user_value = get_user_metric(user, metric)
        benchmark_value = comparison_data.get(f"avg_{metric}") or comparison_data.get("benchmark_value")
        
        ratio = user_value / benchmark_value if benchmark_value else 0
        
        if ratio >= 1.1:
            position = "ahead"
        elif ratio >= 0.9:
            position = "close"
        else:
            position = "behind"
        
        template = templates[position]["template"]
        
    else:
        template = templates["template"]
    
    # Format template
    return template.format(
        target_band=comparison_data.get("target_band", "7.0"),
        benchmark_value=comparison_data.get("benchmark_value"),
        metric=METRIC_LABELS.get(metric, metric),
        day=user.day_in_journey,
        user_value=get_user_metric(user, metric),
        cohort_avg=comparison_data.get("avg_value"),
        percentage=comparison_data.get("percentage"),
        streak_threshold=comparison_data.get("streak_threshold"),
        user_streak=user.current_streak,
        top_10_value=comparison_data.get("top_10_value")
    )


METRIC_LABELS = {
    "tasks_completed": "tasks",
    "practice_minutes": "minutes of practice",
    "speaking_tasks": "speaking exercises",
    "writing_tasks": "writing tasks",
    "current_streak": "day streak"
}
```

---

## API Response Format

```python
@router.get("/cohort/{user_id}/ghost-data")
async def get_ghost_data(user_id: str):
    """
    Get peer comparison data for user.
    """
    user = await get_user(user_id)
    day_number = (date.today() - user.created_at.date()).days + 1
    starting_skill = round(user.diagnostic_score * 2) / 2
    
    # Get success benchmark
    benchmark = await db.fetchrow("""
        SELECT * FROM ghost_benchmarks
        WHERE target_band = 7.5
        AND starting_skill = %s
        AND day_number = %s
        AND success_percentile = 25
    """, starting_skill, min(day_number, 90))
    
    # Get cohort data
    cohort_data = await db.fetchrow("""
        SELECT * FROM cohort_ghost_data
        WHERE cohort_id = %s
        AND snapshot_date = CURRENT_DATE
    """, user.cohort_id)
    
    # Calculate user's percentile in cohort
    percentile = await calculate_user_percentile(user_id, "tasks_completed")
    
    return {
        "user_stats": {
            "tasks_completed": user.tasks_completed,
            "tasks_this_week": await get_weekly_tasks(user_id),
            "practice_minutes": user.total_practice_time,
            "current_streak": user.current_streak,
            "day_in_journey": day_number
        },
        "success_benchmark": {
            "target_band": 7.5,
            "day_number": day_number,
            "benchmark_tasks": benchmark.avg_tasks_completed if benchmark else None,
            "benchmark_practice_minutes": benchmark.avg_practice_minutes if benchmark else None,
            "message": format_ghost_message("success_benchmark", user, {
                "target_band": 7.5,
                "benchmark_value": benchmark.avg_tasks_completed if benchmark else 0,
                "day": day_number
            }, "tasks_completed") if benchmark else None
        },
        "cohort_comparison": {
            "cohort_size": cohort_data.active_member_count if cohort_data else 0,
            "avg_tasks_completed": cohort_data.avg_tasks_completed if cohort_data else None,
            "avg_tasks_this_week": cohort_data.avg_tasks_this_week if cohort_data else None,
            "user_percentile": percentile,
            "message": format_ghost_message("cohort_comparison", user, {
                "avg_value": cohort_data.avg_tasks_completed if cohort_data else 0
            }, "tasks_completed") if cohort_data else None
        },
        "top_performers": {
            "top_10_percent_tasks": cohort_data.top_10_percent_tasks if cohort_data else None,
            "top_25_percent_tasks": cohort_data.top_25_percent_tasks if cohort_data else None
        }
    }
```

**Example Response:**

```json
{
  "user_stats": {
    "tasks_completed": 8,
    "tasks_this_week": 5,
    "practice_minutes": 140,
    "current_streak": 5,
    "day_in_journey": 12
  },
  "success_benchmark": {
    "target_band": 7.5,
    "day_number": 12,
    "benchmark_tasks": 15,
    "benchmark_practice_minutes": 200,
    "message": "Users who scored 7.5+ had completed 15 tasks by Day 12. You're at 8."
  },
  "cohort_comparison": {
    "cohort_size": 24,
    "avg_tasks_completed": 12,
    "avg_tasks_this_week": 8,
    "user_percentile": 35,
    "message": "Your cohort is averaging 12 tasks. You're at 8. Catch up?"
  },
  "top_performers": {
    "top_10_percent_tasks": 22,
    "top_25_percent_tasks": 18
  }
}
```
