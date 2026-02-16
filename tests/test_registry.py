"""Tests for FDO Registry System."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from shared.utils import generate_pid, current_timestamp
from registry.storage import RegistryStorage
from registry.models import FDOProfile, FDOType, Operation, FDORecord


def test_create_profile():
    """Test profile creation."""
    storage = RegistryStorage()
    profile = FDOProfile(
        pid=generate_pid(),
        name="test_profile",
        description="Test profile",
        required_attributes=["pid"],
        created_at=current_timestamp()
    )

    result = storage.create_profile(profile)
    assert result.pid == profile.pid
    assert len(storage.profiles) == 1


def test_create_fdo():
    """Test FDO creation."""
    storage = RegistryStorage()
    fdo = FDORecord(
        pid=generate_pid(),
        fdo_type="test_type",
        fdo_profile="test_profile",
        operations=["test_op"],
        metadata_pointer="metadata-pid",
        created_at=current_timestamp(),
        updated_at=current_timestamp()
    )

    result = storage.create_fdo(fdo)
    assert result.pid == fdo.pid
    assert len(storage.fdo_records) == 1


def test_search_fdos_by_operation():
    """Test FDO search by operation."""
    storage = RegistryStorage()

    # Create FDOs with different operations
    fdo1 = FDORecord(
        pid=generate_pid(),
        fdo_type="type1",
        fdo_profile="profile1",
        operations=["analyze_paper", "extract_text"],
        metadata_pointer="meta1",
        created_at=current_timestamp(),
        updated_at=current_timestamp()
    )
    fdo2 = FDORecord(
        pid=generate_pid(),
        fdo_type="type2",
        fdo_profile="profile1",
        operations=["parse_pdf"],
        metadata_pointer="meta2",
        created_at=current_timestamp(),
        updated_at=current_timestamp()
    )

    storage.create_fdo(fdo1)
    storage.create_fdo(fdo2)

    # Search by operation
    results = storage.search_fdos(operation="analyze_paper")
    assert len(results) == 1
    assert results[0].pid == fdo1.pid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
