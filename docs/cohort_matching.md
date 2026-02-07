# Cohort Matching Algorithm

Specification for grouping users into anonymous cohorts of 20-30 similar learners.

---

## Overview

Cohorts enable social comparison features (ghost data) without revealing user identities. Users are matched based on skill level, learning velocity, and track type to ensure meaningful peer comparisons.

---

## Matching Criteria

### Primary Factors (Weighted)

| Factor | Weight | Description |
|--------|--------|-------------|
| Skill Tier | 50% | Band score bucketed to nearest 0.5 |
| Learning Velocity | 30% | Tasks completed per week category |
| Track Type | 20% | Similar time commitment and goals |

### Skill Tier Calculation

```python
def calculate_skill_tier(diagnostic_score: float) -> float:
    """
    Bucket diagnostic score to nearest 0.5 for cohort matching.
    
    Examples:
        5.3 → 5.5
        6.1 → 6.0
        6.8 → 7.0
    """
    return round(diagnostic_score * 2) / 2
```

### Learning Velocity Classification

```python
def classify_velocity(user_id: str) -> str:
    """
    Classify user's learning velocity based on task completion rate.
    """
    days_active = (datetime.now() - user.created_at).days
    if days_active < 7:
        return "medium"  # Default for new users
    
    weeks_active = max(1, days_active / 7)
    tasks_per_week = user.tasks_completed / weeks_active
    
    if tasks_per_week < 10:
        return "slow"
    elif tasks_per_week < 20:
        return "medium"
    else:
        return "fast"
```

### Cohort Key Generation

```python
def calculate_cohort_key(user: User) -> str:
    """
    Generate unique cohort identifier based on user attributes.
    
    Format: skill_{tier}_velocity_{speed}_track_{track}
    
    Examples:
        "skill_6.5_velocity_medium_track_marathon"
        "skill_7.0_velocity_fast_track_sprint"
        "skill_5.5_velocity_slow_track_foundation"
    """
    skill_tier = calculate_skill_tier(user.diagnostic_score)
    velocity = classify_velocity(user.id)
    track = user.current_track
    
    return f"skill_{skill_tier}_velocity_{velocity}_track_{track}"
```

---

## Cohort Size Rules

### Configuration

```python
# Cohort size boundaries
MIN_COHORT_SIZE = 15      # Below this, merge with adjacent tier
TARGET_COHORT_SIZE = 22   # Optimal for peer comparisons
MAX_COHORT_SIZE = 30      # Hard cap to maintain intimacy
```

### Handling Small Cohorts

```python
def handle_small_cohort(cohort_key: str, member_count: int) -> str:
    """
    Strategy when cohort has fewer than MIN_COHORT_SIZE users.
    """
    if member_count >= MIN_COHORT_SIZE:
        return cohort_key  # No action needed
    
    # Parse cohort key
    parts = parse_cohort_key(cohort_key)
    skill_tier = parts["skill_tier"]
    velocity = parts["velocity"]
    track = parts["track"]
    
    # Strategy 1: Merge with adjacent skill tier (preferred)
    adjacent_tiers = [skill_tier - 0.5, skill_tier + 0.5]
    for adj_skill in adjacent_tiers:
        if 4.0 <= adj_skill <= 9.0:
            adj_key = f"skill_{adj_skill}_velocity_{velocity}_track_{track}"
            adj_count = get_cohort_member_count(adj_key)
            combined = member_count + adj_count
            
            if MIN_COHORT_SIZE <= combined <= MAX_COHORT_SIZE:
                # Merge cohorts
                merge_cohorts(cohort_key, adj_key)
                return adj_key
    
    # Strategy 2: Relax velocity constraint
    for alt_velocity in ["slow", "medium", "fast"]:
        if alt_velocity != velocity:
            alt_key = f"skill_{skill_tier}_velocity_{alt_velocity}_track_{track}"
            alt_count = get_cohort_member_count(alt_key)
            combined = member_count + alt_count
            
            if MIN_COHORT_SIZE <= combined <= MAX_COHORT_SIZE:
                merge_cohorts(cohort_key, alt_key)
                return alt_key
    
    # Strategy 3: Use global ghost data (no cohort match found)
    return "global"
```

### Handling Large Cohorts

