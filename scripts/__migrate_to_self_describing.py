#!/usr/bin/env python3
"""Migrate existing FDO records to include inline self-description."""

import json
import sys
from pathlib import Path

def migrate_fdo_records():
    """Add self_description to existing FDO records."""

    registry_dir = Path("registry/data")
    fdos_dir = registry_dir / "fdos"
    metadata_dir = registry_dir / "metadata"

    if not fdos_dir.exists():
        print(f"❌ FDO directory not found: {fdos_dir}")
        return False

    migrated_count = 0
    skipped_count = 0

    for fdo_file in fdos_dir.glob("*.json"):
        print(f"\n📄 Processing: {fdo_file.name}")

        # Load FDO record
        with open(fdo_file) as f:
            fdo = json.load(f)

        # Skip if already has self_description
        if "self_description" in fdo:
            print(f"   ⏭️  Already has self_description, skipping")
            skipped_count += 1
            continue

        # Check if has metadata_pointer
        if "metadata_pointer" not in fdo:
            print(f"   ⚠️  No metadata_pointer found, skipping")
            skipped_count += 1
            continue

        metadata_pid = fdo["metadata_pointer"]
        metadata_file = metadata_dir / f"{metadata_pid.replace('/', '-')}.json"

        if not metadata_file.exists():
            print(f"   ⚠️  Metadata file not found: {metadata_file}")
            skipped_count += 1
            continue

        # Load metadata
        with open(metadata_file) as f:
            metadata = json.load(f)

        # Create self_description from metadata
        # This is a basic migration - agents should override with proper structure
        content = metadata.get("content", {})

        self_description = {
            "agent_info": {
                "name": fdo.get("kernel_attributes", {}).get("name", "Unknown Agent"),
                "version": content.get("version", "1.0.0"),
                "agent_type": "task",  # Default
                "description": content.get("description", "")
            },
            "capabilities": content.get("capabilities", {}),
            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": content.get("dependencies", {}).get("required_libraries", []),
                "resource_requirements": {}
            },
            "agent_attributes": {
                "has_llm": fdo.get("kernel_attributes", {}).get("has_llm", False),
                "autonomy_level": "task",
                "decision_policy": content.get("decision_policy", "hardcoded"),
                "can_delegate": content.get("can_delegate", False)
            }
        }

        # Add self_description to FDO
        fdo["self_description"] = self_description

        # Keep metadata_pointer for backward compatibility (for now)
        # Will remove in future version

        # Save updated FDO
        with open(fdo_file, 'w') as f:
            json.dump(fdo, f, indent=2)

        print(f"   ✅ Migrated: Added self_description")
        migrated_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Migration complete: {migrated_count} FDOs migrated, {skipped_count} skipped")
    print(f"{'='*60}")

    return True

if __name__ == "__main__":
    success = migrate_fdo_records()
    sys.exit(0 if success else 1)
