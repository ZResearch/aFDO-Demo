"""Tests for LLM Endpoint aFDOs."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os

# Skip tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)

from agents.llm_endpoint_gpt4.llm_endpoint_agent import LLMEndpointGPT4Agent
from agents.llm_endpoint_gpt4_mini.llm_endpoint_agent import LLMEndpointGPT4MiniAgent


@pytest.mark.asyncio
async def test_gpt4_generate():
    """Test GPT-4 text generation."""
    agent = LLMEndpointGPT4Agent()

    result = await agent.handle_operation(
        operation="generate_text",
        caller_pid="test",
        parameters={"prompt": "Say 'Hello World' in one sentence."}
    )

    assert "generated_text" in result
    assert "cost" in result
    assert result["cost"] > 0


@pytest.mark.asyncio
async def test_gpt4_summarize():
    """Test GPT-4 summarization."""
    agent = LLMEndpointGPT4Agent()

    text = "Artificial intelligence is transforming many industries. " * 20

    result = await agent.handle_operation(
        operation="summarize",
        caller_pid="test",
        parameters={"text": text, "max_length": 50}
    )

    assert "summary" in result
    assert len(result["summary"]) < len(text)


@pytest.mark.asyncio
async def test_gpt4mini_scientific():
    """Test GPT-4-mini scientific analysis."""
    agent = LLMEndpointGPT4MiniAgent()

    text = "We used a convolutional neural network with 50 layers to classify images."

    result = await agent.handle_operation(
        operation="analyze_scientific_text",
        caller_pid="test",
        parameters={"text": text}
    )

    assert "analysis" in result
    assert "cost" in result
    assert result["cost"] < 0.1  # Should be cheap


@pytest.mark.asyncio
async def test_cost_difference():
    """Test that mini is cheaper than full GPT-4."""
    gpt4 = LLMEndpointGPT4Agent()
    gpt4mini = LLMEndpointGPT4MiniAgent()

    prompt = {"prompt": "Test prompt"}

    r1 = await gpt4.handle_operation("generate_text", "test", prompt)
    r2 = await gpt4mini.handle_operation("generate_text", "test", prompt)

    # Mini should cost less
    assert r2["cost"] < r1["cost"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
