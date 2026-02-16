"""Tests for Chat UI aFDO."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.chat_ui.chat_ui_agent import ChatUIAgent

def test_chat_ui_init():
    """Test Chat UI initialization."""
    ui = ChatUIAgent()

    assert ui.name == "Chat UI"
    assert ui.port == 8001
    assert ui.kernel_attributes["has_llm"] is False
    assert "receive_user_input" in ui.operations

@pytest.mark.asyncio
async def test_chat_ui_display():
    """Test display message operation."""
    ui = ChatUIAgent()

    result = await ui.handle_operation(
        operation="display_message",
        caller_pid="test",
        parameters={"message": "Hello, user!"}
    )

    assert result["displayed"] is True
    assert "message" in result

@pytest.mark.asyncio
async def test_chat_ui_metadata():
    """Test metadata content."""
    ui = ChatUIAgent()

    metadata = ui.get_metadata_content()

    assert "ui_endpoint" in metadata
    assert "web_ui" in metadata["interface_type"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
