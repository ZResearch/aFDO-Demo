"""Job tracking for monitoring agent workflows and call chains."""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class CallEvent:
    """Represents a single agent-to-agent call."""
    timestamp: float
    caller_pid: str
    target_pid: str
    operation: str
    status: str  # "initiated", "success", "failed"
    duration: Optional[float] = None
    cost: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Job:
    """Represents a complete workflow/job with multiple calls."""
    job_id: str
    initiator_pid: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "in_progress"  # "in_progress", "completed", "failed"
    calls: List[CallEvent] = field(default_factory=list)
    total_cost: float = 0.0

    def add_call(self, call: CallEvent):
        """Add a call event to this job."""
        self.calls.append(call)
        if call.cost:
            self.total_cost += call.cost

    def complete(self, status: str = "completed"):
        """Mark job as complete."""
        self.end_time = time.time()
        self.status = status

    @property
    def duration(self) -> float:
        """Get job duration in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "initiator_pid": self.initiator_pid,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "duration": self.duration,
            "total_cost": self.total_cost,
            "call_count": len(self.calls),
            "calls": [
                call.to_dict()
                for call in self.calls
            ]
        }


class JobTracker:
    """Global job tracker for monitoring workflows."""

    def __init__(self):
        self.active_jobs: Dict[str, Job] = {}
        self.completed_jobs: List[Job] = []
        self.max_completed = 100  # Keep last 100 jobs

    def start_job(self, initiator_pid: str) -> str:
        """Start a new job, return job_id."""
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            job_id=job_id,
            initiator_pid=initiator_pid,
            start_time=time.time()
        )
        self.active_jobs[job_id] = job
        return job_id

    def add_call(
        self,
        job_id: str,
        caller_pid: str,
        target_pid: str,
        operation: str,
        status: str = "initiated",
        duration: Optional[float] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Add a call event to a job."""
        if job_id not in self.active_jobs:
            # Job not tracked, start it
            job_id = self.start_job(caller_pid)

        event = CallEvent(
            timestamp=time.time(),
            caller_pid=caller_pid,
            target_pid=target_pid,
            operation=operation,
            status=status,
            duration=duration,
            cost=cost,
            error=error
        )

        self.active_jobs[job_id].add_call(event)

    def complete_job(self, job_id: str, status: str = "completed"):
        """Mark job as complete and move to history."""
        if job_id in self.active_jobs:
            job = self.active_jobs.pop(job_id)
            job.complete(status)
            self.completed_jobs.append(job)

            # Keep only last N jobs
            if len(self.completed_jobs) > self.max_completed:
                self.completed_jobs = self.completed_jobs[-self.max_completed:]

    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs."""
        return [job.to_dict() for job in self.active_jobs.values()]

    def get_completed_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent completed jobs."""
        return [job.to_dict() for job in self.completed_jobs[-limit:]]

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get specific job by ID."""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()

        for job in reversed(self.completed_jobs):
            if job.job_id == job_id:
                return job.to_dict()

        return None


# Global job tracker instance
_job_tracker = None


def get_job_tracker() -> JobTracker:
    """Get the global job tracker instance."""
    global _job_tracker
    if _job_tracker is None:
        _job_tracker = JobTracker()
    return _job_tracker
