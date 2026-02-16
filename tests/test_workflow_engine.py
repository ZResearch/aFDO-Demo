"""
Test Workflow Engine

Tests:
1. Load workflow from JSON
2. Estimate workflow cost
3. Execute simple workflow
4. Execute workflow with dependencies
5. Handle step failures
6. Budget tracking
"""

import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.protocols.workflow_engine import WorkflowEngine
from shared.afdo_base import aFDOBase


class MockWorkflowAgent(aFDOBase):
    """Mock agent for workflow testing."""
    
    def __init__(self):
        super().__init__(
            name="Workflow Test Agent",
            fdo_type="21.T11148/type-test-v1",
            operations=["extract_topic", "concatenate_results", "format_raw_data"],
            port=9002,
            cost=0.01,
            has_llm=False
        )
    
    def get_metadata_content(self):
        return {}
    
    def get_self_description(self):
        return {}
    
    async def _execute_operation(self, operation, parameters):
        """Mock operation execution."""
        if operation == "extract_topic":
            # Extract topic from question
            question = parameters.get("question", "")
            topic = question.split()[0] if question else "unknown"
            return {"topic": topic}
        
        elif operation == "concatenate_results":
            sources = parameters.get("sources", [])
            return {"result": " | ".join(str(s) for s in sources)}
        
        elif operation == "format_raw_data":
            data = parameters.get("data", {})
            return {"formatted": f"Raw: {data}"}
        
        return {"result": f"Executed {operation}"}
    
    async def discover_by_operation(self, operation):
        """Mock discovery - return fake agents."""
        return [{
            "pid": f"mock-{operation}-agent",
            "name": f"Mock {operation}",
            "cost": 0.02,
            "reputation": 0.8
        }]


async def test_load_workflow():
    """Test 1: Load workflow from JSON."""
    print("\n" + "="*60)
    print("TEST 1: Load Workflow from JSON")
    print("="*60)
    
    agent = MockWorkflowAgent()
    
    # Create simple workflow
    workflow = {
        "workflow_id": "test_wf_001",
        "name": "Test Workflow",
        "steps": [
            {
                "step_id": "step_01",
                "operation": "extract_topic",
                "executor": "self",
                "input_mapping": {
                    "question": "workflow.input.question"
                }
            }
        ]
    }
    
    print("\n📋 Loading workflow...")
    agent.workflow_engine.load_workflow(workflow)
    
    print(f"   Workflow ID: {agent.workflow_engine.workflow['workflow_id']}")
    print(f"   Name: {agent.workflow_engine.workflow['name']}")
    print(f"   Steps: {len(agent.workflow_engine.workflow['steps'])}")
    
    print("\n✅ TEST 1 PASSED")


async def test_estimate_workflow():
    """Test 2: Estimate workflow cost."""
    print("\n" + "="*60)
    print("TEST 2: Estimate Workflow Cost")
    print("="*60)
    
    agent = MockWorkflowAgent()
    
    # Load simple workflow
    workflow = {
        "workflow_id": "test_wf_002",
        "name": "Two-Step Workflow",
        "steps": [
            {
                "step_id": "step_01",
                "operation": "extract_topic",
                "executor": "self",
                "input_mapping": {"question": "workflow.input.question"}
            },
            {
                "step_id": "step_02",
                "operation": "get_article_summary",
                "executor": "discover",
                "discovery_query": {
                    "operation": "get_article_summary",
                    "selection_criteria": "cheapest"
                },
                "depends_on": ["step_01"],
                "input_mapping": {"topic": "step_01.result.topic"}
            }
        ]
    }
    
    agent.workflow_engine.load_workflow(workflow)
    
    print("\n💰 Estimating workflow...")
    
    estimate = await agent.workflow_engine.estimate_workflow(
        workflow_input={"question": "What is coffee?"}
    )
    
    print(f"\n✅ Estimate:")
    print(f"   Total cost: ${estimate['estimated_cost']:.3f}")
    print(f"   Total time: {estimate['estimated_time']:.1f}s")
    print(f"   Steps: {estimate['step_count']}")
    print(f"\n   Breakdown:")
    for item in estimate['breakdown']:
        print(f"     {item['step_id']}: ${item['estimated_cost']:.3f}")
    
    assert estimate['step_count'] == 2
    print("\n✅ TEST 2 PASSED")


