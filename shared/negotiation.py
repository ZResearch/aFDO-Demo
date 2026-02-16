"""Negotiation Protocol for aFDO Marketplace.

This module defines the data models and protocols for price negotiation
between agents in the marketplace.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class QuoteRequest:
    """
    Request for a price quote from an agent.

    Used by callers to request pricing information before committing
    to an operation.
    """

    operation: str
    parameters: Dict[str, Any]
    max_budget: float
    priority: str = "normal"  # low, normal, high, urgent
    deadline: Optional[str] = None  # ISO 8601 timestamp
    caller_pid: Optional[str] = None
    quantity: int = 1  # Number of operations (for bulk pricing)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "parameters": self.parameters,
            "max_budget": self.max_budget,
            "priority": self.priority,
            "deadline": self.deadline,
            "caller_pid": self.caller_pid,
            "quantity": self.quantity,
            "metadata": self.metadata
        }


@dataclass
class Quote:
    """
    Price quote from an agent.

    Represents an agent's offer to perform an operation at a specific
    price with specified terms.
    """

    quote_id: str
    agent_pid: str
    operation: str
    estimated_cost: float
    estimated_duration: float  # seconds
    queue_position: int
    availability_status: str  # available, busy, overloaded
    expires_at: str  # ISO 8601 timestamp
    terms: Dict[str, Any] = field(default_factory=dict)
    negotiable: bool = True
    minimum_price: Optional[float] = None
    bulk_discount: Optional[Dict[str, float]] = None  # quantity -> discount%
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def is_expired(self) -> bool:
        """Check if quote has expired."""
        try:
            expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() > expires
        except:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "quote_id": self.quote_id,
            "agent_pid": self.agent_pid,
            "operation": self.operation,
            "estimated_cost": self.estimated_cost,
            "estimated_duration": self.estimated_duration,
            "queue_position": self.queue_position,
            "availability_status": self.availability_status,
            "expires_at": self.expires_at,
            "terms": self.terms,
            "negotiable": self.negotiable,
            "minimum_price": self.minimum_price,
            "bulk_discount": self.bulk_discount,
            "timestamp": self.timestamp
        }


@dataclass
class NegotiationRequest:
    """
    Request to negotiate a better price.

    Sent by caller to agent to request a price lower than the initial quote.
    """

    quote_id: str
    offered_price: float
    reason: str  # budget_constraint, bulk_discount, repeat_customer, competitive_bid
    caller_pid: str
    caller_reputation: Optional[float] = None
    justification: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "quote_id": self.quote_id,
            "offered_price": self.offered_price,
            "reason": self.reason,
            "caller_pid": self.caller_pid,
            "caller_reputation": self.caller_reputation,
            "justification": self.justification,
            "metadata": self.metadata
        }


@dataclass
class NegotiationResult:
    """
    Result of a negotiation attempt.

    Represents the agent's response to a negotiation request.
    """

    accepted: bool
    final_cost: float
    reason: Optional[str] = None
    alternative_quote: Optional[Quote] = None
    counter_offer: Optional[float] = None
    terms: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "accepted": self.accepted,
            "final_cost": self.final_cost,
            "reason": self.reason,
            "alternative_quote": self.alternative_quote.to_dict() if self.alternative_quote else None,
            "counter_offer": self.counter_offer,
            "terms": self.terms,
            "message": self.message,
            "timestamp": self.timestamp
        }


class NegotiationStrategy:
    """
    Base class for negotiation strategies.

    Defines how an agent responds to negotiation requests.
    """

    def __init__(self, base_price: float, minimum_price: float):
        """
        Initialize negotiation strategy.

        Args:
            base_price: Normal price for service
            minimum_price: Absolute minimum acceptable price
        """
        self.base_price = base_price
        self.minimum_price = minimum_price

    def evaluate_offer(
        self,
        offered_price: float,
        current_load: float,
        caller_reputation: Optional[float],
        reason: str
    ) -> NegotiationResult:
        """
        Evaluate a negotiation offer.

        Args:
            offered_price: Price offered by caller
            current_load: Current agent load (0.0-1.0)
            caller_reputation: Caller's reputation score
            reason: Reason for negotiation

        Returns:
            NegotiationResult with decision
        """
        # Default implementation - override in subclasses
        if offered_price >= self.base_price:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Offer accepted at full price"
            )
        elif offered_price >= self.minimum_price:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Offer accepted at negotiated price"
            )
        else:
            return NegotiationResult(
                accepted=False,
                final_cost=0.0,
                reason="price_too_low",
                counter_offer=self.minimum_price,
                message=f"Offer too low. Minimum price is ${self.minimum_price:.4f}"
            )


class FlexibleStrategy(NegotiationStrategy):
    """Flexible negotiation - accepts lower prices when idle."""

    def evaluate_offer(
        self,
        offered_price: float,
        current_load: float,
        caller_reputation: Optional[float],
        reason: str
    ) -> NegotiationResult:
        # More willing to negotiate when idle
        if current_load < 0.3:  # Idle
            effective_minimum = self.minimum_price * 0.8
        elif current_load < 0.6:  # Moderate load
            effective_minimum = self.minimum_price * 0.9
        else:  # Busy
            effective_minimum = self.minimum_price

        # Good reputation callers get better deals
        if caller_reputation and caller_reputation > 0.9:
            effective_minimum *= 0.95

        if offered_price >= self.base_price:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Offer accepted at full price"
            )
        elif offered_price >= effective_minimum:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message=f"Offer accepted (flexible pricing due to {reason})"
            )
        else:
            return NegotiationResult(
                accepted=False,
                final_cost=0.0,
                reason="price_too_low",
                counter_offer=effective_minimum,
                message=f"Counter-offer: ${effective_minimum:.4f}"
            )


class FirmStrategy(NegotiationStrategy):
    """Firm negotiation - rarely accepts lower prices."""

    def evaluate_offer(
        self,
        offered_price: float,
        current_load: float,
        caller_reputation: Optional[float],
        reason: str
    ) -> NegotiationResult:
        # Only negotiate if offered price is very close to base
        discount_threshold = self.base_price * 0.95

        if offered_price >= self.base_price:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Offer accepted"
            )
        elif offered_price >= discount_threshold and current_load < 0.3:
            # Only accept small discounts when idle
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Small discount approved due to low demand"
            )
        else:
            return NegotiationResult(
                accepted=False,
                final_cost=0.0,
                reason="firm_pricing",
                counter_offer=self.base_price,
                message="Firm pricing policy - no discount available"
            )


class MarketDrivenStrategy(NegotiationStrategy):
    """Market-driven negotiation - adjusts based on competition."""

    def __init__(self, base_price: float, minimum_price: float, competitor_prices: List[float]):
        """
        Initialize market-driven strategy.

        Args:
            base_price: Normal price for service
            minimum_price: Absolute minimum acceptable price
            competitor_prices: List of competitor prices for comparison
        """
        super().__init__(base_price, minimum_price)
        self.competitor_prices = competitor_prices

    def evaluate_offer(
        self,
        offered_price: float,
        current_load: float,
        caller_reputation: Optional[float],
        reason: str
    ) -> NegotiationResult:
        # Calculate market position
        if self.competitor_prices:
            avg_competitor_price = sum(self.competitor_prices) / len(self.competitor_prices)
            min_competitor_price = min(self.competitor_prices)
        else:
            avg_competitor_price = self.base_price
            min_competitor_price = self.minimum_price

        # If we're more expensive than average, be more flexible
        if self.base_price > avg_competitor_price:
            effective_minimum = max(self.minimum_price, min_competitor_price * 0.95)
        else:
            effective_minimum = self.minimum_price

        if offered_price >= self.base_price:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Offer accepted"
            )
        elif offered_price >= effective_minimum:
            return NegotiationResult(
                accepted=True,
                final_cost=offered_price,
                message="Competitive pricing accepted"
            )
        else:
            return NegotiationResult(
                accepted=False,
                final_cost=0.0,
                reason="below_market_rate",
                counter_offer=effective_minimum,
                message=f"Below market rate. Counter-offer: ${effective_minimum:.4f}"
            )


def create_quote_expiry(minutes: int = 5) -> str:
    """
    Create ISO 8601 timestamp for quote expiry.

    Args:
        minutes: Minutes until expiry

    Returns:
        ISO 8601 formatted timestamp
    """
    expiry = datetime.utcnow() + timedelta(minutes=minutes)
    return expiry.isoformat() + 'Z'
