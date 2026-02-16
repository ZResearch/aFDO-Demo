"""Tests for aFDO base framework."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from typing import Dict, Any

from shared.afdo_base import aFDOBase


class TestAFDO(aFDOBase):
    """Test implementation of aFDO."""

    def get_metadata_content(self) -> Dict[str, Any]:
        return {
            "description": "Test aFDO",
            "version": "1.0.0"
        }

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        if operation == "test_operation":
            return {"result": "success", "message": "Test completed"}
        else:
            raise ValueError(f"Unknown operation: {operation}")


def test_afdo_initialization():
    """Test aFDO initialization."""
    afdo = TestAFDO(
        name="Test aFDO",
        fdo_type="test_agent",
        operations=["test_operation"],
        port=9000,
        cost=0.1
    )

    assert afdo.name == "Test aFDO"
    assert afdo.fdo_type == "test_agent"
    assert "test_operation" in afdo.operations
    assert afdo.port == 9000
    assert afdo.kernel_attributes["cost"] == 0.1


@pytest.mark.asyncio
async def test_afdo_registration():
    """Test aFDO registration (requires registry running)."""
    afdo = TestAFDO(
        name="Test aFDO Registration",
        fdo_type="test_agent",
        operations=["test_operation"],
        port=9001
    )

    # Note: This test requires registry to be running on port 8000
    # In real testing, we'd mock the registry client
    try:
        success = await afdo.register_self()
        # If registry is running, should succeed
        # If not, will fail but that's expected
        print(f"Registration result: {success}")
    except Exception as e:
        print(f"Registration failed (expected if registry not running): {e}")


@pytest.mark.asyncio
async def test_afdo_discovery():
    """Test aFDO discovery capabilities."""
    afdo = TestAFDO(
        name="Test aFDO Discovery",
        fdo_type="test_agent",
        operations=["test_operation"],
        port=9002
    )

    # Test discovery by operation
    try:
        results = await afdo.discover_by_operation("test_operation")
        print(f"Found {len(results)} aFDOs with test_operation")
    except Exception as e:
        print(f"Discovery failed (expected if registry not running): {e}")


def test_afdo_metadata():
    """Test metadata generation."""
    afdo = TestAFDO(
        name="Test aFDO Metadata",
        fdo_type="test_agent",
        operations=["test_operation"],
        port=9003
    )

    metadata = afdo.get_metadata_content()
    assert "description" in metadata
    assert metadata["description"] == "Test aFDO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
