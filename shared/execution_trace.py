"""
Execution Trace Framework

Captures complete execution trace for transparency and debugging.

Every interaction between agents is logged with:
- Who called whom
- What operation was called
- What data was passed
- What was returned
- How long it took
- Any errors

This provides complete provenance for research and debugging.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import uuid
from pathlib import Path


@dataclass
class TraceEvent:
    """
    Single event in execution trace.

    Represents one step in the agent interaction flow.
    """

    # Event identification
    event_id: str
    step_number: int
    timestamp: str

    # Agent information
    agent_name: str
    agent_pid: str

    # Action information
    action_type: str  # "receive", "delegate", "execute", "return", "policy_evaluation", etc.
    operation: str

    # Data
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None

    # Metadata
    duration_ms: Optional[int] = None
    cost: Optional[float] = None
    error: Optional[str] = None

    # Delegation chain
    delegated_to: Optional[str] = None  # Target agent name
    delegated_to_pid: Optional[str] = None

    # Policy information
    policy_rule: Optional[str] = None
    policy_reasoning: Optional[str] = None

    # Additional notes
    notes: Optional[str] = None


class ExecutionTracer:
    """
    Tracks execution trace for a single request.

    Usage:
        tracer = ExecutionTracer(request_id="req_123", user_query="what is coffee")
        tracer.log_event(...)
        tracer.save_to_file()
    """

    def __init__(self, request_id: str = None, user_query: str = None, parent_request_id: str = None):
        self.request_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
        self.user_query = user_query
        self.parent_request_id = parent_request_id  # For nested traces
        self.start_time = datetime.utcnow()

        self.events: List[TraceEvent] = []
        self.step_counter = 0

        # Summary statistics
        self.total_cost = 0.0
        self.agents_involved = set()
        self.operations_called = {}

    def log_event(
        self,
        agent_name: str,
        agent_pid: str,
        action_type: str,
        operation: str,
        input_data: Dict[str, Any] = None,
        output_data: Dict[str, Any] = None,
        duration_ms: int = None,
        cost: float = None,
        error: str = None,
        delegated_to: str = None,
        delegated_to_pid: str = None,
        policy_rule: str = None,
        policy_reasoning: str = None,
        notes: str = None
    ) -> TraceEvent:
        """
        Log a single event in the execution trace.

        Args:
            agent_name: Name of agent performing action
            agent_pid: PID of agent
            action_type: Type of action (receive, delegate, execute, return, etc.)
            operation: Operation being performed
            input_data: Input parameters
            output_data: Output/result
            duration_ms: How long it took
            cost: Cost of operation
            error: Error message if failed
            delegated_to: If delegating, target agent name
            delegated_to_pid: If delegating, target PID
            policy_rule: If policy decision, which rule matched
            policy_reasoning: If policy decision, why
            notes: Additional notes

        Returns:
            Created TraceEvent
        """

        self.step_counter += 1

        event = TraceEvent(
            event_id=f"{self.request_id}_step_{self.step_counter}",
            step_number=self.step_counter,
            timestamp=datetime.utcnow().isoformat(),
            agent_name=agent_name,
            agent_pid=agent_pid,
            action_type=action_type,
            operation=operation,
            input_data=input_data or {},
            output_data=output_data,
            duration_ms=duration_ms,
            cost=cost,
            error=error,
            delegated_to=delegated_to,
            delegated_to_pid=delegated_to_pid,
            policy_rule=policy_rule,
            policy_reasoning=policy_reasoning,
            notes=notes
        )

        self.events.append(event)

        # Update statistics
        self.agents_involved.add(agent_name)

        # If delegating, also add the delegated_to agent
        if delegated_to:
            self.agents_involved.add(delegated_to)

        if operation not in self.operations_called:
            self.operations_called[operation] = 0
        self.operations_called[operation] += 1

        if cost:
            self.total_cost += cost

        return event

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution trace.

        Returns:
            Summary statistics
        """

        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds() * 1000

        summary = {
            "request_id": self.request_id,
            "user_query": self.user_query,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_ms": int(duration),
            "total_steps": len(self.events),
            "agents_involved": sorted(list(self.agents_involved)),
            "operations_called": self.operations_called,
            "total_cost": round(self.total_cost, 4),
            "status": "error" if any(e.error for e in self.events) else "success"
        }

        # Include parent_request_id if this is a nested trace
        if self.parent_request_id:
            summary["parent_request_id"] = self.parent_request_id

        return summary

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trace to dictionary.

        Returns:
            Complete trace as dictionary
        """

        return {
            "summary": self.get_summary(),
            "events": [asdict(event) for event in self.events]
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert trace to JSON string.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """

        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, directory: str = "/tmp/afdo_traces") -> str:
        """
        Save trace to file.

        Args:
            directory: Directory to save trace files

        Returns:
            Path to saved file
        """

        Path(directory).mkdir(parents=True, exist_ok=True)

        filename = f"{self.request_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path(directory) / filename

        with open(filepath, 'w') as f:
            f.write(self.to_json())

        return str(filepath)

    def format_readable(self) -> str:
        """
        Format trace as human-readable text.

        Returns:
            Formatted trace
        """

        summary = self.get_summary()

        output = []
        output.append("="*80)
        output.append(f"EXECUTION TRACE: {self.request_id}")
        output.append("="*80)

        output.append(f"\nUser Query: {self.user_query}")
        output.append(f"Total Duration: {summary['total_duration_ms']}ms")
        output.append(f"Total Cost: ${summary['total_cost']:.4f}")
        output.append(f"Status: {summary['status']}")
        output.append(f"Agents Involved: {', '.join(summary['agents_involved'])}")

        output.append("\n" + "="*80)
        output.append("EXECUTION STEPS")
        output.append("="*80)

        for event in self.events:
            output.append(f"\n[Step {event.step_number}] {event.agent_name} - {event.action_type.upper()}")
            output.append(f"  Operation: {event.operation}")
            output.append(f"  Time: {event.timestamp}")

            if event.duration_ms:
                output.append(f"  Duration: {event.duration_ms}ms")

            if event.cost:
                output.append(f"  Cost: ${event.cost:.4f}")

            if event.policy_rule:
                output.append(f"  Policy Rule: {event.policy_rule}")
                output.append(f"  Policy Reasoning: {event.policy_reasoning}")

            if event.delegated_to:
                output.append(f"  Delegated To: {event.delegated_to} ({event.delegated_to_pid})")

            if event.input_data and event.action_type in ["receive", "delegate", "execute"]:
                input_str = str(event.input_data)[:200]
                output.append(f"  Input: {input_str}")

            if event.output_data and event.action_type in ["return"]:
                output_str = str(event.output_data)[:200]
                output.append(f"  Output: {output_str}")

            if event.error:
                output.append(f"  ERROR: {event.error}")

            if event.notes:
                output.append(f"  Notes: {event.notes}")

        output.append("\n" + "="*80)

        return "\n".join(output)
