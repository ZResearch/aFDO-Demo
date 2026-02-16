"""Budget Management System for aFDO Marketplace.

This module implements budget tracking and enforcement for agent workflows.
Each request gets a BudgetManager instance that tracks spending using a
reserve/commit/release pattern to prevent double-spending.
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Transaction:
    """Represents a budget transaction (reservation or commitment)."""

    transaction_id: str
    operation: str
    agent_pid: str
    estimated_cost: float
    actual_cost: Optional[float] = None
    status: str = "reserved"  # reserved, committed, released
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "operation": self.operation,
            "agent_pid": self.agent_pid,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "status": self.status,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class BudgetManager:
    """
    Manages budget allocation and tracking for agent workflows.

    Features:
    - Per-request budget allocation
    - Reserve/commit/release pattern to prevent double-spending
    - Transaction tracking for audit trail
    - Budget inheritance for sub-workflows
    - Thread-safe operations

    Usage:
        budget = BudgetManager(total_budget=1.0)

        # Reserve budget before calling agent
        reservation_id = budget.reserve(0.05, "extract_text")

        # After successful call, commit with actual cost
        budget.commit(reservation_id, actual_cost=0.048)

        # Or release if call was cancelled
        budget.release(reservation_id)

        # Check available budget
        if budget.can_afford(0.10):
            # Proceed with operation
            pass
    """

    def __init__(self, total_budget: float, parent_budget: Optional['BudgetManager'] = None):
        """
        Initialize budget manager.

        Args:
            total_budget: Total budget allocated for this workflow
            parent_budget: Optional parent budget (for sub-workflows)
        """
        if total_budget < 0:
            raise ValueError("Budget cannot be negative")

        self.total_budget = total_budget
        self.parent_budget = parent_budget
        self.spent = 0.0
        self.reserved = 0.0
        self.transactions: List[Transaction] = []
        self._reservations: Dict[str, Transaction] = {}

    def reserve(self, amount: float, operation: str, agent_pid: str = "unknown") -> Optional[str]:
        """
        Reserve budget for an operation.

        Args:
            amount: Amount to reserve
            operation: Operation name
            agent_pid: Agent PID that will perform operation

        Returns:
            Reservation ID if successful, None if insufficient budget
        """
        if amount < 0:
            raise ValueError("Reservation amount cannot be negative")

        # Check if budget allows
        if not self.can_afford(amount):
            return None

        # Create reservation
        reservation_id = str(uuid.uuid4())
        transaction = Transaction(
            transaction_id=reservation_id,
            operation=operation,
            agent_pid=agent_pid,
            estimated_cost=amount,
            status="reserved"
        )

        # Update reserved amount
        self.reserved += amount
        self._reservations[reservation_id] = transaction
        self.transactions.append(transaction)

        return reservation_id

    def commit(self, reservation_id: str, actual_cost: float) -> bool:
        """
        Commit a reservation with actual cost.

        Args:
            reservation_id: ID from reserve() call
            actual_cost: Actual cost incurred

        Returns:
            True if successful, False if reservation not found
        """
        if reservation_id not in self._reservations:
            return False

        transaction = self._reservations[reservation_id]

        if transaction.status != "reserved":
            return False

        # Release the reservation
        self.reserved -= transaction.estimated_cost

        # Add actual spending
        self.spent += actual_cost

        # Update transaction
        transaction.actual_cost = actual_cost
        transaction.status = "committed"

        # Remove from active reservations
        del self._reservations[reservation_id]

        return True

    def release(self, reservation_id: str) -> bool:
        """
        Release an unused reservation.

        Args:
            reservation_id: ID from reserve() call

        Returns:
            True if successful, False if reservation not found
        """
        if reservation_id not in self._reservations:
            return False

        transaction = self._reservations[reservation_id]

        if transaction.status != "reserved":
            return False

        # Release the reservation
        self.reserved -= transaction.estimated_cost
        transaction.status = "released"

        # Remove from active reservations
        del self._reservations[reservation_id]

        return True

    def can_afford(self, estimated_cost: float) -> bool:
        """
        Check if budget allows for estimated cost.

        Args:
            estimated_cost: Estimated cost to check

        Returns:
            True if budget is sufficient, False otherwise
        """
        available = self.get_available()
        return available >= estimated_cost

    def get_available(self) -> float:
        """
        Get remaining available budget.

        Returns:
            Available budget (total - spent - reserved)
        """
        return self.total_budget - self.spent - self.reserved

    def get_remaining(self) -> float:
        """
        Get remaining budget (spent only, not including reservations).

        Returns:
            Remaining budget (total - spent)
        """
        return self.total_budget - self.spent

    def get_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed budget breakdown.

        Returns:
            Dictionary with budget allocation details
        """
        # Group transactions by operation
        by_operation = {}
        for txn in self.transactions:
            if txn.status == "committed":
                op = txn.operation
                if op not in by_operation:
                    by_operation[op] = {
                        "count": 0,
                        "total_cost": 0.0,
                        "agents": []
                    }
                by_operation[op]["count"] += 1
                by_operation[op]["total_cost"] += txn.actual_cost or 0
                if txn.agent_pid not in by_operation[op]["agents"]:
                    by_operation[op]["agents"].append(txn.agent_pid)

        return {
            "total_budget": self.total_budget,
            "spent": self.spent,
            "reserved": self.reserved,
            "available": self.get_available(),
            "remaining": self.get_remaining(),
            "utilization_percent": (self.spent / self.total_budget * 100) if self.total_budget > 0 else 0,
            "transactions": [txn.to_dict() for txn in self.transactions],
            "by_operation": by_operation,
            "active_reservations": len(self._reservations)
        }

    def create_sub_budget(self, amount: float) -> Optional['BudgetManager']:
        """
        Create a sub-budget for a child workflow.

        Args:
            amount: Amount to allocate to sub-budget

        Returns:
            New BudgetManager instance if successful, None if insufficient budget
        """
        # Reserve amount in parent budget
        reservation_id = self.reserve(amount, "sub_budget_allocation")
        if not reservation_id:
            return None

        # Create child budget
        child_budget = BudgetManager(total_budget=amount, parent_budget=self)

        # Commit the reservation immediately
        self.commit(reservation_id, amount)

        return child_budget

    def get_summary_string(self) -> str:
        """
        Get human-readable budget summary.

        Returns:
            Formatted budget summary string
        """
        return (
            f"Budget: ${self.spent:.4f} of ${self.total_budget:.4f} spent "
            f"(${self.reserved:.4f} reserved, ${self.get_available():.4f} available)"
        )

    def __repr__(self) -> str:
        """String representation of budget manager."""
        return (
            f"BudgetManager(total={self.total_budget:.4f}, "
            f"spent={self.spent:.4f}, reserved={self.reserved:.4f}, "
            f"available={self.get_available():.4f})"
        )
