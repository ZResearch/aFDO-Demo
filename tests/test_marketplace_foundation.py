"""Test suite for aFDO Marketplace foundation components."""

import pytest
import asyncio
from shared.budget_manager import BudgetManager, Transaction
from shared.queue_manager import QueueManager, QueuedRequest
from shared.reputation_manager import ReputationManager
from shared.selection_policy import (
    CheapestPolicy, FastestPolicy, BestReputationPolicy, BalancedPolicy
)
from shared.negotiation import Quote, QuoteRequest, FlexibleStrategy


class TestBudgetManager:
    """Test BudgetManager functionality."""

    def test_initialization(self):
        """Test budget manager initialization."""
        budget = BudgetManager(total_budget=1.0)
        assert budget.total_budget == 1.0
        assert budget.spent == 0.0
        assert budget.reserved == 0.0
        assert budget.get_available() == 1.0

    def test_reserve_commit_flow(self):
        """Test reserve/commit pattern."""
        budget = BudgetManager(total_budget=1.0)

        # Reserve
        res_id = budget.reserve(0.25, "test_op", "test_agent")
        assert res_id is not None
        assert budget.get_available() == 0.75
        assert budget.reserved == 0.25

        # Commit
        success = budget.commit(res_id, 0.20)
        assert success
        assert budget.spent == 0.20
        assert budget.reserved == 0.0
        assert budget.get_available() == 0.80

    def test_budget_exhaustion(self):
        """Test budget exhaustion handling."""
        budget = BudgetManager(total_budget=0.10)

        # First reservation succeeds
        res1 = budget.reserve(0.08, "op1")
        assert res1 is not None

        # Second reservation fails (insufficient budget)
        res2 = budget.reserve(0.05, "op2")
        assert res2 is None

    def test_release_reservation(self):
        """Test releasing unused reservations."""
        budget = BudgetManager(total_budget=1.0)

        res_id = budget.reserve(0.30, "test_op")
        assert budget.get_available() == 0.70

        # Release
        success = budget.release(res_id)
        assert success
        assert budget.get_available() == 1.0
        assert budget.reserved == 0.0

    def test_budget_breakdown(self):
        """Test budget breakdown reporting."""
        budget = BudgetManager(total_budget=1.0)

        res1 = budget.reserve(0.30, "extract_text", "agent1")
        budget.commit(res1, 0.28)

        res2 = budget.reserve(0.20, "analyze", "agent2")
        budget.commit(res2, 0.22)

        breakdown = budget.get_breakdown()

        assert breakdown["total_budget"] == 1.0
        assert breakdown["spent"] == 0.50
        assert "extract_text" in breakdown["by_operation"]
        assert "analyze" in breakdown["by_operation"]


class TestQueueManager:
    """Test QueueManager functionality."""

    @pytest.mark.asyncio
    async def test_dynamic_pricing(self):
        """Test dynamic pricing based on queue length."""
        queue_mgr = QueueManager(base_cost=0.05, max_queue_size=10)

        # Empty queue - base price
        assert queue_mgr.get_current_price() == 0.05

        # Add requests - price should increase
        for i in range(5):
            request = QueuedRequest(
                request_id=f"req{i}",
                caller_pid="caller",
                operation="test_op",
                parameters={}
            )
            await queue_mgr.add_request(request)

        # With 5 requests in queue of max 10, price should be higher
        current_price = queue_mgr.get_current_price()
        assert current_price > 0.05
        assert current_price < 0.05 * 3  # Max 3x with default surge factor

    @pytest.mark.asyncio
    async def test_queue_status(self):
        """Test queue status reporting."""
        queue_mgr = QueueManager(base_cost=0.10, max_queue_size=5)

        status = queue_mgr.get_queue_status()
        assert status.queue_length == 0
        assert status.availability_status == "available"

        # Add requests
        for i in range(3):
            request = QueuedRequest(
                request_id=f"req{i}",
                caller_pid="caller",
                operation="test",
                parameters={}
            )
            await queue_mgr.add_request(request)

        status = queue_mgr.get_queue_status()
        assert status.queue_length == 3
        assert status.availability_status == "busy"


