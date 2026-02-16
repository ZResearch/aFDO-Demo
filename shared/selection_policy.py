"""Selection Policy System for aFDO Marketplace.

This module implements various policies for selecting service providers
from multiple available options based on different criteria (cost,
speed, reputation, or balanced).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


# Import Quote from negotiation module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from negotiation import Quote


@dataclass
class SelectionCriteria:
    """Criteria for agent selection."""

    max_cost: Optional[float] = None
    max_wait_time: Optional[float] = None
    min_reputation: Optional[float] = None
    required_availability: Optional[str] = None  # available, busy
    prefer_attributes: Dict[str, Any] = None

    def matches(self, quote: Quote, reputation: float) -> bool:
        """Check if quote matches criteria."""
        if self.max_cost and quote.estimated_cost > self.max_cost:
            return False

        if self.max_wait_time:
            total_wait = (quote.queue_position * 5.0) + quote.estimated_duration
            if total_wait > self.max_wait_time:
                return False

        if self.min_reputation and reputation < self.min_reputation:
            return False

        if self.required_availability:
            if quote.availability_status not in ["available", "busy"]:
                return False

        return True


class SelectionPolicy(ABC):
    """
    Abstract base class for service selection policies.

    Policies determine how to select the best agent from multiple
    available options.
    """

    @abstractmethod
    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """
        Select best quote from available options.

        Args:
            quotes: List of quotes to choose from
            reputations: Optional dict mapping agent_pid to reputation score
            criteria: Optional selection criteria to filter quotes

        Returns:
            Selected Quote or None if no suitable option
        """
        pass

    def _filter_quotes(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]],
        criteria: Optional[SelectionCriteria]
    ) -> List[Quote]:
        """Filter quotes based on criteria."""
        if not criteria:
            return quotes

        filtered = []
        for quote in quotes:
            reputation = reputations.get(quote.agent_pid, 0.85) if reputations else 0.85
            if criteria.matches(quote, reputation):
                filtered.append(quote)

        return filtered


class CheapestPolicy(SelectionPolicy):
    """
    Select the cheapest available option.

    Minimizes cost regardless of other factors.
    """

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select cheapest quote."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        # Return cheapest
        return min(candidates, key=lambda q: q.estimated_cost)


class FastestPolicy(SelectionPolicy):
    """
    Select the fastest available option.

    Minimizes total time (queue wait + execution).
    """

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select fastest quote."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        # Calculate total time (wait + execution)
        def total_time(quote: Quote) -> float:
            wait_time = quote.queue_position * 5.0  # Assume 5s per queued request
            return wait_time + quote.estimated_duration

        return min(candidates, key=total_time)


class BestReputationPolicy(SelectionPolicy):
    """
    Select the highest reputation option.

    Prioritizes quality and reliability over cost or speed.
    """

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select highest reputation quote."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        if not reputations:
            # No reputation data, fallback to cheapest
            return min(candidates, key=lambda q: q.estimated_cost)

        # Return highest reputation
        return max(
            candidates,
            key=lambda q: reputations.get(q.agent_pid, 0.85)
        )


class BalancedPolicy(SelectionPolicy):
    """
    Select based on balanced criteria.

    Weights:
    - 40% Cost (lower is better)
    - 30% Reputation (higher is better)
    - 30% Speed (faster is better)
    """

    def __init__(
        self,
        cost_weight: float = 0.4,
        reputation_weight: float = 0.3,
        speed_weight: float = 0.3
    ):
        """
        Initialize balanced policy.

        Args:
            cost_weight: Weight for cost factor (default 0.4)
            reputation_weight: Weight for reputation factor (default 0.3)
            speed_weight: Weight for speed factor (default 0.3)
        """
        total = cost_weight + reputation_weight + speed_weight
        self.cost_weight = cost_weight / total
        self.reputation_weight = reputation_weight / total
        self.speed_weight = speed_weight / total

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select best balanced quote."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Calculate scores
        scores = []

        # Extract values for normalization
        costs = [q.estimated_cost for q in candidates]
        max_cost = max(costs)
        min_cost = min(costs)
        cost_range = max_cost - min_cost if max_cost > min_cost else 1.0

        # Calculate times
        times = []
        for q in candidates:
            wait_time = q.queue_position * 5.0
            total_time = wait_time + q.estimated_duration
            times.append(total_time)

        max_time = max(times)
        min_time = min(times)
        time_range = max_time - min_time if max_time > min_time else 1.0

        # Get reputations
        reps = []
        for q in candidates:
            rep = reputations.get(q.agent_pid, 0.85) if reputations else 0.85
            reps.append(rep)

        max_rep = max(reps)
        min_rep = min(reps)
        rep_range = max_rep - min_rep if max_rep > min_rep else 1.0

        # Calculate normalized scores
        for i, quote in enumerate(candidates):
            # Cost score (lower is better, so invert)
            if cost_range > 0:
                cost_score = 1.0 - ((quote.estimated_cost - min_cost) / cost_range)
            else:
                cost_score = 1.0

            # Speed score (lower time is better, so invert)
            if time_range > 0:
                speed_score = 1.0 - ((times[i] - min_time) / time_range)
            else:
                speed_score = 1.0

            # Reputation score (higher is better)
            if rep_range > 0:
                rep_score = (reps[i] - min_rep) / rep_range
            else:
                rep_score = 1.0

            # Weighted total
            total_score = (
                (cost_score * self.cost_weight) +
                (rep_score * self.reputation_weight) +
                (speed_score * self.speed_weight)
            )

            scores.append((total_score, quote))

        # Return highest score
        return max(scores, key=lambda x: x[0])[1]


class CustomPolicy(SelectionPolicy):
    """
    Custom selection policy with user-defined scoring function.

    Allows for flexible, application-specific selection logic.
    """

    def __init__(self, scoring_function):
        """
        Initialize custom policy.

        Args:
            scoring_function: Function that takes (quote, reputation) and returns score
        """
        self.scoring_function = scoring_function

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select using custom scoring function."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        # Apply custom scoring
        scores = []
        for quote in candidates:
            reputation = reputations.get(quote.agent_pid, 0.85) if reputations else 0.85
            score = self.scoring_function(quote, reputation)
            scores.append((score, quote))

        # Return highest score
        return max(scores, key=lambda x: x[0])[1]


class ValuePolicy(SelectionPolicy):
    """
    Select based on value for money.

    Considers reputation per dollar spent.
    """

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select best value quote."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        if not reputations:
            # No reputation data, fallback to cheapest
            return min(candidates, key=lambda q: q.estimated_cost)

        # Calculate value score (reputation per dollar)
        def value_score(quote: Quote) -> float:
            reputation = reputations.get(quote.agent_pid, 0.85)
            cost = quote.estimated_cost if quote.estimated_cost > 0 else 0.01
            return reputation / cost

        return max(candidates, key=value_score)


class AvailabilityFirstPolicy(SelectionPolicy):
    """
    Select first available agent (shortest queue).

    Prioritizes immediate availability over other factors.
    """

    def select(
        self,
        quotes: List[Quote],
        reputations: Optional[Dict[str, float]] = None,
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Quote]:
        """Select most available quote."""
        # Filter by criteria
        candidates = self._filter_quotes(quotes, reputations, criteria)

        if not candidates:
            return None

        # Sort by availability status and queue position
        def availability_score(quote: Quote) -> tuple:
            # Available = 0, Busy = 1, Overloaded = 2
            status_priority = {
                "available": 0,
                "busy": 1,
                "overloaded": 2,
                "offline": 3
            }
            priority = status_priority.get(quote.availability_status, 2)
            return (priority, quote.queue_position)

        return min(candidates, key=availability_score)


def get_policy_by_name(name: str) -> SelectionPolicy:
    """
    Get policy instance by name.

    Args:
        name: Policy name (cheapest, fastest, best_reputation, balanced, value, availability)

    Returns:
        SelectionPolicy instance

    Raises:
        ValueError: If policy name not recognized
    """
    policies = {
        "cheapest": CheapestPolicy(),
        "fastest": FastestPolicy(),
        "best_reputation": BestReputationPolicy(),
        "balanced": BalancedPolicy(),
        "value": ValuePolicy(),
        "availability": AvailabilityFirstPolicy()
    }

    if name not in policies:
        raise ValueError(
            f"Unknown policy: {name}. "
            f"Available: {', '.join(policies.keys())}"
        )

    return policies[name]
