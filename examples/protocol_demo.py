#!/usr/bin/env python3
"""
Protocol Demo - Cost Negotiation & Workflow Execution

This script demonstrates the protocol system with simple examples.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.protocols import (
    NegotiationProtocol,
    WorkflowEngine,
    CostEstimate,
    NegotiationState
)


class MockAgent:
    """Mock agent for demonstration purposes."""

    def __init__(self, pid: str, name: str, cost: float = 0.05):
        self.pid = pid
        self.name = name
        self.cost = cost
        self.operations = {
            "search": self._search,
            "analyze": self._analyze,
            "summarize": self._summarize
        }

    async def call_other_afdo(self, target_pid: str, operation: str, data: dict):
        """Mock AFDO call."""
        # Simulate helper agent response
        if operation.startswith("__estimate_"):
            return {
                "message_id": "mock123",
                "estimated_cost": 0.03,
                "estimated_time": 5.0,
                "confidence": 0.9,
                "breakdown": [
                    {
                        "component": "helper_search",
                        "agent_pid": target_pid,
                        "cost": 0.03,
                        "description": "Search operation"
                    }
                ]
            }
        else:
            return {
                "result": {"data": "mock result"},
                "status": "success",
                "_cost": 0.03
            }

    async def discover_by_operation(self, operation: str):
        """Mock discovery."""
        return [
            {
                "pid": "21.T11148/mock-helper",
                "name": "Mock Helper",
                "cost": 0.03,
                "queue_size": 0,
                "reputation": 0.9
            }
        ]

    async def _search(self, params):
        """Mock search operation."""
        return {"results": ["result1", "result2"]}

    async def _analyze(self, params):
        """Mock analyze operation."""
        return {"analysis": "mock analysis"}

    async def _summarize(self, params):
        """Mock summarize operation."""
        return {"summary": "mock summary"}


async def demo_negotiation():
    """Demonstrate cost negotiation protocol."""
    print("\n" + "=" * 60)
    print("DEMO 1: Cost Negotiation Protocol")
    print("=" * 60)

    # Create mock agent
    agent = MockAgent("21.T11148/demo-agent", "Demo Agent")
    negotiation = NegotiationProtocol(agent)

    print("\n1️⃣ Phase 1: Request Estimate")
    print("-" * 60)

    estimate = await negotiation.request_estimate(
        target_pid="21.T11148/target-agent",
        operation="search",
        parameters={"query": "machine learning"},
        budget_limit=0.10,
        quality_preference="balanced"
    )

    print(f"✅ Received estimate:")
    print(f"   Cost: ${estimate.estimated_cost:.3f}")
    print(f"   Time: {estimate.estimated_time:.1f}s")
    print(f"   Confidence: {estimate.confidence:.0%}")
    print(f"   Components: {len(estimate.breakdown)}")

    print("\n2️⃣ Phase 2: Approve Estimate")
    print("-" * 60)

    # Get session ID
    session_id = list(negotiation.active_sessions.keys())[0]
    session = negotiation.active_sessions[session_id]

    print(f"Session ID: {session_id}")
    print(f"Session state: {session.state.value}")

    execution_id = await negotiation.approve_estimate(
        session_id=session_id,
        approved=True,
        allocated_budget=estimate.estimated_cost
    )

    print(f"✅ Estimate approved")
    print(f"   Execution ID: {execution_id}")
    print(f"   Allocated budget: ${estimate.estimated_cost:.3f}")

    print("\n3️⃣ Phase 3: Execute with Budget")
    print("-" * 60)

    result = await negotiation.execute_with_budget(
        session_id=session_id,
        operation="search",
        parameters={"query": "machine learning"}
    )

    print(f"✅ Execution completed")
    print(f"   Status: {result.status}")
    print(f"   Actual cost: ${result.actual_cost:.3f}")
    print(f"   Result: {result.result}")

    print("\n📊 Negotiation Summary:")
    print(f"   Total sessions: {len(negotiation.completed_sessions)}")
    print(f"   Final state: {session.state.value}")


async def demo_workflow():
    """Demonstrate workflow engine."""
    print("\n" + "=" * 60)
    print("DEMO 2: Workflow Execution Engine")
    print("=" * 60)

    # Create mock agent
    agent = MockAgent("21.T11148/workflow-agent", "Workflow Agent")
    engine = WorkflowEngine(agent)

    print("\n1️⃣ Create Workflow Definition")
    print("-" * 60)

    workflow = engine.create_workflow(
        name="Research Workflow",
        description="Search, analyze, and summarize papers",
        steps=[
            {
                "step_id": "step_01_search",
                "name": "Search Papers",
                "operation": "search",
                "executor": "self",
                "input_mapping": {
                    "query": "workflow.input.query"
                },
                "depends_on": []
            },
            {
                "step_id": "step_02_analyze",
                "name": "Analyze Results",
                "operation": "analyze",
                "executor": "self",
                "input_mapping": {
                    "data": "step_01_search.result.results"
                },
                "depends_on": ["step_01_search"],
                "on_failure": "retry",
                "max_retries": 2
            },
            {
                "step_id": "step_03_summarize",
                "name": "Create Summary",
                "operation": "summarize",
                "executor": "self",
                "input_mapping": {
                    "analysis": "step_02_analyze.result.analysis"
                },
                "depends_on": ["step_02_analyze"]
            }
        ],
        input_schema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"}
            }
        }
    )

    print(f"✅ Workflow created: {workflow.name}")
    print(f"   ID: {workflow.workflow_id}")
    print(f"   Steps: {len(workflow.steps)}")
    for step in workflow.steps:
        print(f"      - {step.name} (depends on: {step.depends_on or 'none'})")

    print("\n2️⃣ Execute Workflow")
    print("-" * 60)

    result = await engine.execute_workflow(
        workflow=workflow,
        workflow_input={"query": "artificial intelligence"},
        total_budget=0.50
    )

    print(f"\n✅ Workflow completed")
    print(f"   Status: {result['status']}")
    print(f"   Total cost: ${result['cost']:.3f}")
    print(f"   Steps executed: {len(result['steps'])}")

    print("\n📊 Workflow Summary:")
    for step_id, step_data in result['steps'].items():
        print(f"   {step_id}:")
        print(f"      Cost: ${step_data['cost']:.3f}")
        print(f"      Duration: {step_data['duration']:.2f}s")

    print("\n💰 Cost Breakdown:")
    for item in workflow.cost_summary['breakdown']:
        print(f"   {item['step_name']}: ${item['cost']:.3f}")
    print(f"   Total: ${workflow.cost_summary['actual']:.3f}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("aFDO Protocol System Demonstration")
    print("=" * 60)
    print("\nThis demo shows:")
    print("  1. Cost Negotiation Protocol - Recursive cost estimation")
    print("  2. Workflow Engine - Data-driven workflow execution")

    try:
        await demo_negotiation()
        await demo_workflow()

        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
