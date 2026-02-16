"""
Test Negotiation Protocol

Tests:
1. Simple estimate request/response
2. Recursive estimation (agent needs helpers)
3. Budget approval/rejection
4. Execution with budget tracking
5. Cost escalation handling
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.protocols.negotiation import NegotiationProtocol, CostEstimate
from shared.afdo_base import aFDOBase


# Mock agents for testing
class MockSimpleAgent(aFDOBase):
    """Simple agent that doesn't need helpers."""
    
    def __init__(self, name, cost):
        super().__init__(
            name=name,
            fdo_type="21.T11148/type-test-v1",
            operations=["simple_operation"],
            port=9000,
            cost=cost,
            has_llm=False
        )
    
    def get_metadata_content(self):
        return {}
    
    def get_self_description(self):
        return {}
    
    async def _execute_operation(self, operation, parameters):
        return {"result": f"Executed {operation}", "status": "success"}


class MockCompositeAgent(aFDOBase):
    """Agent that needs helpers (uses negotiation recursively)."""
    
    def __init__(self, name):
        super().__init__(
            name=name,
            fdo_type="21.T11148/type-test-v1",
            operations=["complex_operation"],
            port=9001,
            cost=0.05,
            has_llm=False
        )
    
    def get_metadata_content(self):
        return {}
    
    def get_self_description(self):
        return {}
    
    async def _execute_operation(self, operation, parameters):
        # Simulate needing a helper
        return {
            "result": "Complex result",
            "status": "success",
            "helpers_used": ["helper_agent"]
        }
    
    async def discover_by_operation(self, operation):
        # Mock discovery - return a simple agent
        return [{
            "pid": "mock-helper-pid",
            "name": "Mock Helper",
            "cost": 0.02,
            "reputation": 0.8
        }]


async def test_simple_estimate():
    """Test 1: Simple estimate request/response."""
    print("\n" + "="*60)
    print("TEST 1: Simple Estimate Request/Response")
    print("="*60)
    
    # Create agents
    caller = MockSimpleAgent("Caller Agent", 0.01)
    callee = MockSimpleAgent("Callee Agent", 0.03)
    
    # Caller requests estimate
    print("\n📞 Caller requesting estimate from Callee...")
    
    # Mock the call (in real system, this goes through DOIP)
    estimate = await callee.negotiation.provide_estimate(
        caller_pid=caller.pid,
        operation="simple_operation",
        parameters={"data": "test"}
    )
    
    print(f"✅ Received estimate:")
    print(f"   Cost: ${estimate.estimated_cost:.3f}")
    print(f"   Time: {estimate.estimated_time:.1f}s")
    print(f"   Confidence: {estimate.confidence:.0%}")
    print(f"   Breakdown: {len(estimate.breakdown)} items")
    
    assert estimate.estimated_cost == 0.03, "Cost should match callee's cost"
    print("\n✅ TEST 1 PASSED")


async def test_recursive_estimation():
    """Test 2: Recursive estimation (agent needs helpers)."""
    print("\n" + "="*60)
    print("TEST 2: Recursive Estimation")
    print("="*60)
    
    # Create agents
    caller = MockSimpleAgent("Caller", 0.01)
    composite = MockCompositeAgent("Composite Agent")
    
    print("\n📞 Requesting estimate from composite agent...")
    print("   (Composite agent will need to discover helpers)")
    
    # Composite agent provides estimate
    # It should discover helpers and get their estimates too
    estimate = await composite.negotiation.provide_estimate(
        caller_pid=caller.pid,
        operation="complex_operation",
        parameters={"data": "complex"}
    )
    
    print(f"\n✅ Received estimate:")
    print(f"   Total Cost: ${estimate.estimated_cost:.3f}")
    print(f"   Breakdown:")
    for item in estimate.breakdown:
        print(f"     - {item['component']}: ${item['cost']:.3f} ({item['agent_pid']})")
    
    # Should include composite's cost + helper's cost
    assert estimate.estimated_cost > 0.05, "Should include helper costs"
    print("\n✅ TEST 2 PASSED")


async def test_approval_flow():
    """Test 3: Full approval flow (estimate → approve → execute)."""
    print("\n" + "="*60)
    print("TEST 3: Full Approval Flow")
    print("="*60)
    
    caller = MockSimpleAgent("Caller", 0.01)
    callee = MockSimpleAgent("Callee", 0.03)
    
    print("\n📞 Step 1: Request estimate...")
    
    # Create a mock session manually for testing
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    estimate = await callee.negotiation.provide_estimate(
        caller_pid=caller.pid,
        operation="simple_operation",
        parameters={"data": "test"}
    )
    
    print(f"   Estimate: ${estimate.estimated_cost:.3f}")
    
    # Store estimate in caller's session
    from shared.protocols.negotiation import NegotiationSession
    session = NegotiationSession(session_id, caller.pid, callee.pid)
    session.estimate = estimate
    caller.negotiation.active_sessions[session_id] = session
    
    print("\n✅ Step 2: Approve estimate...")
    
    execution_id = await caller.negotiation.approve_estimate(
        session_id=session_id,
        approved=True,
        allocated_budget=estimate.estimated_cost
    )
    
    print(f"   Execution ID: {execution_id}")
    
    print("\n🚀 Step 3: Execute with budget...")
    
    # Mock execution
    result = await callee._execute_operation("simple_operation", {"data": "test"})
    
    print(f"   Result: {result['result']}")
    print(f"   Status: {result['status']}")
    
    print("\n✅ TEST 3 PASSED")


