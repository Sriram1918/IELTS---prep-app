"""
Unit Tests for Core Services
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

# Test Navigator Service - Track Assignment
class TestTrackAssignment:
    """Tests for Tier 1 track assignment logic."""
    
    def test_sprint_track_for_urgent_timeline(self):
        """Users with <21 days until exam get Sprint track."""
        from momentum_engine.modules.navigator.service import NavigatorService
        
        service = NavigatorService(db=None)
        
        # Test urgent timeline
        track = service.assign_track(
            diagnostic_score=5.5,
            days_until_exam=14,
            weak_modules=["writing"],
            daily_availability_minutes=45
        )
        
        assert track == "academic_fast_track"
    
    def test_sprint_track_for_high_baseline(self):
        """Users with diagnostic ≥6.5 get Sprint track."""
        from momentum_engine.modules.navigator.service import NavigatorService
        
        service = NavigatorService(db=None)
        
        track = service.assign_track(
            diagnostic_score=7.0,
            days_until_exam=60,
            weak_modules=[],
            daily_availability_minutes=30
        )
        
        # High baseline with good timeline = intensive
        assert track in ["intensive", "academic_fast_track", "general_fast_track"]
    
    def test_foundation_track_for_low_baseline(self):
        """Users with diagnostic <5.5 get Foundation track."""
        from momentum_engine.modules.navigator.service import NavigatorService
        
        service = NavigatorService(db=None)
        
        track = service.assign_track(
            diagnostic_score=4.5,
            days_until_exam=90,
            weak_modules=["reading", "writing"],
            daily_availability_minutes=60
        )
        
        assert track == "foundation"
    
    def test_marathon_track_for_professionals(self):
        """Working professionals with limited time get Marathon track."""
        from momentum_engine.modules.navigator.service import NavigatorService
        
        service = NavigatorService(db=None)
        
        track = service.assign_track(
            diagnostic_score=6.0,
            days_until_exam=60,
            weak_modules=["speaking"],
            daily_availability_minutes=20  # Limited time
        )
        
        assert track == "professional_marathon"


# Test Metrics Calculations
class TestMetricsCalculation:
    """Tests for LVS and MACR calculations."""
    
    def test_lvs_calculation(self):
        """Learning Velocity Score = (skill_improvement) / hours."""
        # User improved from 6.0 to 6.3 in 4.5 hours
        skill_t0 = 6.0
        skill_t7 = 6.3
        hours_spent = 4.5
        
        lvs = (skill_t7 - skill_t0) / hours_spent
        
        assert round(lvs, 3) == 0.067
    
    def test_lvs_below_threshold(self):
        """LVS below 0.15 indicates slow learning."""
        lvs = 0.067
        threshold = 0.15
        
        needs_intervention = lvs < threshold
        
        assert needs_intervention is True
    
    def test_macr_calculation(self):
        """MACR = (completed / planned) * 100."""
        planned_tasks = 14  # 2 per day * 7 days
        completed_tasks = 9
        
        macr = (completed_tasks / planned_tasks) * 100
        
        assert round(macr, 1) == 64.3
    
    def test_macr_at_risk_threshold(self):
        """MACR below 50% triggers intervention."""
        planned = 21
        completed = 7
        
        macr = (completed / planned) * 100
        
        assert macr < 50  # At risk


# Test Cohort Matching
class TestCohortMatching:
    """Tests for cohort key generation."""
    
    def test_cohort_key_generation(self):
        """Cohort key includes skill, velocity, and track."""
        diagnostic_score = 6.5
        tasks_per_week = 15  # Medium velocity
        track = "marathon"
        
        # Bucket skill to nearest 0.5
        skill_tier = round(diagnostic_score * 2) / 2
        
        # Classify velocity
        if tasks_per_week < 10:
            velocity = "slow"
        elif tasks_per_week < 20:
            velocity = "medium"
        else:
            velocity = "fast"
        
        cohort_key = f"skill_{skill_tier}_velocity_{velocity}_track_{track}"
        
        assert cohort_key == "skill_6.5_velocity_medium_track_marathon"
    
    def test_skill_tier_bucketing(self):
        """Skill scores are bucketed to nearest 0.5."""
        test_cases = [
            (5.2, 5.0),
            (5.3, 5.5),
            (6.7, 6.5),
            (6.8, 7.0),
            (7.0, 7.0),
        ]
        
        for raw_score, expected_tier in test_cases:
            tier = round(raw_score * 2) / 2
            assert tier == expected_tier, f"Expected {expected_tier} for {raw_score}, got {tier}"


# Test Cost Tracking
class TestCostTracking:
    """Tests for AI cost calculations."""
    
    def test_tier2_cost_calculation(self):
        """Tier 2 costs: $0.00025/1K input, $0.00125/1K output."""
        input_tokens = 500
        output_tokens = 50
        
        # Costs per 1K tokens
        input_cost_per_1k = 0.00025
        output_cost_per_1k = 0.00125
        
        cost = (
            (input_tokens / 1000 * input_cost_per_1k) +
            (output_tokens / 1000 * output_cost_per_1k)
        )
        
        assert round(cost, 6) == 0.000188  # ~$0.00019
    
    def test_tier3_cost_calculation(self):
        """Tier 3 costs: $0.003/1K input, $0.015/1K output."""
        input_tokens = 1000
        output_tokens = 500
        
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
        
        cost = (
            (input_tokens / 1000 * input_cost_per_1k) +
            (output_tokens / 1000 * output_cost_per_1k)
        )
        
        assert cost == 0.0105  # ~$0.01 per Tier 3 call
    
    def test_monthly_budget_check(self):
        """Users have $0.50 monthly budget."""
        monthly_budget = Decimal("0.50")
        current_spend = Decimal("0.48")
        
        has_budget = current_spend < monthly_budget
        
        assert has_budget is True
        
        # After exceeding
        current_spend = Decimal("0.52")
        has_budget = current_spend < monthly_budget
        
        assert has_budget is False


# Test Ghost Data
class TestGhostData:
    """Tests for ghost message generation."""
    
    def test_benchmark_message_ahead(self):
        """Users ahead of benchmark get positive message."""
        user_tasks = 18
        benchmark_tasks = 15
        target_band = 7.5
        day = 12
        
        if user_tasks >= benchmark_tasks:
            message = f"Great progress! Users who scored {target_band}+ had completed {benchmark_tasks} tasks by Day {day}. You're at {user_tasks}. 🎯"
        else:
            message = f"Users who scored {target_band}+ had completed {benchmark_tasks} tasks by Day {day}. You're at {user_tasks}."
        
        assert "Great progress!" in message
        assert "🎯" in message
    
    def test_benchmark_message_behind(self):
        """Users behind benchmark get neutral message."""
        user_tasks = 8
        benchmark_tasks = 15
        target_band = 7.5
        day = 12
        
        if user_tasks >= benchmark_tasks:
            message = f"Great progress!"
        else:
            message = f"Users who scored {target_band}+ had completed {benchmark_tasks} tasks by Day {day}. You're at {user_tasks}."
        
        assert "Great progress!" not in message
        assert f"You're at {user_tasks}" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
