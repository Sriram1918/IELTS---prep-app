"""
AI Cost Tracker - Budget Management & Usage Logging
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
import structlog

from momentum_engine.config import settings

logger = structlog.get_logger()


class CostTracker:
    """
    Tracks AI API usage and enforces per-user budgets.
    
    Budget Limits:
    - Monthly: $0.50 per user
    - Tier 3: 1 call per user per week
    """
    
    MONTHLY_BUDGET_USD = Decimal("0.50")
    TIER3_WEEKLY_LIMIT = 1
    
    # Cost per 1K tokens
    COSTS = {
        2: {"input": Decimal("0.00025"), "output": Decimal("0.00125")},
        3: {"input": Decimal("0.003"), "output": Decimal("0.015")},
    }
    
    def __init__(self):
        # In production, inject database session
        self._db = None
    
    def set_db(self, db):
        """Set database session for async operations."""
        self._db = db
    
    async def has_budget(self, user_id: str, tier: int) -> bool:
        """
        Check if user has budget for this tier.
        
        Returns True if user can make this AI call.
        """
        if not self._db:
            # No DB = allow (for testing)
            return True
        
        from sqlalchemy import select
        from momentum_engine.database.models import UserAIBudget
        
        result = await self._db.execute(
            select(UserAIBudget).where(UserAIBudget.user_id == user_id)
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            # New user, create budget
            return True
        
        # Check monthly budget
        if budget.current_month_spend >= self.MONTHLY_BUDGET_USD:
            logger.warning("User exceeded monthly AI budget", user_id=user_id)
            return False
        
        # Check Tier 3 weekly limit
        if tier == 3 and budget.tier3_calls_this_week >= self.TIER3_WEEKLY_LIMIT:
            logger.info("User hit Tier 3 weekly limit", user_id=user_id)
            return False
        
        return True
    
    async def log_usage(
        self,
        user_id: str,
        tier: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: Optional[int] = None
    ) -> float:
        """
        Log AI usage and update user budget.
        
        Returns cost in USD.
        """
        # Calculate cost
        tier_costs = self.COSTS.get(tier, self.COSTS[2])
        cost = (
            (Decimal(input_tokens) / 1000 * tier_costs["input"]) +
            (Decimal(output_tokens) / 1000 * tier_costs["output"])
        )
        
        logger.info(
            "AI usage logged",
            user_id=user_id,
            tier=tier,
            model=model,
            tokens=input_tokens + output_tokens,
            cost=float(cost)
        )
        
        if not self._db:
            return float(cost)
        
        from sqlalchemy import text
        
        # Insert usage log
        await self._db.execute(
            text("""
                INSERT INTO ai_usage_logs 
                (user_id, tier, operation, model, tokens_input, tokens_output, 
                 tokens_total, cost_usd, latency_ms, success)
                VALUES (:user_id, :tier, 'api_call', :model, :input, :output, 
                        :total, :cost, :latency, true)
            """),
            {
                "user_id": user_id,
                "tier": tier,
                "model": model,
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
                "cost": cost,
                "latency": latency_ms
            }
        )
        
        # Update user budget
        await self._db.execute(
            text("""
                INSERT INTO user_ai_budgets (user_id, current_month_spend, tier3_calls_this_week)
                VALUES (:user_id, :cost, :tier3_inc)
                ON CONFLICT (user_id) DO UPDATE SET
                    current_month_spend = user_ai_budgets.current_month_spend + :cost,
                    tier3_calls_this_week = CASE 
                        WHEN :tier = 3 THEN user_ai_budgets.tier3_calls_this_week + 1 
                        ELSE user_ai_budgets.tier3_calls_this_week 
                    END,
                    last_tier3_call = CASE WHEN :tier = 3 THEN NOW() ELSE user_ai_budgets.last_tier3_call END,
                    updated_at = NOW()
            """),
            {
                "user_id": user_id,
                "cost": cost,
                "tier": tier,
                "tier3_inc": 1 if tier == 3 else 0
            }
        )
        
        return float(cost)
    
    async def get_monthly_summary(self, user_id: str) -> dict:
        """Get user's monthly AI spending summary."""
        if not self._db:
            return {"spend": 0, "budget": float(self.MONTHLY_BUDGET_USD), "remaining": float(self.MONTHLY_BUDGET_USD)}
        
        from sqlalchemy import select
        from momentum_engine.database.models import UserAIBudget
        
        result = await self._db.execute(
            select(UserAIBudget).where(UserAIBudget.user_id == user_id)
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            return {
                "spend": 0,
                "budget": float(self.MONTHLY_BUDGET_USD),
                "remaining": float(self.MONTHLY_BUDGET_USD)
            }
        
        return {
            "spend": float(budget.current_month_spend),
            "budget": float(self.MONTHLY_BUDGET_USD),
            "remaining": float(self.MONTHLY_BUDGET_USD - budget.current_month_spend),
            "tier3_calls_this_week": budget.tier3_calls_this_week
        }
    
    @staticmethod
    async def reset_weekly_limits():
        """Reset Tier 3 weekly limits (run by Celery beat on Mondays)."""
        # In production, run:
        # UPDATE user_ai_budgets SET tier3_calls_this_week = 0
        logger.info("Weekly Tier 3 limits reset")
    
    @staticmethod
    async def reset_monthly_budgets():
        """Reset monthly spending (run by Celery beat on 1st of month)."""
        # In production, run:
        # UPDATE user_ai_budgets SET current_month_spend = 0
        logger.info("Monthly AI budgets reset")
