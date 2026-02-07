# Content Swapping Rules

Dynamic content replacement logic when users struggle with specific modules.

---

## Overview

Content swapping is a Tier 1 (rule-based) intervention that replaces scheduled tasks with targeted remediation content when a user shows signs of struggling.

---

## Trigger Conditions

### 1. Module Weakness Detection

```python
def detect_module_weakness(user_id: str, module: str) -> bool:
    """
    Returns True if user needs intervention in this module.
    
    Tier 1 AI: Pure rule-based, $0 cost
    """
    recent_tasks = get_recent_module_tasks(user_id, module, limit=3)
    
    if len(recent_tasks) < 3:
        return False  # Not enough data
    
    # Criterion 1: Average accuracy below threshold
    avg_accuracy = sum(t.accuracy for t in recent_tasks) / len(recent_tasks)
    if avg_accuracy < 60:
        return True
    
    # Criterion 2: Consecutive failures
    if all(t.accuracy < 50 for t in recent_tasks[-2:]):
        return True
    
    # Criterion 3: Predicted band drop
    band_history = get_predicted_band_history(user_id, module, days=7)
    if len(band_history) >= 2:
        if band_history[-1] - band_history[0] <= -0.5:
            return True
    
    return False
```

### 2. Trigger Thresholds

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Low accuracy | <60% avg (last 3 tasks) | Swap next task |
| Consecutive failures | 2 tasks <50% in row | Swap next task |
| Band score drop | -0.5 points in 7 days | Swap + notification |
| Inactivity | 48+ hours no activity | Rescue task |

### 3. Compound Triggers

```python
def get_intervention_priority(user_id: str) -> str:
    """
    Determine intervention urgency level.
    """
    weakness_count = 0
    for module in ["reading", "writing", "speaking", "listening"]:
        if detect_module_weakness(user_id, module):
            weakness_count += 1
    
    if weakness_count >= 3:
        return "critical"  # Multiple modules struggling
    elif weakness_count >= 2:
        return "high"
    elif weakness_count == 1:
        return "normal"
    else:
        return "none"
```

---

## Intervention Content Pools

### Pre-Defined Intervention Tasks

