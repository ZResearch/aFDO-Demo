"""
Protocol implementations for aFDO system.

This package contains protocol schemas and implementations for:
- Cost negotiation with recursive estimation
- Workflow execution engine
"""

from .negotiation import (
    NegotiationProtocol,
    NegotiationSession,
    NegotiationState,
    CostEstimate,
    ApprovalDecision,
    ExecutionResult,
    CostEscalationRequest,
    EscalationDecision,
    CostBreakdownItem
)

from .workflow_engine import (
    WorkflowEngine,
    WorkflowExecutionError,
    StepResult,
    ExecutionContext
)

__all__ = [
    # Negotiation Protocol
    "NegotiationProtocol",
    "NegotiationSession",
    "NegotiationState",
    "CostEstimate",
    "ApprovalDecision",
    "ExecutionResult",
    "CostEscalationRequest",
    "EscalationDecision",
    "CostBreakdownItem",
    # Workflow Engine
    "WorkflowEngine",
    "WorkflowExecutionError",
    "StepResult",
    "ExecutionContext"
]
