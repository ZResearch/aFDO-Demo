#!/usr/bin/env python3
"""Migrate existing FDO records to new activity_log structure."""

import json
from pathlib import Path

def migrate_activity_logs():
    """Update all FDO records to use new activity_log structure."""

    fdos_dir = Path("registry/data/fdos")

    if not fdos_dir.exists():
        print("❌ FDO directory not found: registry/data/fdos")
        return False

    print("🔄 Migrating FDO activity logs to new structure...")
    print(f"   Scanning: {fdos_dir}")
    print()

    migrated = 0
    skipped = 0
    errors = 0

    for fdo_file in fdos_dir.glob("*.json"):
        try:
            # Load FDO
            with open(fdo_file, 'r') as f:
                fdo = json.load(f)

            # Check if activity_log exists and needs migration
            if "activity_log" in fdo:
                activity_log = fdo["activity_log"]

                # If it's already a dict with correct structure, skip
                if isinstance(activity_log, dict) and "calls_made" in activity_log and "calls_received" in activity_log:
                    skipped += 1
                    continue

                # If it's a list (old format), migrate it
                if isinstance(activity_log, list):
                    # Migrate: try to categorize old entries
                    new_activity_log = {
                        "calls_made": [],
                        "calls_received": []
                    }

                    # Try to categorize old log entries
                    for entry in activity_log:
                        if isinstance(entry, dict):
                            entry_type = entry.get("type", "")
                            if entry_type == "call_made":
                                # Convert to new format
                                new_entry = {
                                    "timestamp": entry.get("timestamp", ""),
                                    "target_pid": entry.get("target_pid", "unknown"),
                                    "operation": entry.get("operation", "unknown"),
                                    "status": entry.get("status", "unknown"),
                                    "duration": entry.get("duration", 0.0),
                                    "cost": entry.get("cost", 0.0)
                                }
                                new_activity_log["calls_made"].append(new_entry)
                            elif entry_type == "call_received":
                                # Convert to new format
                                new_entry = {
                                    "timestamp": entry.get("timestamp", ""),
                                    "caller_pid": entry.get("caller_pid", "unknown"),
                                    "operation": entry.get("operation", "unknown"),
                                    "status": entry.get("status", "unknown"),
                                    "duration": entry.get("duration", 0.0)
                                }
                                new_activity_log["calls_received"].append(new_entry)

                    # Update FDO
                    fdo["activity_log"] = new_activity_log

                    # Save
                    with open(fdo_file, 'w') as f:
                        json.dump(fdo, f, indent=2)

                    print(f"   ✅ Migrated: {fdo_file.name}")
                    print(f"      - Calls made: {len(new_activity_log['calls_made'])}")
                    print(f"      - Calls received: {len(new_activity_log['calls_received'])}")
                    migrated += 1

                # If it's something else, reset to empty structure
                else:
                    fdo["activity_log"] = {
                        "calls_made": [],
                        "calls_received": []
                    }

                    with open(fdo_file, 'w') as f:
                        json.dump(fdo, f, indent=2)

                    print(f"   ⚠️  Reset: {fdo_file.name} (unknown format)")
                    migrated += 1

            # If no activity_log field, add it
            else:
                fdo["activity_log"] = {
                    "calls_made": [],
                    "calls_received": []
                }

                with open(fdo_file, 'w') as f:
                    json.dump(fdo, f, indent=2)

                print(f"   ➕ Added: {fdo_file.name}")
                migrated += 1

        except Exception as e:
            print(f"   ❌ Error processing {fdo_file.name}: {e}")
            errors += 1

    print()
    print("=" * 60)
    print("Migration Summary:")
    print(f"  ✅ Migrated: {migrated}")
    print(f"  ⏭️  Skipped (already correct): {skipped}")
    print(f"  ❌ Errors: {errors}")
    print("=" * 60)

    return errors == 0

if __name__ == "__main__":
    import sys
    success = migrate_activity_logs()
    sys.exit(0 if success else 1)
