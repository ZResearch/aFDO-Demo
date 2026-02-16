#!/usr/bin/env python3
"""Test script for Policy Engine framework."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.policy_engine import PolicyEngine, DecisionType


async def test_task_agent_policy():
    """Test default task agent policy."""
    print("\n" + "="*60)
    print("TEST 1: Task Agent Policy")
    print("="*60)

    engine = PolicyEngine(
        agent_pid="test-task-agent",
        agent_capabilities=["parse_pdf", "extract_text"],
        policy_file="shared/policies/default_task_policy.json"
    )

    policy_info = engine.get_policy_info()
    print(f"\n📋 Policy: {policy_info['policy_id']} v{policy_info['policy_version']}")
    print(f"   Rules: {policy_info['rule_count']}")
    print(f"   Default: {policy_info['default_action']}")

    # Test 1: Operation within capability
    print("\n--- Test 1a: Operation within capability ---")
    decision = await engine.decide(
        operation="parse_pdf",
        parameters={"file": "test.pdf"},
        context={}
    )
    print(f"Operation: parse_pdf")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Rule: {decision.rule_id}")
    assert decision.decision == DecisionType.HANDLE_ALONE

    # Test 2: Operation outside capability
    print("\n--- Test 1b: Operation outside capability ---")
    decision = await engine.decide(
        operation="analyze_data",
        parameters={"data": "test"},
        context={}
    )
    print(f"Operation: analyze_data")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Rule: {decision.rule_id}")
    assert decision.decision == DecisionType.QUERY_REGISTRY_FOR_HELPER

    print("\n✅ Task Agent Policy tests passed!")


async def test_composite_agent_policy():
    """Test default composite agent policy."""
    print("\n" + "="*60)
    print("TEST 2: Composite Agent Policy")
    print("="*60)

    engine = PolicyEngine(
        agent_pid="test-composite-agent",
        agent_capabilities=["coordinate", "plan"],
        policy_file="shared/policies/default_composite_policy.json"
    )

    policy_info = engine.get_policy_info()
    print(f"\n📋 Policy: {policy_info['policy_id']} v{policy_info['policy_version']}")
    print(f"   Rules: {policy_info['rule_count']}")
    print(f"   Default: {policy_info['default_action']}")

    # Test 1: Simple task within capability
    print("\n--- Test 2a: Simple task within capability ---")
    decision = await engine.decide(
        operation="plan",
        parameters={"task": "simple"},
        context={}
    )
    print(f"Operation: plan (simple)")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    assert decision.decision == DecisionType.HANDLE_ALONE

    # Test 2: Moderate complexity task
    print("\n--- Test 2b: Moderate complexity task ---")
    decision = await engine.decide(
        operation="coordinate",
        parameters={"task": "moderate", "p1": "v1", "p2": "v2", "p3": "v3"},
        context={}
    )
    print(f"Operation: coordinate (moderate)")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Parameters: {decision.parameters}")
    assert decision.decision == DecisionType.COLLABORATE

    # Test 3: Complex task
    print("\n--- Test 2c: Complex task ---")
    decision = await engine.decide(
        operation="analyze",
        parameters={"p1": "v1", "p2": "v2", "p3": "v3", "p4": "v4", "p5": "v5"},
        context={}
    )
    print(f"Operation: analyze (complex)")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    assert decision.decision == DecisionType.COLLABORATE

    print("\n✅ Composite Agent Policy tests passed!")


async def test_interface_agent_policy():
    """Test default interface agent policy."""
    print("\n" + "="*60)
    print("TEST 3: Interface Agent Policy")
    print("="*60)

    engine = PolicyEngine(
        agent_pid="test-interface-agent",
        agent_capabilities=["greeting", "hello", "help", "display_message"],
        policy_file="shared/policies/default_interface_policy.json"
    )

    policy_info = engine.get_policy_info()
    print(f"\n📋 Policy: {policy_info['policy_id']} v{policy_info['policy_version']}")
    print(f"   Rules: {policy_info['rule_count']}")
    print(f"   Default: {policy_info['default_action']}")

    # Test 1: Greeting
    print("\n--- Test 3a: Greeting operation ---")
    decision = await engine.decide(
        operation="hello",
        parameters={},
        context={}
    )
    print(f"Operation: hello")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    assert decision.decision == DecisionType.HANDLE_ALONE

    # Test 2: User request
    print("\n--- Test 3b: User request ---")
    decision = await engine.decide(
        operation="receive_user_input",
        parameters={"query": "Analyze this paper"},
        context={}
    )
    print(f"Operation: receive_user_input")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    assert decision.decision == DecisionType.DELEGATE_FULLY

    print("\n✅ Interface Agent Policy tests passed!")


async def test_chat_ui_policy():
    """Test Chat UI agent-specific policy."""
    print("\n" + "="*60)
    print("TEST 4: Chat UI Agent Policy")
    print("="*60)

    policy_file = "agents/chat_ui/policy.json"
    if not Path(policy_file).exists():
        print(f"⚠️  Skipping - policy file not found: {policy_file}")
        return

    engine = PolicyEngine(
        agent_pid="test-chat-ui",
        agent_capabilities=["display_message", "receive_user_input", "execute_workflow"],
        policy_file=policy_file
    )

    policy_info = engine.get_policy_info()
    print(f"\n📋 Policy: {policy_info['policy_id']} v{policy_info['policy_version']}")
    print(f"   Rules: {policy_info['rule_count']}")
    print(f"   Default: {policy_info['default_action']}")

    # Test 1: Display message
    print("\n--- Test 4a: Display message ---")
    decision = await engine.decide(
        operation="display_message",
        parameters={"message": "Hello"},
        context={}
    )
    print(f"Operation: display_message")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    assert decision.decision == DecisionType.HANDLE_ALONE

    # Test 2: User input
    print("\n--- Test 4b: User input ---")
    decision = await engine.decide(
        operation="receive_user_input",
        parameters={"query": "Analyze paper", "param1": "v1", "param2": "v2"},
        context={}
    )
    print(f"Operation: receive_user_input")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Parameters: {decision.parameters}")

    print("\n✅ Chat UI Policy tests passed!")


async def test_paper_analyzer_policy():
    """Test Paper Analyzer agent-specific policy."""
    print("\n" + "="*60)
    print("TEST 5: Paper Analyzer Agent Policy")
    print("="*60)

    policy_file = "agents/paper_analyzer/policy.json"
    if not Path(policy_file).exists():
        print(f"⚠️  Skipping - policy file not found: {policy_file}")
        return

    engine = PolicyEngine(
        agent_pid="test-paper-analyzer",
        agent_capabilities=["analyze_paper", "extract_key_findings", "assess_methodology"],
        policy_file=policy_file
    )

    policy_info = engine.get_policy_info()
    print(f"\n📋 Policy: {policy_info['policy_id']} v{policy_info['policy_version']}")
    print(f"   Rules: {policy_info['rule_count']}")
    print(f"   Default: {policy_info['default_action']}")

    # Test 1: Simple extraction
    print("\n--- Test 5a: Simple extraction ---")
    decision = await engine.decide(
        operation="extract_key_findings",
        parameters={"text": "paper text"},
        context={}
    )
    print(f"Operation: extract_key_findings")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    assert decision.decision == DecisionType.HANDLE_ALONE

    # Test 2: Full analysis (complex)
    print("\n--- Test 5b: Full analysis (complex) ---")
    decision = await engine.decide(
        operation="analyze_paper",
        parameters={
            "pdf_data": "base64",
            "metadata": {},
            "options": {},
            "p1": "v1",
            "p2": "v2",
            "p3": "v3",
            "p4": "v4"
        },
        context={}
    )
    print(f"Operation: analyze_paper (complex)")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Parameters: {decision.parameters}")
    assert decision.decision == DecisionType.COLLABORATE

    # Test 3: With sufficient budget
    print("\n--- Test 5c: With sufficient budget ---")
    decision = await engine.decide(
        operation="analyze_paper",
        parameters={"pdf_data": "base64"},
        context={"budget": 1.0}  # Above threshold (0.5)
    )
    print(f"Operation: analyze_paper (sufficient budget)")
    print(f"Decision: {decision.decision.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Parameters: {decision.parameters}")
    assert decision.decision == DecisionType.COLLABORATE
    # With budget >= 0.5, should use balanced approach
    assert decision.parameters.get("selection_criteria") == "balanced"

    print("\n✅ Paper Analyzer Policy tests passed!")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("POLICY ENGINE TEST SUITE")
    print("="*60)

    try:
        await test_task_agent_policy()
        await test_composite_agent_policy()
        await test_interface_agent_policy()
        await test_chat_ui_policy()
        await test_paper_analyzer_policy()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
