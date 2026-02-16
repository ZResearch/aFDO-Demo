"""Reputation Management System for aFDO Marketplace.

This module implements a dual-path reputation system that combines:
1. Objective metrics (success rate, response time accuracy, uptime)
2. Subjective ratings (caller satisfaction scores)

Reputation score formula:
- 40% Success rate
- 20% Response time accuracy
- 30% Caller ratings (1-5 stars)
- 10% Uptime
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque


@dataclass
class OperationRecord:
    """Record of a single operation for reputation tracking."""

    operation_id: str
    operation_name: str
    success: bool
    estimated_duration: float
    actual_duration: float
    estimated_cost: float
    actual_cost: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def get_duration_accuracy(self) -> float:
        """Calculate duration accuracy (1.0 = perfect estimate)."""
        if self.estimated_duration == 0:
            return 1.0 if self.actual_duration == 0 else 0.0

        ratio = self.actual_duration / self.estimated_duration
        # Penalize both over and under estimates
        # Perfect = 1.0, 2x off = 0.5, 4x off = 0.25
        if ratio > 1.0:
            return 1.0 / ratio
        else:
            return ratio

    def get_cost_accuracy(self) -> float:
        """Calculate cost accuracy (1.0 = perfect estimate)."""
        if self.estimated_cost == 0:
            return 1.0 if self.actual_cost == 0 else 0.0

        ratio = self.actual_cost / self.estimated_cost
        if ratio > 1.0:
            return 1.0 / ratio
        else:
            return ratio


@dataclass
class CallerRating:
    """Rating submitted by a caller."""

    caller_pid: str
    overall: float  # 1.0-5.0
    speed: Optional[float] = None  # 1.0-5.0
    quality: Optional[float] = None  # 1.0-5.0
    value: Optional[float] = None  # 1.0-5.0
    reliability: Optional[float] = None  # 1.0-5.0
    comment: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def get_average(self) -> float:
        """Get average of all rating components."""
        ratings = [self.overall]
        if self.speed is not None:
            ratings.append(self.speed)
        if self.quality is not None:
            ratings.append(self.quality)
        if self.value is not None:
            ratings.append(self.value)
        if self.reliability is not None:
            ratings.append(self.reliability)

        return sum(ratings) / len(ratings) if ratings else 0.0


@dataclass
class ReputationMetrics:
    """Aggregate reputation metrics."""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_duration_accuracy: float = 1.0
    avg_cost_accuracy: float = 1.0
    caller_ratings: List[float] = field(default_factory=list)
    uptime_percentage: float = 1.0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_operations == 0:
            return 1.0
        return self.successful_operations / self.total_operations

    def get_average_rating(self) -> float:
        """Calculate average caller rating (0.0-1.0 scale)."""
        if not self.caller_ratings:
            return 0.8  # Default rating

        # Convert from 1-5 scale to 0-1 scale
        avg_5_scale = sum(self.caller_ratings) / len(self.caller_ratings)
        return (avg_5_scale - 1.0) / 4.0  # 1->0.0, 3->0.5, 5->1.0


class ReputationManager:
    """
    Manages dual-path reputation system for an agent.

    Tracks both objective metrics (success rate, accuracy) and
    subjective ratings (caller feedback).

    Reputation Score Formula:
        score = (success_rate * 0.4) +
                (duration_accuracy * 0.2) +
                (average_rating * 0.3) +
                (uptime * 0.1)

    All components scaled to 0.0-1.0 range.
    """

    def __init__(
        self,
        agent_pid: str,
        max_history: int = 100,
        max_ratings: int = 50
    ):
        """
        Initialize reputation manager.

        Args:
            agent_pid: PID of the agent being tracked
            max_history: Maximum number of operation records to keep
            max_ratings: Maximum number of caller ratings to keep
        """
        self.agent_pid = agent_pid
        self.max_history = max_history
        self.max_ratings = max_ratings

        # Operation history (recent operations weighted more)
        self.operation_history: deque = deque(maxlen=max_history)

        # Caller ratings
        self.caller_ratings: deque = deque(maxlen=max_ratings)

        # Aggregate metrics
        self.metrics = ReputationMetrics()

        # Uptime tracking
        self.start_time = time.time()
        self.total_downtime = 0.0  # seconds
        self.last_online_check = time.time()

    def record_operation(
        self,
        operation_id: str,
        operation_name: str,
        success: bool,
        estimated_duration: float,
        actual_duration: float,
        estimated_cost: float,
        actual_cost: float
    ):
        """
        Record an operation for reputation tracking.

        Args:
            operation_id: Unique operation identifier
            operation_name: Name of operation
            success: Whether operation succeeded
            estimated_duration: Estimated duration in seconds
            actual_duration: Actual duration in seconds
            estimated_cost: Estimated cost
            actual_cost: Actual cost
        """
        record = OperationRecord(
            operation_id=operation_id,
            operation_name=operation_name,
            success=success,
            estimated_duration=estimated_duration,
            actual_duration=actual_duration,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost
        )

        self.operation_history.append(record)
        self._update_metrics()

    def record_caller_rating(
        self,
        caller_pid: str,
        overall: float,
        speed: Optional[float] = None,
        quality: Optional[float] = None,
        value: Optional[float] = None,
        reliability: Optional[float] = None,
        comment: Optional[str] = None
    ):
        """
        Record a caller rating.

        Args:
            caller_pid: PID of caller submitting rating
            overall: Overall satisfaction (1.0-5.0)
            speed: Speed rating (1.0-5.0)
            quality: Quality rating (1.0-5.0)
            value: Value rating (1.0-5.0)
            reliability: Reliability rating (1.0-5.0)
            comment: Optional text comment
        """
        rating = CallerRating(
            caller_pid=caller_pid,
            overall=overall,
            speed=speed,
            quality=quality,
            value=value,
            reliability=reliability,
            comment=comment
        )

        self.caller_ratings.append(rating)
        self._update_metrics()

    def _update_metrics(self):
        """Update aggregate metrics from operation history and ratings."""
        # Calculate from operation history
        if self.operation_history:
            self.metrics.total_operations = len(self.operation_history)
            self.metrics.successful_operations = sum(
                1 for op in self.operation_history if op.success
            )
            self.metrics.failed_operations = (
                self.metrics.total_operations - self.metrics.successful_operations
            )

            # Calculate average duration accuracy
            duration_accuracies = [op.get_duration_accuracy() for op in self.operation_history]
            self.metrics.avg_duration_accuracy = (
                sum(duration_accuracies) / len(duration_accuracies)
                if duration_accuracies else 1.0
            )

            # Calculate average cost accuracy
            cost_accuracies = [op.get_cost_accuracy() for op in self.operation_history]
            self.metrics.avg_cost_accuracy = (
                sum(cost_accuracies) / len(cost_accuracies)
                if cost_accuracies else 1.0
            )

        # Update caller ratings list
        if self.caller_ratings:
            self.metrics.caller_ratings = [
                rating.get_average() for rating in self.caller_ratings
            ]

        # Update uptime
        self.metrics.uptime_percentage = self._calculate_uptime()
        self.metrics.last_updated = datetime.utcnow().isoformat()

    def _calculate_uptime(self) -> float:
        """Calculate uptime percentage."""
        total_time = time.time() - self.start_time
        if total_time == 0:
            return 1.0

        uptime = total_time - self.total_downtime
        return max(0.0, min(1.0, uptime / total_time))

    def record_downtime(self, duration: float):
        """
        Record downtime period.

        Args:
            duration: Downtime duration in seconds
        """
        self.total_downtime += duration
        self._update_metrics()

    def calculate_score(self) -> float:
        """
        Calculate overall reputation score (0.0-1.0).

        Formula:
            score = (success_rate * 0.4) +
                    (duration_accuracy * 0.2) +
                    (average_rating * 0.3) +
                    (uptime * 0.1)

        Returns:
            Reputation score from 0.0 to 1.0
        """
        success_rate = self.metrics.get_success_rate()
        duration_accuracy = self.metrics.avg_duration_accuracy
        average_rating = self.metrics.get_average_rating()
        uptime = self.metrics.uptime_percentage

        score = (
            (success_rate * 0.4) +
            (duration_accuracy * 0.2) +
            (average_rating * 0.3) +
            (uptime * 0.1)
        )

        return max(0.0, min(1.0, score))

    def get_reputation_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed reputation breakdown.

        Returns:
            Dictionary with all reputation components
        """
        score = self.calculate_score()
        success_rate = self.metrics.get_success_rate()
        average_rating = self.metrics.get_average_rating()

        # Calculate component contributions
        contributions = {
            "success_rate": {
                "value": success_rate,
                "weight": 0.4,
                "contribution": success_rate * 0.4
            },
            "duration_accuracy": {
                "value": self.metrics.avg_duration_accuracy,
                "weight": 0.2,
                "contribution": self.metrics.avg_duration_accuracy * 0.2
            },
            "caller_ratings": {
                "value": average_rating,
                "weight": 0.3,
                "contribution": average_rating * 0.3
            },
            "uptime": {
                "value": self.metrics.uptime_percentage,
                "weight": 0.1,
                "contribution": self.metrics.uptime_percentage * 0.1
            }
        }

        return {
            "agent_pid": self.agent_pid,
            "overall_score": score,
            "grade": self._get_grade(score),
            "components": contributions,
            "statistics": {
                "total_operations": self.metrics.total_operations,
                "successful_operations": self.metrics.successful_operations,
                "failed_operations": self.metrics.failed_operations,
                "success_rate": success_rate,
                "avg_duration_accuracy": self.metrics.avg_duration_accuracy,
                "avg_cost_accuracy": self.metrics.avg_cost_accuracy,
                "total_ratings": len(self.caller_ratings),
                "average_rating_5_scale": self._get_average_rating_5_scale(),
                "uptime_percentage": self.metrics.uptime_percentage * 100
            },
            "recent_operations": len(self.operation_history),
            "recent_ratings": len(self.caller_ratings),
            "last_updated": self.metrics.last_updated
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "A-"
        elif score >= 0.80:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.70:
            return "B-"
        elif score >= 0.65:
            return "C+"
        elif score >= 0.60:
            return "C"
        elif score >= 0.50:
            return "C-"
        else:
            return "F"

    def _get_average_rating_5_scale(self) -> float:
        """Get average caller rating on 1-5 scale."""
        if not self.caller_ratings:
            return 4.0  # Default

        return sum(r.get_average() for r in self.caller_ratings) / len(self.caller_ratings)

    def get_trend(self, window_size: int = 10) -> str:
        """
        Calculate reputation trend (improving, declining, stable).

        Args:
            window_size: Number of recent operations to analyze

        Returns:
            "improving", "declining", or "stable"
        """
        if len(self.operation_history) < window_size * 2:
            return "stable"

        # Split into recent and older
        recent = list(self.operation_history)[-window_size:]
        older = list(self.operation_history)[-window_size*2:-window_size]

        recent_success = sum(1 for op in recent if op.success) / len(recent)
        older_success = sum(1 for op in older if op.success) / len(older)

        diff = recent_success - older_success

        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"

    def __repr__(self) -> str:
        """String representation."""
        score = self.calculate_score()
        grade = self._get_grade(score)
        return f"ReputationManager(score={score:.3f}, grade={grade}, operations={self.metrics.total_operations})"
