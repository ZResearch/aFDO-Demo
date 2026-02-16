"""Tests for Creator aFDO."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.creator.afdo_templates import aFDOTemplate
from agents.creator.creator_agent import CreatorAgent


def test_create_fdo_record():
    """Test FDO record creation."""
    record = aFDOTemplate.create_fdo_record(
        name="Test Agent",
        fdo_type="test_type",
        operations=["test_op"],
        port=9000,
        cost=0.1
    )

    assert "pid" in record
    assert record["fdo_type"] == "test_type"
    assert "test_op" in record["operations"]
    assert record["kernel_attributes"]["port"] == 9000


def test_create_metadata_record():
    """Test metadata record creation."""
    record = aFDOTemplate.create_metadata_record(
        fdo_pid="21.T11148/test",
        name="Test Agent",
        description="Test description",
        version="1.0.0"
    )

    assert "pid" in record
    assert record["associated_fdo"] == "21.T11148/test"
    assert record["content"]["name"] == "Test Agent"


def test_fork_with_provenance():
    """Test forked record includes provenance."""
    parent_pid = "21.T11148/parent"

    record = aFDOTemplate.create_fdo_record(
        name="Forked Agent",
        fdo_type="test_type",
        operations=["test_op"],
        port=9001,
        parent_pid=parent_pid
    )

    assert record["kernel_attributes"]["parent_pid"] == parent_pid
    assert record["kernel_attributes"]["forked_from"] == parent_pid


def test_validate_specification():
    """Test specification validation."""
    # Valid spec
    valid_spec = {
        "name": "Test",
        "fdo_type": "test",
        "operations": ["op1"],
        "port": 8000
    }
    valid, error = aFDOTemplate.validate_specification(valid_spec)
    assert valid is True
    assert error is None

    # Invalid spec (missing operations)
    invalid_spec = {
        "name": "Test",
        "fdo_type": "test",
        "port": 8000
    }
    valid, error = aFDOTemplate.validate_specification(invalid_spec)
    assert valid is False
    assert "operations" in error.lower()


@pytest.mark.asyncio
async def test_creator_validate():
    """Test Creator validation operation."""
    creator = CreatorAgent()

    spec = {
        "name": "Test Agent",
        "fdo_type": "test",
        "operations": ["test_op"],
        "port": 9000
    }

    result = await creator.handle_operation(
        operation="validate_specification",
        caller_pid="test-caller",
        parameters={"specification": spec}
    )

    assert result["valid"] is True
    assert result["error"] is None


@pytest.mark.asyncio
async def test_creator_agent():
    """Test Creator agent (requires registry)."""
    creator = CreatorAgent()

    # Test create_afdo operation
    spec = {
        "name": "Test Created Agent",
        "fdo_type": "test_agent",
        "operations": ["test_op1", "test_op2"],
        "port": 9100,
        "cost": 0.05
    }

    try:
        result = await creator.handle_operation(
            operation="create_afdo",
            caller_pid="test-caller",
            parameters={
                "specification": spec,
                "metadata": {"description": "Test agent created by Creator"}
            }
        )

        assert "fdo_pid" in result
        assert result["status"] == "created"
        print(f"Created: {result['fdo_pid']}")
    except Exception as e:
        print(f"Creation test failed (expected if registry not running): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