```python
INTERVENTION_CONTENT = {
    "reading": {
        "strategy_video": [
            {"id": "read_strat_001", "title": "Skimming & Scanning Techniques", "duration_min": 8, "difficulty": "easy"},
            {"id": "read_strat_002", "title": "Time Management for Reading", "duration_min": 10, "difficulty": "easy"},
            {"id": "read_strat_003", "title": "Keyword Spotting Strategy", "duration_min": 7, "difficulty": "easy"},
            {"id": "read_strat_004", "title": "Paragraph Matching Approach", "duration_min": 12, "difficulty": "medium"},
        ],
        "targeted_practice": [
            {"id": "read_prac_001", "title": "True/False/Not Given - Easy Set", "duration_min": 15, "difficulty": "easy"},
            {"id": "read_prac_002", "title": "Matching Headings - Easy Set", "duration_min": 15, "difficulty": "easy"},
            {"id": "read_prac_003", "title": "Summary Completion - Easy Set", "duration_min": 12, "difficulty": "easy"},
            {"id": "read_prac_004", "title": "Multiple Choice - Easy Set", "duration_min": 10, "difficulty": "easy"},
        ],
        "quick_win": [
            {"id": "read_quick_001", "title": "5-Minute Reading Warm-up", "duration_min": 5, "difficulty": "easy"},
            {"id": "read_quick_002", "title": "Vocabulary in Context Quiz", "duration_min": 5, "difficulty": "easy"},
        ]
    },
    "writing": {
        "strategy_video": [
            {"id": "write_strat_001", "title": "Task 2 Structure Breakdown", "duration_min": 12, "difficulty": "easy"},
            {"id": "write_strat_002", "title": "Coherence & Cohesion Tips", "duration_min": 10, "difficulty": "easy"},
            {"id": "write_strat_003", "title": "Task 1 Data Description", "duration_min": 10, "difficulty": "easy"},
            {"id": "write_strat_004", "title": "Linking Words Masterclass", "duration_min": 8, "difficulty": "easy"},
        ],
        "targeted_practice": [
            {"id": "write_prac_001", "title": "Idea Generation Exercise", "duration_min": 10, "difficulty": "easy"},
            {"id": "write_prac_002", "title": "Paragraph Structure Drill", "duration_min": 12, "difficulty": "easy"},
            {"id": "write_prac_003", "title": "Introduction Writing Practice", "duration_min": 10, "difficulty": "easy"},
            {"id": "write_prac_004", "title": "Conclusion Templates", "duration_min": 8, "difficulty": "easy"},
        ],
        "quick_win": [
            {"id": "write_quick_001", "title": "5-Minute Sentence Combining", "duration_min": 5, "difficulty": "easy"},
            {"id": "write_quick_002", "title": "Transition Words Quiz", "duration_min": 5, "difficulty": "easy"},
        ]
    },
    "speaking": {
        "strategy_video": [
            {"id": "speak_strat_001", "title": "Part 1 Common Questions", "duration_min": 10, "difficulty": "easy"},
            {"id": "speak_strat_002", "title": "Cue Card Structure (Part 2)", "duration_min": 12, "difficulty": "easy"},
            {"id": "speak_strat_003", "title": "Extending Answers Technique", "duration_min": 8, "difficulty": "easy"},
            {"id": "speak_strat_004", "title": "Fluency vs Accuracy Balance", "duration_min": 10, "difficulty": "medium"},
        ],
        "targeted_practice": [
            {"id": "speak_prac_001", "title": "Part 1 Easy Topics", "duration_min": 10, "difficulty": "easy"},
            {"id": "speak_prac_002", "title": "Cue Card Practice - Familiar Topics", "duration_min": 12, "difficulty": "easy"},
            {"id": "speak_prac_003", "title": "Opinion Phrases Drill", "duration_min": 8, "difficulty": "easy"},
            {"id": "speak_prac_004", "title": "Pronunciation Focus", "duration_min": 10, "difficulty": "easy"},
        ],
        "quick_win": [
            {"id": "speak_quick_001", "title": "2-Minute Introduction Practice", "duration_min": 5, "difficulty": "easy"},
            {"id": "speak_quick_002", "title": "Common Phrases Review", "duration_min": 5, "difficulty": "easy"},
        ]
    },
    "listening": {
        "strategy_video": [
            {"id": "listen_strat_001", "title": "Note-Taking Strategies", "duration_min": 10, "difficulty": "easy"},
            {"id": "listen_strat_002", "title": "Predicting Answers", "duration_min": 8, "difficulty": "easy"},
            {"id": "listen_strat_003", "title": "Section 4 Academic Lectures", "duration_min": 12, "difficulty": "medium"},
            {"id": "listen_strat_004", "title": "Handling Distractors", "duration_min": 10, "difficulty": "medium"},
        ],
        "targeted_practice": [
            {"id": "listen_prac_001", "title": "Section 1 Easy Practice", "duration_min": 10, "difficulty": "easy"},
            {"id": "listen_prac_002", "title": "Gap Fill Practice", "duration_min": 12, "difficulty": "easy"},
            {"id": "listen_prac_003", "title": "Multiple Choice Easy Set", "duration_min": 10, "difficulty": "easy"},
            {"id": "listen_prac_004", "title": "Map/Diagram Labeling", "duration_min": 12, "difficulty": "easy"},
        ],
        "quick_win": [
            {"id": "listen_quick_001", "title": "5-Minute Dictation", "duration_min": 5, "difficulty": "easy"},
            {"id": "listen_quick_002", "title": "Number & Spelling Practice", "duration_min": 5, "difficulty": "easy"},
        ]
    }
}
```

---

## Swap Decision Logic