async def test_execute_simple_workflow():
    """Test 3: Execute simple workflow."""
    print("\n" + "="*60)
    print("TEST 3: Execute Simple Workflow")
    print("="*60)
    
    agent = MockWorkflowAgent()
    
    workflow = {
        "workflow_id": "test_wf_003",
        "name": "Extract Topic Workflow",
        "steps": [
            {
                "step_id": "step_01",
                "operation": "extract_topic",
                "executor": "self",
                "input_mapping": {"question": "workflow.input.question"}
            }
        ]
    }
    
    agent.workflow_engine.load_workflow(workflow)
    
    print("\n🚀 Executing workflow...")
    
    result = await agent.workflow_engine.execute_workflow(
        workflow_input={"question": "What is machine learning?"},
        budget=1.0
    )
    
    print(f"\n✅ Workflow completed:")
    print(f"   Status: {result['status']}")
    print(f"   Result: {result['result']}")
    print(f"   Cost: ${result['cost_summary']['actual_cost']:.3f}")
    print(f"   Steps executed: {len(result['execution_log'])}")
    
    assert result['status'] == "completed"
    print("\n✅ TEST 3 PASSED")


async def test_workflow_with_dependencies():
    """Test 4: Execute workflow with dependencies."""
    print("\n" + "="*60)
    print("TEST 4: Workflow with Dependencies")
    print("="*60)
    
    agent = MockWorkflowAgent()
    
    workflow = {
        "workflow_id": "test_wf_004",
        "name": "Multi-Step with Dependencies",
        "steps": [
            {
                "step_id": "step_01",
                "operation": "extract_topic",
                "executor": "self",
                "input_mapping": {"question": "workflow.input.question"}
            },
            {
                "step_id": "step_02",
                "operation": "format_raw_data",
                "executor": "self",
                "depends_on": ["step_01"],
                "input_mapping": {"data": "step_01.result"}
            }
        ]
    }
    
    agent.workflow_engine.load_workflow(workflow)
    
    print("\n🚀 Executing workflow with dependencies...")
    print("   step_02 depends on step_01")
    
    result = await agent.workflow_engine.execute_workflow(
        workflow_input={"question": "What is AI?"},
        budget=1.0
    )
    
    print(f"\n✅ Workflow completed:")
    print(f"   Steps executed: {len(result['execution_log'])}")
    
    # Check execution order
    step_order = [log['step_id'] for log in result['execution_log']]
    print(f"   Execution order: {step_order}")
    
    assert step_order == ["step_01", "step_02"], "step_01 should execute before step_02"
    
    print("\n✅ TEST 4 PASSED")


async def test_budget_tracking():
    """Test 5: Budget tracking during execution."""
    print("\n" + "="*60)
    print("TEST 5: Budget Tracking")
    print("="*60)
    
    agent = MockWorkflowAgent()
    
    workflow = {
        "workflow_id": "test_wf_005",
        "name": "Budget Test",
        "steps": [
            {
                "step_id": "step_01",
                "operation": "extract_topic",
                "executor": "self",
                "input_mapping": {"question": "workflow.input.question"}
            }
        ]
    }
    
    agent.workflow_engine.load_workflow(workflow)
    
    initial_budget = 0.50
    
    print(f"\n💰 Executing with budget: ${initial_budget:.2f}")
    
    result = await agent.workflow_engine.execute_workflow(
        workflow_input={"question": "Test"},
        budget=initial_budget
    )
    
    cost_summary = result['cost_summary']
    
    print(f"\n✅ Budget tracking:")
    print(f"   Total budget: ${cost_summary['total_budget']:.3f}")
    print(f"   Actual cost: ${cost_summary['actual_cost']:.3f}")
    print(f"   Remaining: ${cost_summary['remaining']:.3f}")
    
    assert cost_summary['actual_cost'] <= initial_budget
    assert cost_summary['remaining'] >= 0
    
    print("\n✅ TEST 5 PASSED")


async def run_all_tests():
    """Run all workflow engine tests."""
    print("\n" + "="*60)
    print("WORKFLOW ENGINE TEST SUITE")
    print("="*60)
    
    await test_load_workflow()
    await test_estimate_workflow()
    await test_execute_simple_workflow()
    await test_workflow_with_dependencies()
    await test_budget_tracking()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
