"""
AI Orchestrator - Tiered Intelligence System

Tier 1 (90%): Pure rules - $0
Tier 2 (9%): Small LLM (Claude Haiku) - $0.001/request
Tier 3 (1%): Heavy LLM (Claude Sonnet) - $0.02/request
"""

from typing import Literal, Optional, Dict, Any
from datetime import datetime
import structlog
from anthropic import AsyncAnthropic

from momentum_engine.config import settings
from momentum_engine.ai.prompts import PROMPTS
from momentum_engine.ai.cost_tracker import CostTracker

logger = structlog.get_logger()

TierLevel = Literal[1, 2, 3]


class AIOrchestrator:
    """
    Orchestrates AI calls across tiers with fallback logic.
    
    Usage:
        orchestrator = AIOrchestrator()
        result = await orchestrator.select_task(user_id, context)
    """
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.cost_tracker = CostTracker()
        
        # Model configs
        self.models = {
            2: "claude-3-5-haiku-latest",  # Fast, cheap
            3: "claude-sonnet-4-20250514",  # Powerful
        }
        
        # Cost per 1K tokens (input/output)
        self.costs = {
            2: {"input": 0.00025, "output": 0.00125},
            3: {"input": 0.003, "output": 0.015},
        }
    
    async def select_task(
        self, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select next task for user.
        
        Tier 1: Rule-based selection (default)
        Tier 2: AI-enhanced if user struggling
        """
        # Check if AI intervention needed
        needs_ai = self._needs_ai_intervention(context)
        
        if not needs_ai:
            # Tier 1: Pure rules
            return await self._tier1_task_selection(context)
        
        # Check budget before Tier 2
        if not await self.cost_tracker.has_budget(user_id, tier=2):
            logger.info("User exceeded Tier 2 budget, using Tier 1", user_id=user_id)
            return await self._tier1_task_selection(context)
        
        # Tier 2: AI-assisted selection
        try:
            return await self._tier2_task_selection(user_id, context)
        except Exception as e:
            logger.error("Tier 2 failed, falling back to Tier 1", error=str(e))
            return await self._tier1_task_selection(context)
    
    async def generate_weekly_report(
        self, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized weekly report.
        
        Tier 3: Heavy LLM for detailed analysis
        """
        # Check budget
        if not await self.cost_tracker.has_budget(user_id, tier=3):
            logger.info("User exceeded Tier 3 budget, using template", user_id=user_id)
            return self._template_weekly_report(context)
        
        try:
            return await self._tier3_weekly_report(user_id, context)
        except Exception as e:
            logger.error("Tier 3 failed, using template", error=str(e))
            return self._template_weekly_report(context)
    
    def _needs_ai_intervention(self, context: Dict[str, Any]) -> bool:
        """Determine if AI intervention is needed."""
        # Rule: Struggling users get AI help
        recent_accuracy = context.get("recent_accuracy", 100)
        consecutive_failures = context.get("consecutive_failures", 0)
        
        return recent_accuracy < 60 or consecutive_failures >= 2
    
    async def _tier1_task_selection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pure rule-based task selection (Tier 1)."""
        weak_modules = context.get("weak_modules", [])
        available_tasks = context.get("available_task_ids", [])
        
        # Select task from weak module if available
        if weak_modules and available_tasks:
            selected_id = available_tasks[0]  # Simplified
        else:
            selected_id = available_tasks[0] if available_tasks else None
        
        return {
            "tier": 1,
            "selected_task_id": selected_id,
            "reasoning": "Rule-based selection",
            "cost": 0.0
        }
    
    async def _tier2_task_selection(
        self, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI-enhanced task selection (Tier 2)."""
        prompt = PROMPTS["task_selection"].format(
            recent_tasks=context.get("recent_tasks", []),
            weak_areas=context.get("weak_modules", []),
            available_tasks=context.get("available_task_ids", []),
        )
        
        response = await self.anthropic.messages.create(
            model=self.models[2],
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        task_id = int(response.content[0].text.strip())
        
        # Track cost
        cost = await self.cost_tracker.log_usage(
            user_id=user_id,
            tier=2,
            model=self.models[2],
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
        
        return {
            "tier": 2,
            "selected_task_id": task_id,
            "reasoning": "AI-selected based on weakness analysis",
            "cost": cost
        }
    
    async def _tier3_weekly_report(
        self, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized report (Tier 3)."""
        prompt = PROMPTS["weekly_report"].format(
            week_number=context.get("week_number", 1),
            tasks_completed=context.get("tasks_completed", 0),
            practice_minutes=context.get("practice_minutes", 0),
            lvs=context.get("lvs", 0),
            macr=context.get("macr", 0),
            module_performance=context.get("module_performance", {}),
        )
        
        response = await self.anthropic.messages.create(
            model=self.models[3],
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        report_text = response.content[0].text
        
        # Track cost
        cost = await self.cost_tracker.log_usage(
            user_id=user_id,
            tier=3,
            model=self.models[3],
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
        
        return {
            "tier": 3,
            "report": report_text,
            "cost": cost
        }
    
    def _template_weekly_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback template report when AI unavailable."""
        tasks = context.get("tasks_completed", 0)
        minutes = context.get("practice_minutes", 0)
        
        report = f"""## Week {context.get('week_number', 1)} Summary

**Your Progress:**
- Tasks completed: {tasks}
- Practice time: {minutes} minutes
- Completion rate: {context.get('macr', 0):.1f}%

**Keep Going!**
Consistency is key to IELTS success. Aim for daily practice to maintain momentum.
"""
        
        return {
            "tier": 0,  # Template
            "report": report,
            "cost": 0.0
        }