class TestReputationManager:
    """Test ReputationManager functionality."""

    def test_initial_reputation(self):
        """Test default reputation score."""
        rep_mgr = ReputationManager("test_agent")
        score = rep_mgr.calculate_score()

        # Default score should be reasonable (around 0.85)
        assert 0.80 <= score <= 0.90

    def test_reputation_with_operations(self):
        """Test reputation updates with operation records."""
        rep_mgr = ReputationManager("test_agent")

        # Record successful operations
        for i in range(10):
            rep_mgr.record_operation(
                operation_id=f"op{i}",
                operation_name="test_op",
                success=True,
                estimated_duration=5.0,
                actual_duration=4.8,
                estimated_cost=0.05,
                actual_cost=0.05
            )

        score = rep_mgr.calculate_score()
        assert score > 0.85  # Should be high with all successes

    def test_reputation_with_failures(self):
        """Test reputation penalty for failures."""
        rep_mgr = ReputationManager("test_agent")

        # Mix of successes and failures
        for i in range(5):
            rep_mgr.record_operation(
                operation_id=f"op{i}",
                operation_name="test",
                success=True,
                estimated_duration=5.0,
                actual_duration=5.0,
                estimated_cost=0.05,
                actual_cost=0.05
            )

        for i in range(5, 10):
            rep_mgr.record_operation(
                operation_id=f"op{i}",
                operation_name="test",
                success=False,
                estimated_duration=5.0,
                actual_duration=5.0,
                estimated_cost=0.05,
                actual_cost=0.05
            )

        score = rep_mgr.calculate_score()
        # 50% success rate should lower score
        assert score < 0.70

    def test_caller_ratings(self):
        """Test caller rating integration."""
        rep_mgr = ReputationManager("test_agent")

        # Add some operations for context
        for i in range(5):
            rep_mgr.record_operation(
                operation_id=f"op{i}",
                operation_name="test",
                success=True,
                estimated_duration=5.0,
                actual_duration=5.0,
                estimated_cost=0.05,
                actual_cost=0.05
            )

        # Add caller ratings
        rep_mgr.record_caller_rating("caller1", overall=5.0)
        rep_mgr.record_caller_rating("caller2", overall=4.5)
        rep_mgr.record_caller_rating("caller3", overall=4.8)

        breakdown = rep_mgr.get_reputation_breakdown()
        assert breakdown["overall_score"] > 0.85
        assert "caller_ratings" in breakdown["components"]


class TestSelectionPolicies:
    """Test selection policy implementations."""

    def test_cheapest_policy(self):
        """Test cheapest policy selects lowest cost."""
        policy = CheapestPolicy()

        quotes = [
            Quote("q1", "agent1", "op", 0.10, 5.0, 0, "available", "2026-01-01"),
            Quote("q2", "agent2", "op", 0.05, 5.0, 0, "available", "2026-01-01"),
            Quote("q3", "agent3", "op", 0.08, 5.0, 0, "available", "2026-01-01"),
        ]

        selected = policy.select(quotes)
        assert selected.agent_pid == "agent2"
        assert selected.estimated_cost == 0.05

    def test_fastest_policy(self):
        """Test fastest policy selects lowest wait time."""
        policy = FastestPolicy()

        quotes = [
            Quote("q1", "agent1", "op", 0.05, 10.0, 2, "busy", "2026-01-01"),
            Quote("q2", "agent2", "op", 0.05, 3.0, 0, "available", "2026-01-01"),
            Quote("q3", "agent3", "op", 0.05, 5.0, 1, "busy", "2026-01-01"),
        ]

        selected = policy.select(quotes)
        assert selected.agent_pid == "agent2"  # No queue + shortest duration

    def test_balanced_policy(self):
        """Test balanced policy weighs multiple factors."""
        policy = BalancedPolicy()

        quotes = [
            Quote("q1", "agent1", "op", 0.20, 10.0, 5, "overloaded", "2026-01-01"),
            Quote("q2", "agent2", "op", 0.10, 5.0, 1, "busy", "2026-01-01"),
            Quote("q3", "agent3", "op", 0.15, 3.0, 0, "available", "2026-01-01"),
        ]

        reputations = {
            "agent1": 0.95,
            "agent2": 0.88,
            "agent3": 0.82
        }

        selected = policy.select(quotes, reputations)
        # Should balance cost, speed, and reputation
        assert selected is not None


class TestNegotiation:
    """Test negotiation protocol."""

    def test_flexible_strategy_accepts_reasonable_offers(self):
        """Test flexible strategy accepts good offers when idle."""
        strategy = FlexibleStrategy(base_price=0.10, minimum_price=0.07)

        # Idle agent (low load) should accept lower price
        result = strategy.evaluate_offer(
            offered_price=0.08,
            current_load=0.2,
            caller_reputation=0.90,
            reason="budget_constraint"
        )

        assert result.accepted
        assert result.final_cost == 0.08

    def test_flexible_strategy_rejects_too_low(self):
        """Test flexible strategy rejects unreasonably low offers."""
        strategy = FlexibleStrategy(base_price=0.10, minimum_price=0.07)

        result = strategy.evaluate_offer(
            offered_price=0.03,
            current_load=0.5,
            caller_reputation=0.80,
            reason="budget_constraint"
        )

        assert not result.accepted
        assert result.counter_offer is not None
        assert result.counter_offer >= 0.07


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
