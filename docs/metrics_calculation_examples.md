# Metrics Calculation Examples

Concrete examples of LVS, MACR, and CRC calculations.

---

## Learning Velocity Score (LVS)

### Formula
```
LVS = (Skill_t+7 - Skill_t) / Hours_spent_in_week
```

### Definition
- **Skill** = Predicted Band Score (from recent task performance)
- **Success Target**: 70% of active users maintain LVS ≥ 0.15

### Example 1: Good Progress

**User: Raj**
```
Day 0 Predicted Band: 6.0
Day 7 Predicted Band: 6.3
Hours spent: 4.5 hours (270 min)

LVS = (6.3 - 6.0) / 4.5 = 0.067
```

**Interpretation:**
- LVS = 0.067 (BELOW target of 0.15)
- Raj is learning slower than expected
- **Action:** Trigger content swap or motivational nudge

### Example 2: Excellent Progress

**User: Priya**
```
Day 0 Predicted Band: 5.5
Day 7 Predicted Band: 6.2
Hours spent: 5 hours

LVS = (6.2 - 5.5) / 5 = 0.14
```

**Interpretation:**
- LVS = 0.14 (close to target)
- Priya is progressing well
- **Action:** Continue current track

### Code Implementation

```python
async def calculate_lvs(user_id: str) -> float:
    """Calculate Learning Velocity Score for past 7 days."""
    # Get band score from 7 days ago
    skill_t0 = await db.fetchval("""
        SELECT predicted_band FROM user_metrics
        WHERE user_id = $1 AND date = CURRENT_DATE - 7
    """, user_id)
    
    # Current band
    user = await get_user(user_id)
    skill_t7 = user.predicted_band
    
    # Hours spent in past week
    minutes = await db.fetchval("""
        SELECT COALESCE(SUM(time_spent_minutes), 0)
        FROM user_progress
        WHERE user_id = $1 AND completed_at >= NOW() - INTERVAL '7 days'
    """, user_id)
    
    hours = minutes / 60
    if hours == 0 or skill_t0 is None:
        return 0.0
    
    return round((skill_t7 - skill_t0) / hours, 3)
```

---

## Micro-Action Completion Rate (MACR)

### Formula
```
MACR = (Completed_Actions / Planned_Actions) × 100
```

### Definition
- **Actions** = Daily planned tasks from user's track
- **Success Target:** Median 65-70%

### Example 1: On Track

**User: Priya (Professional Marathon)**
```
Planned tasks this week: 14 (2/day × 7 days)
Completed tasks: 9

MACR = (9 / 14) × 100 = 64.3%
```

**Interpretation:**
- MACR = 64% (within target 65-70%)
- Slightly under but acceptable
- **Action:** No intervention needed

### Example 2: At Risk

**User: Amit (Sprint track)**
```
Planned tasks this week: 21 (3/day × 7 days)
Completed tasks: 7

MACR = (7 / 21) × 100 = 33.3%
```

**Interpretation:**
- MACR = 33% (WELL BELOW target)
- Amit is struggling with workload
- **Action:** 
  - Trigger "Quick Win Rescue Task"
  - Reduce tomorrow's plan from 3 → 2 tasks
  - Consider track transition

### Code Implementation

```python
async def calculate_macr(user_id: str) -> float:
    """Calculate Micro-Action Completion Rate for past 7 days."""
    user = await get_user(user_id)
    track = await get_track(user.current_track)
    
    planned = track.tasks_per_day * 7
    
    completed = await db.fetchval("""
        SELECT COUNT(*) FROM user_progress
        WHERE user_id = $1 AND completed_at >= NOW() - INTERVAL '7 days'
    """, user_id)
    
    if planned == 0:
        return 0.0
    
    return round((completed / planned) * 100, 2)
```

---

## Cohort Retention Coefficient (CRC)

### Formula
```
CRC = Pearson_correlation(user_day28_status, cohort_weekly_activity)
```

### Definition
- **user_day28_status**: 1 = still active on Day 28, 0 = churned
- **cohort_weekly_activity**: Average tasks/week by cohort
- **Success Target:** CRC ≥ 0.55

### Example Calculation

**Cohort: skill_6.5_velocity_medium_track_marathon (25 users)**

| User | Day 28 Active | Cohort Avg Tasks/Week |
|------|---------------|----------------------|
| 1 | 1 | 15 |
| 2 | 1 | 18 |
| 3 | 0 | 8 |
| 4 | 1 | 20 |
| 5 | 0 | 6 |
| ... | ... | ... |

```python
from scipy.stats import pearsonr

day28_status = [1, 1, 0, 1, 0, 1, 1, 0, ...]
cohort_activity = [15, 18, 8, 20, 6, 17, 19, 5, ...]

crc, p_value = pearsonr(day28_status, cohort_activity)
# Result: crc = 0.62, p_value = 0.001
```

**Interpretation:**
- CRC = 0.62 (ABOVE target of 0.55)
- Strong positive correlation
- Users in active cohorts stay longer
- **Validation:** Social loops are working!

### Code Implementation

```python
from scipy.stats import pearsonr

async def calculate_crc(cohort_id: str) -> float:
    """Calculate Cohort Retention Coefficient."""
    users = await db.fetch("""
        SELECT 
            id,
            CASE WHEN last_activity_date >= CURRENT_DATE - 7 THEN 1 ELSE 0 END as active,
            tasks_completed / NULLIF(EXTRACT(days FROM NOW() - created_at) / 7, 0) as weekly_rate
        FROM users
        WHERE cohort_id = $1 AND created_at <= CURRENT_DATE - 28
    """, cohort_id)
    
    if len(users) < 10:
        return 0.0
    
    retention = [u.active for u in users]
    activity = [u.weekly_rate or 0 for u in users]
    
    crc, _ = pearsonr(retention, activity)
    return round(crc, 3)
```

---

## Daily Metrics Job

```python
async def calculate_daily_metrics():
    """Run daily to calculate LVS, MACR for all active users."""
    active_users = await db.fetch("""
        SELECT id FROM users
        WHERE last_activity_date >= CURRENT_DATE - 7
    """)
    
    for user in active_users:
        lvs = await calculate_lvs(user.id)
        macr = await calculate_macr(user.id)
        
        await db.execute("""
            INSERT INTO user_metrics (user_id, date, lvs, macr)
            VALUES ($1, CURRENT_DATE, $2, $3)
            ON CONFLICT (user_id, date) DO UPDATE SET lvs = $2, macr = $3
        """, user.id, lvs, macr)
    
    logger.info(f"Calculated metrics for {len(active_users)} users")
```

---

## Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| LVS | < 0.10 | < 0.05 | Content swap |
| MACR | < 50% | < 30% | Workload reduction |
| CRC | < 0.50 | < 0.40 | Review social features |