```python
from typing import Optional, Dict
from datetime import datetime, timedelta

# Configuration
MAX_SWAPS_PER_WEEK = 3
COOLDOWN_HOURS = 48
MAX_CONSECUTIVE_MODULE_SWAPS = 2

def perform_content_swap(user_id: str, module: str) -> Optional[Dict]:
    """
    Executes content swap for struggling user.
    
    Returns: New task dict or None if swap not allowed
    """
    # Check 1: Weekly swap limit
    recent_swaps = get_recent_swaps(user_id, days=7)
    if len(recent_swaps) >= MAX_SWAPS_PER_WEEK:
        log_swap_skipped(user_id, "weekly_limit_reached")
        return None
    
    # Check 2: Module-specific cooldown
    last_module_swap = get_last_swap_for_module(user_id, module)
    if last_module_swap:
        hours_since = (datetime.now() - last_module_swap.created_at).total_seconds() / 3600
        if hours_since < COOLDOWN_HOURS:
            log_swap_skipped(user_id, "cooldown_active", module=module)
            return None
    
    # Check 3: Consecutive module swap limit
    recent_module_swaps = [s for s in recent_swaps if s.module == module]
    if len(recent_module_swaps) >= MAX_CONSECUTIVE_MODULE_SWAPS:
        # Escalate to Tier 3 AI for personalized intervention
        queue_tier3_intervention(user_id, module)
        return None
    
    # Determine weakness type and select intervention
    weakness_type = diagnose_weakness_type(user_id, module)
    intervention = select_intervention(module, weakness_type)
    
    # Record the swap
    log_content_swap(user_id, module, intervention["id"], weakness_type)
    
    return intervention


def diagnose_weakness_type(user_id: str, module: str) -> str:
    """
    Analyze user's error patterns to determine weakness type.
    """
    recent_tasks = get_recent_module_tasks(user_id, module, limit=5)
    
    # Check time management issues
    avg_time_ratio = sum(t.actual_time / t.expected_time for t in recent_tasks) / len(recent_tasks)
    if avg_time_ratio > 1.3:  # Taking 30%+ longer than expected
        return "time_management"
    
    # Check for specific question type weaknesses
    error_patterns = analyze_error_patterns(recent_tasks)
    if error_patterns.get("consistent_question_type"):
        return "question_type_specific"
    
    # Check vocabulary issues (for reading/listening)
    if module in ["reading", "listening"]:
        vocab_errors = count_vocabulary_related_errors(recent_tasks)
        if vocab_errors > 0.4:  # 40%+ errors vocabulary-related
            return "vocabulary_gap"
    
    # Default to general skill gap
    return "skill_gap"


def select_intervention(module: str, weakness_type: str) -> Dict:
    """
    Select appropriate intervention content based on weakness.
    """
    content_pool = INTERVENTION_CONTENT[module]
    
    if weakness_type == "time_management":
        # Strategy video about time management
        candidates = [c for c in content_pool["strategy_video"] 
                     if "time" in c["title"].lower() or "strategy" in c["title"].lower()]
        
    elif weakness_type == "question_type_specific":
        # Targeted practice for specific question types
        candidates = content_pool["targeted_practice"]
        
    elif weakness_type == "vocabulary_gap":
        # Vocabulary-focused content
        candidates = [c for c in content_pool["targeted_practice"] 
                     if "vocab" in c["title"].lower()]
        if not candidates:
            candidates = content_pool["strategy_video"][:2]
            
    else:  # skill_gap
        # Mix of strategy and easy practice
        candidates = content_pool["strategy_video"][:2] + content_pool["targeted_practice"][:2]
    
    # Select one not recently used
    used_recently = get_recently_used_content(user_id, days=14)
    available = [c for c in candidates if c["id"] not in used_recently]
    
    if not available:
        available = candidates  # Reset if all used
    
    return random.choice(available)
```

---

## Swap Execution Flow

### Which Task Gets Replaced?

