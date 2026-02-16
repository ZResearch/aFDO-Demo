"""Tests for FAIR Assessor aFDO."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.fair_assessor.fair_criteria import FAIRCriteria
from agents.fair_assessor.fair_assessor_agent import FAIRAssessorAgent


def test_assess_findable_complete():
    """Test Findable assessment with complete metadata."""
    metadata = {
        "pid": "21.T11148/test-123",
        "title": "Test Dataset",
        "description": "Test dataset with PID 21.T11148/test-123",
        "keywords": ["test", "data"],
        "author": "Test Author",
        "indexed_in": "Test Repository"
    }

    score, suggestions = FAIRCriteria.assess_findable(metadata)
    assert score == 1.0  # Perfect score
    assert len(suggestions) == 0


def test_assess_findable_incomplete():
    """Test Findable assessment with incomplete metadata."""
    metadata = {
        "title": "Test Dataset"
    }

    score, suggestions = FAIRCriteria.assess_findable(metadata)
    assert score < 1.0
    assert len(suggestions) > 0


def test_assess_accessible():
    """Test Accessible assessment."""
    metadata = {
        "access_url": "https://example.com/data",
        "metadata_preserved": True
    }

    score, suggestions = FAIRCriteria.assess_accessible(metadata)
    assert score == 1.0


def test_assess_overall():
    """Test overall FAIR assessment."""
    metadata = {
        "pid": "21.T11148/test",
        "title": "Test",
        "description": "Test with pid 21.T11148/test",
        "author": "Author",
        "keywords": ["test"],
        "access_url": "https://example.com",
        "license": "CC-BY",
        "format": "JSON",
        "provenance": "Created 2025",
        "version": "1.0"
    }

    result = FAIRCriteria.assess_overall(metadata)

    assert "overall_score" in result
    assert "principle_scores" in result
    assert "suggestions" in result
    assert 0 <= result["overall_score"] <= 1.0


@pytest.mark.asyncio
async def test_fair_assessor_agent():
    """Test FAIR Assessor agent."""
    agent = FAIRAssessorAgent()

    metadata = {
        "pid": "21.T11148/test-data",
        "title": "Test Dataset",
        "description": "Research data with pid",
        "author": "Researcher",
        "keywords": ["research", "data"],
        "license": "MIT"
    }

    # Test assess_fairness
    result = await agent.handle_operation(
        operation="assess_fairness",
        caller_pid="test-caller",
        parameters={"metadata": metadata}
    )

    assert "overall_score" in result
    assert "compliance_level" in result
    assert "assessed_by" in result
    assert agent.pid in result["assessed_by"]


@pytest.mark.asyncio
async def test_suggest_improvements():
    """Test improvement suggestions."""
    agent = FAIRAssessorAgent()

    # Minimal metadata (should get many suggestions)
    metadata = {"title": "Test"}

    result = await agent.handle_operation(
        operation="suggest_improvements",
        caller_pid="test-caller",
        parameters={"metadata": metadata}
    )

    assert "suggestions" in result
    assert result["total_suggestions"] > 0
    assert "priority" in result["suggestions"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
