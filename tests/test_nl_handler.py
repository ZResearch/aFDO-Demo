"""Tests for Scientific NL Handler aFDO."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os

from agents.nl_handler_scientific.workflow_planner import WorkflowPlanner

# Only import agent if API key available
if os.getenv("OPENAI_API_KEY"):
    from agents.nl_handler_scientific.nl_handler_agent import ScientificNLHandlerAgent


def test_workflow_planner_pdf():
    """Test workflow planning for PDF query."""
    query = "Analyze this research paper"
    workflow = WorkflowPlanner.analyze_query(query, "User wants paper analysis")

    assert "steps" in workflow
    assert len(workflow["steps"]) > 0
    assert any(step["action"] == "extract_pdf" for step in workflow["steps"])


def test_workflow_planner_fair():
    """Test workflow planning for FAIR query."""
    query = "Check FAIR compliance of this dataset"
    workflow = WorkflowPlanner.analyze_query(query, "User wants FAIR check")

    assert any(step["action"] == "assess_fair" for step in workflow["steps"])


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_nl_handler_interpret():
    """Test NL interpretation."""
    handler = ScientificNLHandlerAgent()

    result = await handler.handle_operation(
        operation="interpret_natural_language",
        caller_pid="test",
        parameters={"query": "Can you analyze this research paper?"}
    )

    assert "interpretation" in result
    assert "workflow_plan" in result


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_nl_handler_plan():
    """Test workflow planning."""
    handler = ScientificNLHandlerAgent()

    result = await handler.handle_operation(
        operation="plan_workflow",
        caller_pid="test",
        parameters={"query": "Check if this data is FAIR compliant"}
    )

    assert "workflow" in result
    assert "planner" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