```python
def handle_large_cohort(cohort_key: str, member_count: int) -> list:
    """
    Split cohort when it exceeds MAX_COHORT_SIZE.
    """
    if member_count <= MAX_COHORT_SIZE:
        return [cohort_key]
    
    # Split into sub-cohorts based on registration date
    members = get_cohort_members(cohort_key, order_by="created_at")
    num_splits = (member_count // TARGET_COHORT_SIZE) + 1
    
    new_cohorts = []
    for i in range(num_splits):
        new_key = f"{cohort_key}_sub{i+1}"
        start_idx = i * TARGET_COHORT_SIZE
        end_idx = min((i + 1) * TARGET_COHORT_SIZE, member_count)
        
        for member in members[start_idx:end_idx]:
            reassign_user_to_cohort(member.id, new_key)
        
        new_cohorts.append(new_key)
    
    return new_cohorts
```

---

## Cohort Recalculation

### Schedule

```python
# Recalculate cohorts every Monday at 00:00 UTC
COHORT_RECALCULATION_SCHEDULE = "0 0 * * 1"  # Cron expression
```

### Recalculation Logic

```python
async def recalculate_cohorts():
    """
    Weekly cohort reassignment job.
    
    Runs every Monday to:
    1. Recalculate cohort keys for active users
    2. Move users who changed skill/velocity/track
    3. Balance cohort sizes
    """
    active_users = await get_active_users(days=14)
    moves = []
    
    for user in active_users:
        current_key = user.cohort_key
        new_key = calculate_cohort_key(user)
        
        if current_key != new_key:
            moves.append({
                "user_id": user.id,
                "from_cohort": current_key,
                "to_cohort": new_key,
                "reason": determine_move_reason(user, current_key, new_key)
            })
    
    # Execute moves
    for move in moves:
        await reassign_user_to_cohort(
            move["user_id"], 
            move["to_cohort"],
            log_reason=move["reason"]
        )
    
    # Rebalance cohort sizes
    await rebalance_all_cohorts()
    
    # Update cohort stats
    await update_all_cohort_stats()
    
    logger.info(f"Cohort recalculation complete. {len(moves)} users moved.")


def determine_move_reason(user: User, old_key: str, new_key: str) -> str:
    """Determine why user is moving cohorts."""
    old_parts = parse_cohort_key(old_key)
    new_parts = parse_cohort_key(new_key)
    
    reasons = []
    
    if old_parts["skill_tier"] != new_parts["skill_tier"]:
        if new_parts["skill_tier"] > old_parts["skill_tier"]:
            reasons.append("skill_improved")
        else:
            reasons.append("skill_declined")
    
    if old_parts["velocity"] != new_parts["velocity"]:
        reasons.append("velocity_changed")
    
    if old_parts["track"] != new_parts["track"]:
        reasons.append("track_changed")
    
    return ",".join(reasons) if reasons else "unknown"
```

### Cohort Stability Rules

| Rule | Description |
|------|-------------|
| No mid-week moves | Users stay in cohort until next Monday |
| Improvement celebration | Users who improve stay 2+ weeks to celebrate with peers |
| Gradual transitions | Move max 20% of cohort per week to maintain stability |

```python
def should_move_user_immediately(user: User, improvement: float) -> bool:
    """
    Check if user should move outside regular Monday cycle.
    
    Only for significant improvements (1.0+ band points).
    """
    if improvement >= 1.0:
        # Check if in current cohort for at least 2 weeks
        time_in_cohort = datetime.now() - user.cohort_joined_at
        if time_in_cohort.days >= 14:
            return True
    
    return False
```

---

## Edge Cases

### New User (No History)

```python
async def assign_new_user_to_cohort(user: User):
    """
    Assign new user to cohort based on diagnostic only.
    
    New users default to "medium" velocity assumption.
    """
    skill_tier = calculate_skill_tier(user.diagnostic_score)
    track = user.assigned_track
    
    # Default velocity for new users
    cohort_key = f"skill_{skill_tier}_velocity_medium_track_{track}"
    
    # Find or create cohort
    cohort = await get_or_create_cohort(cohort_key)
    
    # Check size constraints
    if cohort.member_count >= MAX_COHORT_SIZE:
        cohort_key = handle_large_cohort(cohort_key, cohort.member_count + 1)[0]
    
    await assign_user_to_cohort(user.id, cohort_key)
    
    logger.info(f"New user {user.id} assigned to cohort {cohort_key}")
```

### User Significantly Improves