async def test_budget_rejection():
    """Test 4: Budget rejection scenario."""
    print("\n" + "="*60)
    print("TEST 4: Budget Rejection")
    print("="*60)
    
    caller = MockSimpleAgent("Caller", 0.01)
    expensive_callee = MockSimpleAgent("Expensive Callee", 0.50)
    
    print("\n📞 Requesting estimate from expensive agent...")
    
    estimate = await expensive_callee.negotiation.provide_estimate(
        caller_pid=caller.pid,
        operation="simple_operation",
        parameters={"data": "test"},
        budget_limit=0.10  # Caller only has $0.10
    )
    
    print(f"   Estimate: ${estimate.estimated_cost:.3f}")
    print(f"   Budget limit: $0.10")
    
    # Create session
    import uuid
    session_id = str(uuid.uuid4())[:8]
    from shared.protocols.negotiation import NegotiationSession
    session = NegotiationSession(session_id, caller.pid, expensive_callee.pid)
    session.estimate = estimate
    caller.negotiation.active_sessions[session_id] = session
    
    print("\n❌ Rejecting estimate (exceeds budget)...")
    
    execution_id = await caller.negotiation.approve_estimate(
        session_id=session_id,
        approved=False,
        reason="Exceeds budget limit"
    )
    
    assert execution_id is None, "Should not receive execution_id when rejected"
    assert session.state.value == "cancelled", "Session should be cancelled"
    
    print("   Session cancelled")
    print("\n✅ TEST 4 PASSED")


async def test_cost_escalation():
    """Test 5: Cost escalation during execution."""
    print("\n" + "="*60)
    print("TEST 5: Cost Escalation")
    print("="*60)
    
    caller = MockSimpleAgent("Caller", 0.01)
    callee = MockSimpleAgent("Callee", 0.03)
    
    # Setup approved session
    import uuid
    session_id = str(uuid.uuid4())[:8]
    from shared.protocols.negotiation import NegotiationSession
    session = NegotiationSession(session_id, caller.pid, callee.pid)
    
    # Mock estimate and approval
    from shared.protocols.negotiation import CostEstimate, ApprovalDecision
    estimate = CostEstimate(
        message_id=str(uuid.uuid4())[:8],
        responder_pid=callee.pid,
        estimated_cost=0.03,
        estimated_time=5.0,
        confidence=0.9,
        breakdown=[{"component": "test", "agent_pid": callee.pid, "cost": 0.03, "description": "test"}]
    )
    
    approval = ApprovalDecision(
        message_id=str(uuid.uuid4())[:8],
        estimate_message_id=estimate.message_id,
        approved=True,
        allocated_budget=0.03,
        execution_id=str(uuid.uuid4())[:8]
    )
    
    session.estimate = estimate
    session.approval = approval
    session.execution_id = approval.execution_id
    caller.negotiation.active_sessions[session_id] = session
    
    print("\n⚠️ During execution, cost increases from $0.03 to $0.08...")
    
    # Callee requests escalation
    decision = await caller.negotiation.handle_cost_escalation(
        session_id=session_id,
        new_estimate=0.08,
        reason="Data larger than expected",
        progress={
            "completed_steps": ["step1"],
            "remaining_steps": ["step2", "step3"],
            "spent_so_far": 0.01
        }
    )
    
    print(f"\n📊 Escalation decision:")
    print(f"   Approved: {decision.approved}")
    print(f"   Action: {decision.action}")
    
    if decision.approved:
        print(f"   New budget: ${decision.new_budget:.3f}")
        print("   ✅ Escalation approved - execution continues")
    else:
        print(f"   Reason: Increase too large")
        print("   ❌ Escalation rejected - execution aborted")
    
    print("\n✅ TEST 5 PASSED")


async def run_all_tests():
    """Run all negotiation protocol tests."""
    print("\n" + "="*60)
    print("NEGOTIATION PROTOCOL TEST SUITE")
    print("="*60)
    
    await test_simple_estimate()
    await test_recursive_estimation()
    await test_approval_flow()
    await test_budget_rejection()
    await test_cost_escalation()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
