"""Queue Management System for aFDO Marketplace.

This module implements request queuing and dynamic pricing based on load.
Each agent maintains a queue of pending requests and adjusts pricing
based on current load.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class QueuedRequest:
    """Represents a request in the queue."""

    request_id: str
    caller_pid: str
    operation: str
    parameters: Dict[str, Any]
    priority: float = 1.0  # Higher = more important (budget-weighted)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    budget_reservation_id: Optional[str] = None
    estimated_duration: float = 5.0  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: 'QueuedRequest') -> bool:
        """Compare requests by priority for priority queue."""
        # Higher priority comes first
        return self.priority > other.priority


@dataclass
class QueueStatus:
    """Represents current queue status."""

    queue_length: int
    current_load: float  # 0.0-1.0
    estimated_wait_time: float  # seconds
    current_price: float
    base_price: float
    price_multiplier: float
    availability_status: str  # available, busy, overloaded, offline
    processing_request: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class QueueManager:
    """
    Manages request queues and dynamic pricing for agents.

    Features:
    - Priority-based request queue
    - Dynamic pricing based on queue length
    - Wait time estimation
    - Load tracking and reporting
    - Thread-safe operations

    Pricing Formula:
        current_price = base_cost * (1 + (queue_length / max_queue_size) * surge_factor)

    Usage:
        queue_mgr = QueueManager(base_cost=0.05, max_queue_size=10)

        # Get current price
        price = queue_mgr.get_current_price()

        # Add request to queue
        request = QueuedRequest(...)
        position = queue_mgr.add_request(request)

        # Get wait time estimate
        wait_time = queue_mgr.estimate_wait_time(position)

        # Mark request as processing
        await queue_mgr.start_processing(request_id)

        # Complete request
        await queue_mgr.complete_request(request_id, duration=3.2)
    """

    def __init__(
        self,
        base_cost: float,
        max_queue_size: int = 10,
        surge_factor: float = 2.0,
        avg_processing_time: float = 5.0
    ):
        """
        Initialize queue manager.

        Args:
            base_cost: Base cost when queue is empty
            max_queue_size: Maximum queue size before overload
            surge_factor: Price multiplier at max queue (default 2.0 = 3x price at full)
            avg_processing_time: Average time to process one request (seconds)
        """
        self.base_cost = base_cost
        self.max_queue_size = max_queue_size
        self.surge_factor = surge_factor
        self.avg_processing_time = avg_processing_time

        # Queue state
        self.queue: List[QueuedRequest] = []
        self.processing: Optional[QueuedRequest] = None
        self._lock = asyncio.Lock()

        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.processing_times: List[float] = []  # Last 100 times
        self.max_processing_history = 100

    def get_current_price(self) -> float:
        """
        Calculate current price based on queue length.

        Formula: base_cost * (1 + (queue_length / max_queue_size) * surge_factor)

        Returns:
            Current price
        """
        if self.max_queue_size == 0:
            return self.base_cost

        # Calculate load factor (0.0 to 1.0)
        load_factor = min(len(self.queue) / self.max_queue_size, 1.0)

        # Apply surge pricing
        price_multiplier = 1.0 + (load_factor * self.surge_factor)

        return self.base_cost * price_multiplier

    def get_price_multiplier(self) -> float:
        """
        Get current price multiplier.

        Returns:
            Price multiplier (1.0 = base price)
        """
        if self.max_queue_size == 0:
            return 1.0

        load_factor = min(len(self.queue) / self.max_queue_size, 1.0)
        return 1.0 + (load_factor * self.surge_factor)

    async def add_request(self, request: QueuedRequest) -> int:
        """
        Add request to queue.

        Args:
            request: QueuedRequest to add

        Returns:
            Queue position (0-indexed)
        """
        async with self._lock:
            # Add to queue (sorted by priority)
            self.queue.append(request)
            self.queue.sort(key=lambda r: r.priority, reverse=True)

            self.total_requests += 1

            # Find position
            position = next(
                (i for i, r in enumerate(self.queue) if r.request_id == request.request_id),
                len(self.queue) - 1
            )

            return position

    def estimate_wait_time(self, position: int = 0) -> float:
        """
        Estimate wait time for a position in queue.

        Args:
            position: Queue position (0 = next in line)

        Returns:
            Estimated wait time in seconds
        """
        if position < 0:
            return 0.0

        # Use average processing time
        avg_time = self._get_average_processing_time()

        # If something is currently processing, add remaining time estimate
        wait_time = 0.0
        if self.processing:
            wait_time += avg_time  # Assume full duration remaining

        # Add time for all requests ahead in queue
        wait_time += position * avg_time

        return wait_time

    def _get_average_processing_time(self) -> float:
        """
        Get average processing time from history.

        Returns:
            Average processing time in seconds
        """
        if not self.processing_times:
            return self.avg_processing_time

        return sum(self.processing_times) / len(self.processing_times)

    async def start_processing(self, request_id: str) -> bool:
        """
        Mark request as currently processing.

        Args:
            request_id: Request ID to process

        Returns:
            True if successful, False if request not in queue
        """
        async with self._lock:
            # Find request in queue
            request = next(
                (r for r in self.queue if r.request_id == request_id),
                None
            )

            if not request:
                return False

            # Remove from queue and mark as processing
            self.queue.remove(request)
            self.processing = request

            return True

    async def complete_request(self, request_id: str, duration: float, success: bool = True) -> bool:
        """
        Mark request as completed.

        Args:
            request_id: Request ID
            duration: Actual processing duration in seconds
            success: Whether request succeeded

        Returns:
            True if successful, False if request not found
        """
        async with self._lock:
            if not self.processing or self.processing.request_id != request_id:
                return False

            # Update statistics
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            # Track processing time
            self.processing_times.append(duration)
            if len(self.processing_times) > self.max_processing_history:
                self.processing_times.pop(0)

            # Clear processing
            self.processing = None

            return True

    def get_queue_status(self) -> QueueStatus:
        """
        Get current queue status.

        Returns:
            QueueStatus object with current state
        """
        queue_length = len(self.queue)
        current_load = min(queue_length / self.max_queue_size, 1.0) if self.max_queue_size > 0 else 0.0

        # Determine availability status
        if queue_length == 0 and not self.processing:
            availability_status = "available"
        elif queue_length < self.max_queue_size * 0.5:
            availability_status = "busy"
        elif queue_length < self.max_queue_size:
            availability_status = "overloaded"
        else:
            availability_status = "overloaded"

        return QueueStatus(
            queue_length=queue_length,
            current_load=current_load,
            estimated_wait_time=self.estimate_wait_time(queue_length),
            current_price=self.get_current_price(),
            base_price=self.base_cost,
            price_multiplier=self.get_price_multiplier(),
            availability_status=availability_status,
            processing_request=self.processing.request_id if self.processing else None
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        success_rate = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "avg_processing_time": self._get_average_processing_time(),
            "current_queue_length": len(self.queue),
            "current_load": self.get_queue_status().current_load
        }

    async def get_next_request(self) -> Optional[QueuedRequest]:
        """
        Get next request from queue (highest priority).

        Returns:
            Next QueuedRequest or None if queue is empty
        """
        async with self._lock:
            if not self.queue:
                return None

            # Queue is already sorted by priority
            return self.queue[0]

    def clear_queue(self):
        """Clear all pending requests from queue."""
        self.queue.clear()

    def __repr__(self) -> str:
        """String representation of queue manager."""
        status = self.get_queue_status()
        return (
            f"QueueManager(queue={status.queue_length}, "
            f"load={status.current_load:.2f}, "
            f"price=${status.current_price:.4f}, "
            f"status={status.availability_status})"
        )