```python
def get_task_to_replace(user_id: str, module: str) -> Optional[str]:
    """
    Determine which scheduled task should be replaced.
    
    Priority:
    1. Next scheduled task of the same module
    2. Most difficult task of the day if no module match
    """
    tomorrow_tasks = get_scheduled_tasks(user_id, date=tomorrow())
    
    # Priority 1: Same module task
    module_tasks = [t for t in tomorrow_tasks if t.module == module]
    if module_tasks:
        return module_tasks[0].id
    
    # Priority 2: Hardest task of the day
    if tomorrow_tasks:
        return max(tomorrow_tasks, key=lambda t: t.difficulty_score).id
    
    return None


def execute_swap(user_id: str, old_task_id: str, new_task: Dict):
    """
    Perform the actual swap in the database.
    """
    # Mark original task as swapped (not deleted, for analytics)
    db.execute("""
        UPDATE scheduled_tasks 
        SET status = 'swapped', swapped_at = NOW()
        WHERE id = %s
    """, old_task_id)
    
    # Insert intervention task
    db.execute("""
        INSERT INTO scheduled_tasks 
        (user_id, task_id, scheduled_date, is_intervention, original_task_id)
        VALUES (%s, %s, %s, TRUE, %s)
    """, user_id, new_task["id"], tomorrow(), old_task_id)
    
    # Send notification
    send_notification(user_id, {
        "title": "Personalized task added",
        "body": f"We've added '{new_task['title']}' to help you improve.",
        "action": "view_task"
    })
```

---

## Cool-Down & Escalation Rules

### Limits

| Rule | Value | Rationale |
|------|-------|-----------|
| Max swaps per week | 3 | Prevent infinite loops |
| Cooldown per module | 48 hours | Let user practice |
| Max consecutive module swaps | 2 | Force variety |

### Escalation Path

```python
def check_escalation(user_id: str, module: str) -> Optional[str]:
    """
    Check if user needs escalated intervention.
    """
    swaps_this_month = get_swaps_count(user_id, days=30)
    
    # Level 1: Many swaps, no improvement
    if swaps_this_month >= 6:
        improvement = calculate_improvement(user_id, module, days=30)
        if improvement < 0.1:  # Less than 0.1 band improvement
            return "tier3_diagnosis"
    
    # Level 2: Consistent low performance
    avg_accuracy_30d = get_avg_accuracy(user_id, module, days=30)
    if avg_accuracy_30d < 50:
        return "track_transition_review"
    
    # Level 3: User explicitly struggling
    if user_reported_struggling(user_id):
        return "support_outreach"
    
    return None
```

### Tier 3 AI Escalation

```python
async def queue_tier3_intervention(user_id: str, module: str):
    """
    Queue a Tier 3 AI request for personalized diagnosis.
    
    Only triggered after 2+ swaps with no improvement.
    """
    context = {
        "user_id": user_id,
        "module": module,
        "recent_tasks": get_recent_module_tasks(user_id, module, limit=10),
        "swap_history": get_swap_history(user_id, module),
        "error_patterns": analyze_detailed_errors(user_id, module)
    }
    
    message = AIQueueMessage(
        request_id=str(uuid4()),
        user_id=user_id,
        tier=3,
        operation="intervention_diagnosis",
        context=context,
        priority="high",
        created_at=datetime.now()
    )
    
    await redis.publish("ai_requests", message.json())
```

---

## Analytics & Monitoring

### Swap Effectiveness Tracking

```sql
-- Track swap outcomes
CREATE TABLE content_swaps (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    module VARCHAR(20) NOT NULL,
    weakness_type VARCHAR(50),
    original_task_id UUID,
    intervention_task_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Outcome tracking
    intervention_completed BOOLEAN,
    intervention_accuracy INT,
    post_swap_accuracy INT,  -- Avg accuracy in next 3 tasks of same module
    improvement_delta DECIMAL(3,2)
);

-- Dashboard query: Swap effectiveness
SELECT 
    module,
    weakness_type,
    COUNT(*) as total_swaps,
    AVG(improvement_delta) as avg_improvement,
    SUM(CASE WHEN improvement_delta > 0 THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate
FROM content_swaps
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY module, weakness_type;
```
