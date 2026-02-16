"""
Cost Negotiation Protocol Implementation

Enables recursive cost estimation and budget approval between aFDOs.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class NegotiationState(Enum):
    """States in negotiation state machine."""
    IDLE = "idle"
    ESTIMATING = "estimating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    ESCALATION_REQUESTED = "escalation_requested"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CostBreakdownItem:
    """Single item in cost breakdown."""
    component: str
    agent_pid: str
    cost: float
    description: str


@dataclass
class CostEstimate:
    """Cost estimate response."""
    message_id: str
    responder_pid: str
    estimated_cost: float
    estimated_time: float  # seconds
    confidence: float  # 0-1
    breakdown: List[Dict[str, Any]]
    alternatives: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovalDecision:
    """Approval or rejection of estimate."""
    message_id: str
    estimate_message_id: str
    approved: bool
    allocated_budget: float
    execution_id: Optional[str] = None
    reason: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    """Result of task execution."""
    message_id: str
    execution_id: str
    status: str  # success|failed|partial
    result: Any
    actual_cost: float
    breakdown: List[Dict[str, Any]]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CostEscalationRequest:
    """Request for additional budget."""
    message_id: str
    execution_id: str
    original_estimate: float
    new_estimate: float
    reason: str
    progress: Dict[str, Any]
    alternatives: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EscalationDecision:
    """Response to cost escalation."""
    message_id: str
    escalation_message_id: str
    approved: bool
    new_budget: Optional[float] = None
    action: str = "continue"  # continue|abort|revise
    revision_instructions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NegotiationSession:
    """
    Tracks state of a single negotiation session.

    Each negotiation has:
    - Unique session ID
    - Current state
    - Message history
    - Budget tracking
    """

    def __init__(self, session_id: str, caller_pid: str, callee_pid: str):
        self.session_id = session_id
        self.caller_pid = caller_pid
        self.callee_pid = callee_pid
        self.state = NegotiationState.IDLE
        self.messages = []
        self.estimate: Optional[CostEstimate] = None
        self.approval: Optional[ApprovalDecision] = None
        self.execution_id: Optional[str] = None
        self.result: Optional[ExecutionResult] = None
        self.created_at = time.time()
        self.updated_at = time.time()

    def add_message(self, message_type: str, message: Dict[str, Any]):
        """Add message to history."""
        self.messages.append({
            "timestamp": time.time(),
            "type": message_type,
            "message": message
        })
        self.updated_at = time.time()

    def transition_to(self, new_state: NegotiationState):
        """Transition to new state."""
        self.state = new_state
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "caller_pid": self.caller_pid,
            "callee_pid": self.callee_pid,
            "state": self.state.value,
            "estimate": self.estimate.to_dict() if self.estimate else None,
            "approval": self.approval.to_dict() if self.approval else None,
            "execution_id": self.execution_id,
            "result": self.result.to_dict() if self.result else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages)
        }


class NegotiationProtocol:
    """
    Cost Negotiation Protocol Implementation.

    Provides methods for:
    - Requesting estimates (with recursive sub-estimates)
    - Approving/rejecting estimates
    - Executing with budget tracking
    - Handling cost escalations
    """

    def __init__(self, agent):
        """
        Initialize protocol for an agent.

        Args:
            agent: The aFDOBase instance using this protocol
        """
        self.agent = agent
        self.logger = logging.getLogger(f"Negotiation[{agent.pid}]")

        # Active negotiation sessions
        self.active_sessions: Dict[str, NegotiationSession] = {}

        # Completed sessions (keep last 100)
        self.completed_sessions: List[NegotiationSession] = []
        self.max_completed = 100

    # ========================================================================
    # CLIENT SIDE (Requesting services from others)
    # ========================================================================

    async def request_estimate(
        self,
        target_pid: str,
        operation: str,
        parameters: Dict[str, Any],
        budget_limit: Optional[float] = None,
        quality_preference: str = "balanced"
    ) -> CostEstimate:
        """
        Request cost estimate from another aFDO.

        This is Phase 1 of negotiation protocol.

        Args:
            target_pid: PID of aFDO to request from
            operation: Operation to estimate
            parameters: Operation parameters
            budget_limit: Maximum budget (optional)
            quality_preference: speed|balanced|quality

        Returns:
            CostEstimate from target aFDO
        """
        # Create session
        session_id = str(uuid.uuid4())[:8]
        session = NegotiationSession(session_id, self.agent.pid, target_pid)
        self.active_sessions[session_id] = session

        # Create estimate request message
        message_id = str(uuid.uuid4())[:8]
        request = {
            "message_id": message_id,
            "caller_pid": self.agent.pid,
            "operation": operation,
            "parameters": parameters,
            "budget_limit": budget_limit,
            "quality_preference": quality_preference
        }

        session.add_message("estimate_request", request)
        session.transition_to(NegotiationState.ESTIMATING)

        self.logger.info(f"💰 Requesting estimate from {target_pid}")
        self.logger.info(f"   Session: {session_id}, Operation: {operation}")

        try:
            # Call target aFDO with special "estimate" mode
            response = await self.agent.call_other_afdo(
                target_pid=target_pid,
                operation=f"__estimate_{operation}",  # Special estimate operation
                data={
                    **request,
                    "negotiation_session_id": session_id
                }
            )

            # Parse estimate response
            estimate = CostEstimate(
                message_id=response.get("message_id", str(uuid.uuid4())[:8]),
                responder_pid=target_pid,
                estimated_cost=response["estimated_cost"],
                estimated_time=response["estimated_time"],
                confidence=response["confidence"],
                breakdown=response["breakdown"],
                alternatives=response.get("alternatives")
            )

            session.estimate = estimate
            session.add_message("estimate_response", estimate.to_dict())
            session.transition_to(NegotiationState.AWAITING_APPROVAL)

            self.logger.info(f"✅ Received estimate: ${estimate.estimated_cost:.3f}")
            self.logger.info(f"   Time: {estimate.estimated_time:.1f}s, Confidence: {estimate.confidence:.0%}")

            return estimate

        except Exception as e:
            self.logger.error(f"❌ Estimate request failed: {e}")
            session.transition_to(NegotiationState.FAILED)
            self._archive_session(session_id)
            raise

    async def approve_estimate(
        self,
        session_id: str,
        approved: bool,
        allocated_budget: Optional[float] = None,
        reason: Optional[str] = None
    ) -> str:
        """
        Approve or reject an estimate.

        This is Phase 2 of negotiation protocol.

        Args:
            session_id: Negotiation session ID
            approved: Whether to approve
            allocated_budget: Budget to allocate (if approved)
            reason: Reason for rejection (if rejected)

        Returns:
            execution_id (if approved)
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"No active session: {session_id}")

        if not session.estimate:
            raise ValueError(f"No estimate in session: {session_id}")

        # Create approval message
        message_id = str(uuid.uuid4())[:8]
        execution_id = str(uuid.uuid4())[:8] if approved else None

        approval = ApprovalDecision(
            message_id=message_id,
            estimate_message_id=session.estimate.message_id,
            approved=approved,
            allocated_budget=allocated_budget or session.estimate.estimated_cost,
            execution_id=execution_id,
            reason=reason
        )

        session.approval = approval
        session.execution_id = execution_id
        session.add_message("approval_decision", approval.to_dict())

        if approved:
            session.transition_to(NegotiationState.APPROVED)
            self.logger.info(f"✅ Approved estimate for session {session_id}")
            self.logger.info(f"   Execution ID: {execution_id}, Budget: ${allocated_budget:.3f}")
        else:
            session.transition_to(NegotiationState.CANCELLED)
            self.logger.info(f"❌ Rejected estimate for session {session_id}: {reason}")
            self._archive_session(session_id)

        # Send approval to callee
        try:
            await self.agent.call_other_afdo(
                target_pid=session.callee_pid,
                operation="__approval_decision",
                data=approval.to_dict()
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send approval to callee: {e}")

        return execution_id if approved else None

    async def execute_with_budget(
        self,
        session_id: str,
        operation: str,
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute approved task with budget.

        This is Phase 3 of negotiation protocol.

        Args:
            session_id: Negotiation session ID
            operation: Operation to execute
            parameters: Operation parameters

        Returns:
            ExecutionResult
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"No active session: {session_id}")

        if session.state != NegotiationState.APPROVED:
            raise ValueError(f"Session not approved: {session_id}")

        if not session.execution_id:
            raise ValueError(f"No execution ID: {session_id}")

        session.transition_to(NegotiationState.EXECUTING)

        self.logger.info(f"🚀 Executing session {session_id}")

        # Create execution request
        request = {
            "message_id": str(uuid.uuid4())[:8],
            "execution_id": session.execution_id,
            "operation": operation,
            "parameters": parameters,
            "allocated_budget": session.approval.allocated_budget
        }

        session.add_message("execution_request", request)

        try:
            # Call target aFDO for execution
            response = await self.agent.call_other_afdo(
                target_pid=session.callee_pid,
                operation=operation,
                data={
                    **parameters,
                    "__execution_id": session.execution_id,
                    "__allocated_budget": session.approval.allocated_budget
                }
            )

            # Parse execution result
            result = ExecutionResult(
                message_id=response.get("message_id", str(uuid.uuid4())[:8]),
                execution_id=session.execution_id,
                status=response.get("status", "success"),
                result=response.get("result", response),
                actual_cost=response.get("actual_cost", session.estimate.estimated_cost),
                breakdown=response.get("breakdown", [])
            )

            session.result = result
            session.add_message("execution_result", result.to_dict())
            session.transition_to(NegotiationState.COMPLETED)

            self.logger.info(f"✅ Execution completed: {session_id}")
            self.logger.info(f"   Actual cost: ${result.actual_cost:.3f}")

            self._archive_session(session_id)

            return result

        except Exception as e:
            self.logger.error(f"❌ Execution failed: {e}")

            result = ExecutionResult(
                message_id=str(uuid.uuid4())[:8],
                execution_id=session.execution_id,
                status="failed",
                result=None,
                actual_cost=0.0,
                breakdown=[],
                error=str(e)
            )

            session.result = result
            session.transition_to(NegotiationState.FAILED)
            self._archive_session(session_id)

            raise

    async def handle_cost_escalation(
        self,
        session_id: str,
        new_estimate: float,
        reason: str,
        progress: Dict[str, Any]
    ) -> EscalationDecision:
        """
        Handle cost escalation request from callee.

        This is Phase 4 (optional) of negotiation protocol.

        Args:
            session_id: Negotiation session ID
            new_estimate: New cost estimate
            reason: Why cost increased
            progress: Current progress

        Returns:
            EscalationDecision
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"No active session: {session_id}")

        escalation_request = CostEscalationRequest(
            message_id=str(uuid.uuid4())[:8],
            execution_id=session.execution_id,
            original_estimate=session.estimate.estimated_cost,
            new_estimate=new_estimate,
            reason=reason,
            progress=progress
        )

        session.add_message("cost_escalation_request", escalation_request.to_dict())
        session.transition_to(NegotiationState.ESCALATION_REQUESTED)

        self.logger.warning(f"⚠️ Cost escalation in session {session_id}")
        self.logger.warning(f"   Original: ${escalation_request.original_estimate:.3f}")
        self.logger.warning(f"   New: ${new_estimate:.3f}")
        self.logger.warning(f"   Reason: {reason}")

        # Decision logic (can be overridden by subclasses)
        decision = await self._decide_on_escalation(session, escalation_request)

        session.add_message("escalation_decision", decision.to_dict())

        if decision.approved:
            session.approval.allocated_budget = decision.new_budget
            session.transition_to(NegotiationState.EXECUTING)
            self.logger.info(f"✅ Escalation approved: new budget ${decision.new_budget:.3f}")
        else:
            if decision.action == "abort":
                session.transition_to(NegotiationState.FAILED)
                self.logger.info(f"❌ Escalation rejected: aborting")
            else:
                self.logger.info(f"🔄 Escalation rejected: {decision.action}")

        return decision

    async def _decide_on_escalation(
        self,
        session: NegotiationSession,
        request: CostEscalationRequest
    ) -> EscalationDecision:
        """
        Decide how to handle cost escalation.

        Default implementation - can be overridden by agents.
        """
        # Simple logic: approve if within reasonable range
        increase_ratio = request.new_estimate / request.original_estimate

        if increase_ratio < 1.5:  # Less than 50% increase
            return EscalationDecision(
                message_id=str(uuid.uuid4())[:8],
                escalation_message_id=request.message_id,
                approved=True,
                new_budget=request.new_estimate,
                action="continue"
            )
        else:
            return EscalationDecision(
                message_id=str(uuid.uuid4())[:8],
                escalation_message_id=request.message_id,
                approved=False,
                action="abort",
                revision_instructions="Cost increase too high"
            )

    # ========================================================================
    # SERVER SIDE (Providing services to others)
    # ========================================================================

    async def provide_estimate(
        self,
        caller_pid: str,
        operation: str,
        parameters: Dict[str, Any],
        budget_limit: Optional[float] = None
    ) -> CostEstimate:
        """
        Provide cost estimate to requesting aFDO.

        This is called when another aFDO requests estimate from this agent.

        Args:
            caller_pid: PID of requesting aFDO
            operation: Operation to estimate
            parameters: Operation parameters
            budget_limit: Caller's budget limit

        Returns:
            CostEstimate
        """
        self.logger.info(f"📊 Providing estimate for {operation} to {caller_pid}")

        # Step 1: Can I do this operation?
        if operation not in self.agent.operations:
            raise ValueError(f"Operation not supported: {operation}")

        # Step 2: Calculate my own cost
        my_cost = self.agent.cost

        # Step 3: Do I need helpers? (consult policy)
        context = {
            "caller_pid": caller_pid,
            "budget_limit": budget_limit,
            "operation": operation,
            "parameters": parameters
        }

        decision = await self.agent.policy_engine.decide(
            operation=operation,
            parameters=parameters,
            context=context
        )

        breakdown = [{
            "component": f"self_{operation}",
            "agent_pid": self.agent.pid,
            "cost": my_cost,
            "description": f"{self.agent.name} execution"
        }]

        total_cost = my_cost
        estimated_time = 10.0  # Default estimate

        # Step 4: If need helpers, get their estimates (RECURSIVE!)
        if decision.decision.value in ["query_registry_for_helper", "collaborate"]:
            helper_estimates = await self._estimate_helper_costs(
                operation=operation,
                parameters=parameters,
                decision=decision
            )

            for helper_est in helper_estimates:
                total_cost += helper_est["cost"]
                estimated_time += helper_est["time"]
                breakdown.append({
                    "component": helper_est["operation"],
                    "agent_pid": helper_est["agent_pid"],
                    "cost": helper_est["cost"],
                    "description": helper_est["description"]
                })

        # Step 5: Create estimate
        estimate = CostEstimate(
            message_id=str(uuid.uuid4())[:8],
            responder_pid=self.agent.pid,
            estimated_cost=total_cost,
            estimated_time=estimated_time,
            confidence=0.85,  # Can be made more sophisticated
            breakdown=breakdown
        )

        self.logger.info(f"✅ Estimate provided: ${total_cost:.3f} ({len(breakdown)} components)")

        return estimate

    async def _estimate_helper_costs(
        self,
        operation: str,
        parameters: Dict[str, Any],
        decision
    ) -> List[Dict[str, Any]]:
        """
        Get cost estimates from helpers (recursive negotiation).

        This is where RECURSIVE estimation happens!
        """
        helper_estimates = []

        # Extract discovery query from decision
        if decision.parameters and "registry_query" in decision.parameters:
            query = decision.parameters["registry_query"]
            operation_to_find = query.get("operation")

            if operation_to_find and operation_to_find != "from_request":
                # Discover helpers
                helpers = await self.agent.discover_by_operation(operation_to_find)

                if helpers:
                    # Request estimate from first helper (can be made more sophisticated)
                    helper = helpers[0]

                    try:
                        # RECURSIVE call to request_estimate!
                        helper_estimate = await self.request_estimate(
                            target_pid=helper["pid"],
                            operation=operation_to_find,
                            parameters=parameters
                        )

                        helper_estimates.append({
                            "operation": operation_to_find,
                            "agent_pid": helper["pid"],
                            "cost": helper_estimate.estimated_cost,
                            "time": helper_estimate.estimated_time,
                            "description": f"{helper['name']} - {operation_to_find}"
                        })

                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to get helper estimate: {e}")

        return helper_estimates

    def _archive_session(self, session_id: str):
        """Archive completed session."""
        if session_id in self.active_sessions:
            session = self.active_sessions.pop(session_id)
            self.completed_sessions.append(session)

            # Keep only last N sessions
            if len(self.completed_sessions) > self.max_completed:
                self.completed_sessions = self.completed_sessions[-self.max_completed:]

    def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        """Get session by ID."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        for session in self.completed_sessions:
            if session.session_id == session_id:
                return session

        return None

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return [s.to_dict() for s in self.active_sessions.values()]