```python
async def handle_significant_improvement(user_id: str, old_band: float, new_band: float):
    """
    Handle user who improved 1.0+ band points.
    
    Triggers immediate cohort graduation + celebration notification.
    """
    improvement = new_band - old_band
    
    if improvement >= 1.0:
        user = await get_user(user_id)
        
        # Check minimum time in current cohort
        time_in_cohort = datetime.now() - user.cohort_joined_at
        if time_in_cohort.days < 14:
            # Too soon to move - let them celebrate
            return
        
        # Calculate new cohort
        new_cohort_key = calculate_cohort_key(user)
        
        if new_cohort_key != user.cohort_key:
            await reassign_user_to_cohort(user_id, new_cohort_key)
            
            # Send celebration notification
            await send_notification(user_id, {
                "title": "🎉 You've leveled up!",
                "body": f"Congrats on your improvement! You're now in a new cohort with peers at your level.",
                "type": "celebration"
            })
```

### Inactive Users

```python
# Inactivity thresholds
INACTIVE_EXCLUSION_DAYS = 14    # Excluded from cohort stats
INACTIVE_REMOVAL_DAYS = 30      # Removed from cohort entirely

async def handle_inactive_users():
    """
    Process inactive users for cohort health.
    
    Runs daily as part of maintenance job.
    """
    now = datetime.now()
    
    # Exclude from stats (14+ days inactive)
    inactive_14d = await db.fetch("""
        SELECT id FROM users 
        WHERE last_activity_date < NOW() - INTERVAL '14 days'
        AND cohort_excluded = FALSE
    """)
    
    for user in inactive_14d:
        await db.execute("""
            UPDATE users SET cohort_excluded = TRUE WHERE id = %s
        """, user.id)
    
    # Remove from cohort (30+ days inactive)
    inactive_30d = await db.fetch("""
        SELECT id, cohort_id FROM users 
        WHERE last_activity_date < NOW() - INTERVAL '30 days'
        AND cohort_id IS NOT NULL
    """)
    
    for user in inactive_30d:
        await remove_from_cohort(user.id)
        await db.execute("""
            UPDATE cohorts SET member_count = member_count - 1 WHERE id = %s
        """, user.cohort_id)


async def handle_returning_user(user_id: str):
    """
    Reassign returning user to appropriate cohort.
    
    Called when inactive user resumes activity.
    """
    user = await get_user(user_id)
    
    # Recalculate cohort based on current metrics
    new_cohort_key = calculate_cohort_key(user)
    await assign_user_to_cohort(user_id, new_cohort_key)
    
    # Mark as active
    await db.execute("""
        UPDATE users 
        SET cohort_excluded = FALSE, last_activity_date = NOW()
        WHERE id = %s
    """, user_id)
    
    # Send welcome back notification
    await send_notification(user_id, {
        "title": "Welcome back! 👋",
        "body": "You've been matched with a new study cohort. Let's continue your IELTS journey!",
        "type": "welcome_back"
    })
```

---

## Database Schema

```sql
CREATE TABLE cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_key VARCHAR(100) UNIQUE NOT NULL,
    skill_tier DECIMAL(2,1) NOT NULL,
    velocity_tier VARCHAR(20) NOT NULL,
    track VARCHAR(50) NOT NULL,
    member_count INT DEFAULT 0,
    active_member_count INT DEFAULT 0,
    avg_tasks_per_week DECIMAL(5,2),
    avg_accuracy DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for cohort lookup
CREATE INDEX idx_cohorts_key ON cohorts(cohort_key);
CREATE INDEX idx_cohorts_skill ON cohorts(skill_tier);

-- User cohort assignment tracking
ALTER TABLE users ADD COLUMN cohort_key VARCHAR(100);
ALTER TABLE users ADD COLUMN cohort_joined_at TIMESTAMP;
ALTER TABLE users ADD COLUMN cohort_excluded BOOLEAN DEFAULT FALSE;

-- Cohort movement history
CREATE TABLE cohort_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    from_cohort VARCHAR(100),
    to_cohort VARCHAR(100),
    reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

```python
@router.post("/cohorts/assign")
async def assign_to_cohort(user_id: str):
    """Assign or reassign user to appropriate cohort."""
    user = await get_user(user_id)
    cohort_key = calculate_cohort_key(user)
    await assign_user_to_cohort(user_id, cohort_key)
    return {"cohort_key": cohort_key}


@router.get("/cohort/{cohort_id}/stats")
async def get_cohort_stats(cohort_id: str):
    """Get aggregate statistics for a cohort."""
    cohort = await get_cohort(cohort_id)
    return {
        "cohort_key": cohort.cohort_key,
        "member_count": cohort.member_count,
        "active_member_count": cohort.active_member_count,
        "avg_tasks_per_week": cohort.avg_tasks_per_week,
        "avg_accuracy": cohort.avg_accuracy
    }
```
