# AI Integration Specification

Complete specification for the tiered AI system.

---

## Tiered Intelligence Overview

| Tier | % Operations | Cost/Request | Latency | Use Cases |
|------|-------------|--------------|---------|-----------|
| 1 | 90% | $0 | <50ms | Track assignment, streaks, leaderboards |
| 2 | 9% | $0.001 | <1s | Task selection, nudges |
| 3 | 1% | $0.02 | <5s | Weekly reports, diagnosis |

**Monthly Cost (1M users):** ~$24K (Tier 2: $4K + Tier 3: $20K)

---

## Queue Message Schema

```python
from pydantic import BaseModel
from typing import Literal, Dict, Any
from datetime import datetime

class AIQueueMessage(BaseModel):
    request_id: str
    user_id: str
    tier: Literal[2, 3]
    operation: Literal[
        "daily_task_selection",
        "personalized_nudge", 
        "weekly_report",
        "intervention_diagnosis"
    ]
    context: Dict[str, Any]
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    max_retries: int = 3
    created_at: datetime
    attempt_count: int = 0
```

---

## Retry Logic

```python
async def process_ai_request(message: AIQueueMessage) -> dict:
    """Process with exponential backoff retry."""
    attempt = 0
    
    while attempt < message.max_retries:
        try:
            if not await ai_budget_manager.check_budget(message.user_id, message.tier):
                raise BudgetExceededError("Budget exceeded")
            
            result = await call_llm(message)
            await log_ai_usage(message, result)
            return result
            
        except RateLimitError:
            backoff = min(2 ** attempt + random.uniform(0, 1), 60)
            await asyncio.sleep(backoff)
            attempt += 1
            
        except (APIConnectionError, APITimeoutError):
            await asyncio.sleep(2 ** attempt)
            attempt += 1
            
        except InvalidRequestError as e:
            await log_ai_failure(message, str(e))
            raise
    
    await handle_max_retries_exceeded(message)
    raise MaxRetriesExceededError()
```

---

## Error Handling

### Redis Fallback
```python
async def get_with_fallback(redis_key: str, pg_query: str, params: tuple):
    try:
        return await asyncio.wait_for(redis.get(redis_key), timeout=0.2)
    except (RedisConnectionError, asyncio.TimeoutError):
        return await db.fetchval(pg_query, *params)
```

### PostgreSQL Timeout
```python
async def execute_with_timeout(query: str, *args, timeout_ms: int = 5000):
    try:
        async with db.acquire() as conn:
            await conn.execute(f"SET statement_timeout = '{timeout_ms}ms'")
            return await conn.fetch(query, *args)
    except QueryCanceledError:
        raise HTTPException(504, "Query timeout")
```

---

## Cost Tracking Schema

```sql
CREATE TABLE ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    tier INT CHECK (tier IN (2, 3)),
    operation VARCHAR(50),
    tokens_total INT,
    cost_usd DECIMAL(10, 6),
    latency_ms INT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_ai_budgets (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    monthly_budget_usd DECIMAL(6, 2) DEFAULT 0.50,
    current_month_spend DECIMAL(6, 2) DEFAULT 0.00,
    tier3_calls_this_week INT DEFAULT 0,
    budget_exceeded BOOLEAN DEFAULT FALSE
);
```

---

## Budget Management

```python
class AIBudgetManager:
    MONTHLY_BUDGET_USD = 0.50
    TIER3_WEEKLY_LIMIT = 4
    
    async def check_budget(self, user_id: str, tier: int) -> bool:
        budget = await db.fetchrow(
            "SELECT * FROM user_ai_budgets WHERE user_id = $1", user_id
        )
        
        if budget.current_month_spend >= self.MONTHLY_BUDGET_USD:
            return False
        
        if tier == 3 and budget.tier3_calls_this_week >= self.TIER3_WEEKLY_LIMIT:
            return False
        
        return True
    
    async def log_usage(self, user_id: str, tier: int, cost: float):
        await db.execute("""
            UPDATE user_ai_budgets
            SET current_month_spend = current_month_spend + $2,
                tier3_calls_this_week = tier3_calls_this_week + CASE WHEN $3 = 3 THEN 1 ELSE 0 END
            WHERE user_id = $1
        """, user_id, cost, tier)
```

---

## Cost Calculation

```python
AI_PRICING = {
    "claude-haiku-3-5": {"input_per_1m": 0.25, "output_per_1m": 1.25},
    "claude-sonnet-4": {"input_per_1m": 3.00, "output_per_1m": 15.00}
}

def calculate_cost(usage, tier: int) -> float:
    model = "claude-haiku-3-5" if tier == 2 else "claude-sonnet-4"
    p = AI_PRICING[model]
    return (usage.input_tokens / 1e6) * p["input_per_1m"] + \
           (usage.output_tokens / 1e6) * p["output_per_1m"]
```

---

## SLA Targets

| Metric | Tier 2 | Tier 3 |
|--------|--------|--------|
| Max latency | 1000ms | 5000ms |
| Success rate | 98% | 95% |
| User waits? | No (async) | Yes (loading) |
| Max cost/user/month | $0.50 | $0.50 |
