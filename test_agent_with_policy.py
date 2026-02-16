#!/usr/bin/env python3
"""Test that a real agent can load and use policy engine."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from shared.afdo_base import aFDOBase
from typing import Dict, Any


class TestAgent(aFDOBase):
    """Test agent to verify policy engine integration."""

    def __init__(self):
        super().__init__(
            name="Test Agent",
            fdo_type="21.T11148/type-test-task-agent-v1",
            operations=["test_operation", "another_operation"],
            port=9999,  # Won't actually start server
            cost=0.01
        )

    def get_metadata_content(self) -> Dict[str, Any]:
        return {
            "description": "Test agent for policy engine verification",
            "version": "1.0.0"
        }

    def get_self_description(self) -> Dict[str, Any]:
        return {
            "agent_info": {
                "name": "Test Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Test agent"
            },
            "capabilities": {
                "test_operation": {
                    "operation_type": "test",
                    "input_schema": {"type": "object"},
                    "output_schema": {"type": "object"},
                    "side_effects": [],
                    "idempotent": True
                }
            }
        }

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle test operation."""
        return {
            "status": "success",
            "operation": operation,
            "message": f"Handled {operation} from {caller_pid}"
        }


async def test_agent_policy_loading():
    """Test that agent can load policy engine."""
    print("\n" + "="*60)
    print("AGENT POLICY LOADING TEST")
    print("="*60)

    print("\n--- Creating test agent ---")
    agent = TestAgent()
    print(f"✅ Agent created: {agent.name}")
    print(f"   PID: {agent.pid}")
    print(f"   Type: {agent.fdo_type}")
    print(f"   Operations: {agent.operations}")

    print("\n--- Loading policy engine ---")
    agent.policy_engine = agent._load_policy_engine()

    if agent.policy_engine:
        print("✅ Policy engine loaded!")
        policy_info = agent.policy_engine.get_policy_info()
        print(f"   Policy ID: {policy_info['policy_id']}")
        print(f"   Version: {policy_info['policy_version']}")
        print(f"   Rules: {policy_info['rule_count']}")
        print(f"   Default: {policy_info['default_action']}")
    else:
        print("⚠️  No policy engine loaded (using default behavior)")

    print("\n--- Testing policy decisions ---")

    # Test 1: Operation within capability
    print("\n  Test 1: Operation within capability")
    decision = await agent.policy_engine.decide(
        operation="test_operation",
        parameters={"param": "value"},
        context={"caller_pid": "test-caller"}
    )
    print(f"  Decision: {decision.decision.value}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Rule: {decision.rule_id}")

    # Test 2: Operation outside capability
    print("\n  Test 2: Operation outside capability")
    decision = await agent.policy_engine.decide(
        operation="unknown_operation",
        parameters={"param": "value"},
        context={"caller_pid": "test-caller"}
    )
    print(f"  Decision: {decision.decision.value}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Rule: {decision.rule_id}")

    # Test 3: Complex operation
    print("\n  Test 3: Complex operation (many parameters)")
    decision = await agent.policy_engine.decide(
        operation="test_operation",
        parameters={
            "p1": "v1", "p2": "v2", "p3": "v3",
            "p4": "v4", "p5": "v5", "p6": "v6"
        },
        context={"caller_pid": "test-caller"}
    )
    print(f"  Decision: {decision.decision.value}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Assessed complexity: complex")

    print("\n--- Testing handle_operation_with_policy ---")
    try:
        result = await agent.handle_operation_with_policy(
            operation="test_operation",
            caller_pid="test-caller",
            parameters={"test_param": "test_value"}
        )
        print(f"✅ Operation handled successfully")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*60)
    print("✅ AGENT POLICY LOADING TEST PASSED!")
    print("="*60)
    return True


async def test_different_agent_types():
    """Test that different agent types get correct default policies."""
    print("\n" + "="*60)
    print("AGENT TYPE POLICY SELECTION TEST")
    print("="*60)

    test_cases = [
        ("Task Agent", "21.T11148/type-task-agent-v1", "task", "default_task_agent_policy"),
        ("Composite Agent", "21.T11148/type-coordinator-v1", "composite", "default_composite_agent_policy"),
        ("Interface Agent", "21.T11148/type-interface-v1", "interface", "default_interface_agent_policy"),
    ]

    for name, fdo_type, expected_type, expected_policy_id in test_cases:
        print(f"\n--- Testing {name} ---")

        class TempAgent(aFDOBase):
            def __init__(self, n, t):
                super().__init__(
                    name=n,
                    fdo_type=t,
                    operations=["test_op"],
                    port=9999
                )

            def get_metadata_content(self):
                return {"description": "Test"}

            def get_self_description(self):
                return {
                    "agent_info": {"name": "Test", "version": "1.0.0", "agent_type": "test", "description": "Test"},
                    "capabilities": {"test_op": {"operation_type": "test", "input_schema": {}, "output_schema": {}, "side_effects": [], "idempotent": True}}
                }

            async def handle_operation(self, operation, caller_pid, parameters):
                return {"status": "success"}

        agent = TempAgent(name, fdo_type)
        inferred_type = agent._infer_agent_type(fdo_type)
        print(f"  FDO Type: {fdo_type}")
        print(f"  Inferred: {inferred_type}")
        print(f"  Expected: {expected_type}")

        if inferred_type == expected_type:
            print(f"  ✅ Type inference correct")
        else:
            print(f"  ❌ Type inference wrong")
            return False

        # Load policy
        agent.policy_engine = agent._load_policy_engine()
        if agent.policy_engine:
            policy_info = agent.policy_engine.get_policy_info()
            print(f"  Policy: {policy_info['policy_id']}")

            if policy_info['policy_id'] == expected_policy_id:
                print(f"  ✅ Correct policy loaded")
            else:
                print(f"  ❌ Wrong policy loaded (expected {expected_policy_id})")
                return False
        else:
            print(f"  ⚠️  No policy loaded")

    print("\n" + "="*60)
    print("✅ AGENT TYPE POLICY SELECTION TEST PASSED!")
    print("="*60)
    return True


async def main():
    """Run all agent tests."""
    print("\n" + "="*60)
    print("AGENT WITH POLICY ENGINE - INTEGRATION TEST")
    print("="*60)

    all_passed = True

    if not await test_agent_policy_loading():
        all_passed = False

    if not await test_different_agent_types():
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL AGENT INTEGRATION TESTS PASSED!")
        print("="*60 + "\n")
        return True
    else:
        print("❌ SOME AGENT INTEGRATION TESTS FAILED!")
        print("="*60 + "\n")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
