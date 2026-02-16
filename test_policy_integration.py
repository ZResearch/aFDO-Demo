#!/usr/bin/env python3
"""Integration test for Policy Engine with real agents."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from shared.policy_engine import PolicyEngine, DecisionType


def test_policy_loading():
    """Test that policies can be loaded correctly."""
    print("\n" + "="*60)
    print("POLICY ENGINE INTEGRATION TEST")
    print("="*60)

    # Test 1: Load task policy
    print("\n--- Test 1: Load Task Agent Policy ---")
    try:
        engine = PolicyEngine(
            agent_pid="test-task",
            agent_capabilities=["parse_pdf", "extract_text"],
            policy_file="shared/policies/default_task_policy.json"
        )
        info = engine.get_policy_info()
        print(f"✅ Loaded: {info['policy_id']}")
        print(f"   Version: {info['policy_version']}")
        print(f"   Rules: {info['rule_count']}")
        print(f"   Default: {info['default_action']}")
    except Exception as e:
        print(f"❌ Failed to load task policy: {e}")
        return False

    # Test 2: Load composite policy
    print("\n--- Test 2: Load Composite Agent Policy ---")
    try:
        engine = PolicyEngine(
            agent_pid="test-composite",
            agent_capabilities=["coordinate", "plan"],
            policy_file="shared/policies/default_composite_policy.json"
        )
        info = engine.get_policy_info()
        print(f"✅ Loaded: {info['policy_id']}")
        print(f"   Version: {info['policy_version']}")
        print(f"   Rules: {info['rule_count']}")
        print(f"   Default: {info['default_action']}")
    except Exception as e:
        print(f"❌ Failed to load composite policy: {e}")
        return False

    # Test 3: Load interface policy
    print("\n--- Test 3: Load Interface Agent Policy ---")
    try:
        engine = PolicyEngine(
            agent_pid="test-interface",
            agent_capabilities=["display_message", "receive_user_input"],
            policy_file="shared/policies/default_interface_policy.json"
        )
        info = engine.get_policy_info()
        print(f"✅ Loaded: {info['policy_id']}")
        print(f"   Version: {info['policy_version']}")
        print(f"   Rules: {info['rule_count']}")
        print(f"   Default: {info['default_action']}")
    except Exception as e:
        print(f"❌ Failed to load interface policy: {e}")
        return False

    # Test 4: Load Chat UI policy
    print("\n--- Test 4: Load Chat UI Agent Policy ---")
    if Path("agents/chat_ui/policy.json").exists():
        try:
            engine = PolicyEngine(
                agent_pid="test-chat-ui",
                agent_capabilities=["display_message", "receive_user_input"],
                policy_file="agents/chat_ui/policy.json"
            )
            info = engine.get_policy_info()
            print(f"✅ Loaded: {info['policy_id']}")
            print(f"   Version: {info['policy_version']}")
            print(f"   Rules: {info['rule_count']}")
            print(f"   Default: {info['default_action']}")
        except Exception as e:
            print(f"❌ Failed to load chat UI policy: {e}")
            return False
    else:
        print("⚠️  Chat UI policy not found (skipping)")

    # Test 5: Load Paper Analyzer policy
    print("\n--- Test 5: Load Paper Analyzer Agent Policy ---")
    if Path("agents/paper_analyzer/policy.json").exists():
        try:
            engine = PolicyEngine(
                agent_pid="test-paper-analyzer",
                agent_capabilities=["analyze_paper", "extract_key_findings"],
                policy_file="agents/paper_analyzer/policy.json"
            )
            info = engine.get_policy_info()
            print(f"✅ Loaded: {info['policy_id']}")
            print(f"   Version: {info['policy_version']}")
            print(f"   Rules: {info['rule_count']}")
            print(f"   Default: {info['default_action']}")
        except Exception as e:
            print(f"❌ Failed to load paper analyzer policy: {e}")
            return False
    else:
        print("⚠️  Paper Analyzer policy not found (skipping)")

    # Test 6: Load PDF Parser policy
    print("\n--- Test 6: Load PDF Parser Agent Policy ---")
    if Path("agents/pdf_parser/policy.json").exists():
        try:
            engine = PolicyEngine(
                agent_pid="test-pdf-parser",
                agent_capabilities=["parse_pdf", "extract_text"],
                policy_file="agents/pdf_parser/policy.json"
            )
            info = engine.get_policy_info()
            print(f"✅ Loaded: {info['policy_id']}")
            print(f"   Version: {info['policy_version']}")
            print(f"   Rules: {info['rule_count']}")
            print(f"   Default: {info['default_action']}")
        except Exception as e:
            print(f"❌ Failed to load PDF parser policy: {e}")
            return False
    else:
        print("⚠️  PDF Parser policy not found (skipping)")

    print("\n" + "="*60)
    print("✅ ALL POLICY FILES LOAD SUCCESSFULLY!")
    print("="*60)
    return True


def test_afdo_base_imports():
    """Test that aFDOBase can import policy engine."""
    print("\n" + "="*60)
    print("AFDO BASE INTEGRATION TEST")
    print("="*60)

    print("\n--- Testing imports ---")
    try:
        from shared.afdo_base import aFDOBase
        from shared.policy_engine import PolicyEngine, PolicyDecision, DecisionType
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    print("\n--- Testing aFDOBase has policy engine methods ---")
    methods_to_check = [
        '_load_policy_engine',
        '_infer_agent_type',
        'handle_operation_with_policy',
        '_execute_policy_decision',
        '_query_and_delegate_to_helper',
        '_query_and_delegate_to_planner',
        '_delegate_fully',
        '_collaborate',
        '_execute_fallback'
    ]

    for method in methods_to_check:
        if hasattr(aFDOBase, method):
            print(f"✅ {method} exists")
        else:
            print(f"❌ {method} missing")
            return False

    print("\n" + "="*60)
    print("✅ AFDO BASE INTEGRATION SUCCESSFUL!")
    print("="*60)
    return True


def test_agent_type_inference():
    """Test agent type inference logic."""
    print("\n" + "="*60)
    print("AGENT TYPE INFERENCE TEST")
    print("="*60)

    from shared.afdo_base import aFDOBase

    # Create a mock subclass to test _infer_agent_type
    class MockAgent(aFDOBase):
        def __init__(self, fdo_type):
            self.fdo_type = fdo_type

        def get_metadata_content(self):
            return {}

        def get_self_description(self):
            return {}

        async def handle_operation(self, operation, caller_pid, parameters):
            return {}

    test_cases = [
        ("21.T11148/type-user-interface-v1", "interface"),
        ("21.T11148/type-chat-ui-v1", "interface"),
        ("21.T11148/type-web-interface-v1", "interface"),
        ("21.T11148/type-workflow-coordinator-v1", "composite"),
        ("21.T11148/type-planner-v1", "composite"),
        ("21.T11148/type-orchestrator-v1", "composite"),
        ("21.T11148/type-composite-agent-v1", "composite"),
        ("21.T11148/type-pdf-parser-v1", "task"),
        ("21.T11148/type-data-processor-v1", "task"),
        ("21.T11148/type-analyzer-v1", "task"),
    ]

    print("\n--- Testing type inference ---")
    all_passed = True
    for fdo_type, expected_type in test_cases:
        mock = MockAgent(fdo_type)
        inferred = mock._infer_agent_type(fdo_type)
        if inferred == expected_type:
            print(f"✅ {fdo_type} → {inferred}")
        else:
            print(f"❌ {fdo_type} → {inferred} (expected {expected_type})")
            all_passed = False

    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL TYPE INFERENCE TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME TYPE INFERENCE TESTS FAILED!")
        print("="*60)

    return all_passed


def test_policy_validation():
    """Test policy files are valid JSON."""
    print("\n" + "="*60)
    print("POLICY FILE VALIDATION TEST")
    print("="*60)

    import json

    policy_files = [
        "shared/policies/default_task_policy.json",
        "shared/policies/default_composite_policy.json",
        "shared/policies/default_interface_policy.json",
        "agents/chat_ui/policy.json",
        "agents/paper_analyzer/policy.json",
        "agents/pdf_parser/policy.json",
    ]

    print("\n--- Validating JSON syntax ---")
    all_valid = True
    for policy_file in policy_files:
        if not Path(policy_file).exists():
            print(f"⚠️  {policy_file} not found (skipping)")
            continue

        try:
            with open(policy_file) as f:
                policy = json.load(f)

            # Check required fields
            required = ["policy_id", "policy_version", "rules"]
            missing = [field for field in required if field not in policy]
            if missing:
                print(f"❌ {policy_file}: Missing fields: {missing}")
                all_valid = False
            else:
                print(f"✅ {policy_file}: Valid JSON with all required fields")
        except json.JSONDecodeError as e:
            print(f"❌ {policy_file}: Invalid JSON - {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {policy_file}: Error - {e}")
            all_valid = False

    if all_valid:
        print("\n" + "="*60)
        print("✅ ALL POLICY FILES ARE VALID!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME POLICY FILES ARE INVALID!")
        print("="*60)

    return all_valid


if __name__ == "__main__":
    print("\n" + "="*60)
    print("POLICY ENGINE INTEGRATION TEST SUITE")
    print("="*60)

    all_passed = True

    # Run all tests
    if not test_policy_loading():
        all_passed = False

    if not test_afdo_base_imports():
        all_passed = False

    if not test_agent_type_inference():
        all_passed = False

    if not test_policy_validation():
        all_passed = False

    # Final result
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("❌ SOME INTEGRATION TESTS FAILED!")
        print("="*60 + "\n")
        sys.exit(1)
