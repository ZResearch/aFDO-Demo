"""Tests for Paper Analyzer aFDO."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)

from agents.paper_analyzer.paper_analyzer_agent import PaperAnalyzerAgent
from agents.paper_analyzer.analysis_templates import AnalysisTemplates

def test_analysis_templates():
    """Test analysis template generation."""
    text = "This is a test paper about machine learning."

    prompt = AnalysisTemplates.get_comprehensive_analysis_prompt(text)
    assert "Main Contribution" in prompt
    assert text in prompt

    method_prompt = AnalysisTemplates.get_methodology_prompt(text)
    assert "methodology" in method_prompt.lower()

@pytest.mark.asyncio
async def test_paper_analyzer_extract_findings():
    """Test key findings extraction."""
    analyzer = PaperAnalyzerAgent()

    text = "Our research shows that neural networks achieve 95% accuracy on the benchmark dataset."

    result = await analyzer.handle_operation(
        operation="extract_key_findings",
        caller_pid="test",
        parameters={"text": text}
    )

    assert "key_findings" in result
    assert "analyzer" in result

@pytest.mark.asyncio
async def test_paper_analyzer_methodology():
    """Test methodology assessment."""
    analyzer = PaperAnalyzerAgent()

    text = "We used a supervised learning approach with cross-validation."

    result = await analyzer.handle_operation(
        operation="assess_methodology",
        caller_pid="test",
        parameters={"text": text}
    )

    assert "methodology_assessment" in result

@pytest.mark.asyncio
async def test_paper_analyzer_performance_tracking():
    """Test performance tracking."""
    analyzer = PaperAnalyzerAgent()

    initial_count = analyzer.performance_stats["total_analyses"]

    text = "Test paper text"
    await analyzer.handle_operation(
        operation="extract_key_findings",
        caller_pid="test",
        parameters={"text": text}
    )

    assert analyzer.performance_stats["total_analyses"] == initial_count + 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
