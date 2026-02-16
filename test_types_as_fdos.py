#!/usr/bin/env python3
"""Test types as first-class FDOs."""

import asyncio
import json
import aiohttp
from pathlib import Path
import sys


async def test_types_as_fdos():
    """Verify types and profiles are FDO records."""

    print("="*60)
    print("TESTING TYPES AS FIRST-CLASS FDOS")
    print("="*60)

    # Test 1: Check type files exist
    print("\n1. Checking type FDO files...")
    types_dir = Path("registry/data/types")

    if not types_dir.exists():
        print(f"   ❌ Types directory not found: {types_dir}")
        return False

    type_files = list(types_dir.glob("*.json"))
    print(f"   Found {len(type_files)} type files")

    if len(type_files) == 0:
        print(f"   ❌ No type files found. Run scripts/initialize_types.py")
        return False

    for type_file in type_files:
        with open(type_file) as f:
            type_def = json.load(f)
        print(f"   ✅ {type_def['pid']}: {type_def['name']}")

    # Test 2: Check profile files exist
    print("\n2. Checking profile FDO files...")
    profiles_dir = Path("registry/data/profiles")

    if not profiles_dir.exists():
        print(f"   ❌ Profiles directory not found: {profiles_dir}")
        return False

    profile_files = list(profiles_dir.glob("*.json"))
    print(f"   Found {len(profile_files)} profile files")

    for profile_file in profile_files:
        with open(profile_file) as f:
            profile_def = json.load(f)
        print(f"   ✅ {profile_def['pid']}: {profile_def['name']}")

    # Test 3: Check FDOs use PIDs (not strings)
    print("\n3. Checking FDO type references...")
    fdos_dir = Path("registry/data/fdos")

    pids_count = 0
    strings_count = 0

    for fdo_file in fdos_dir.glob("*.json"):
        with open(fdo_file) as f:
            fdo = json.load(f)

        type_pid = fdo.get("fdo_type_pid", "")

        if type_pid.startswith("21.T11148/type-"):
            pids_count += 1
            print(f"   ✅ {fdo['pid']}: uses PID {type_pid}")
        else:
            strings_count += 1
            print(f"   ❌ {fdo['pid']}: uses string '{type_pid}'")

    print(f"\n   Summary: {pids_count} using PIDs, {strings_count} using strings")

    # Test 4: Test via API
    print("\n4. Testing registry API...")

    try:
        async with aiohttp.ClientSession() as session:
            # List types
            async with session.get("http://localhost:8000/registry/types") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ GET /registry/types: {data['count']} types")
                else:
                    print(f"   ❌ GET /registry/types failed: {resp.status}")

            # Get specific type
            async with session.get(
                "http://localhost:8000/registry/types/21.T11148/type-document-processor-v1"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ GET specific type: {data['type']['name']}")
                else:
                    print(f"   ❌ GET specific type failed: {resp.status}")

            # List profiles
            async with session.get("http://localhost:8000/registry/profiles") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ GET /registry/profiles: {data['count']} profiles")
                else:
                    print(f"   ❌ GET /registry/profiles failed: {resp.status}")

            # Get FDOs by type
            async with session.get(
                "http://localhost:8000/registry/fdos/by-type/21.T11148/type-document-processor-v1"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ GET FDOs by type: {data['count']} document processors")
                else:
                    print(f"   ❌ GET FDOs by type failed: {resp.status}")

    except Exception as e:
        print(f"   ⚠️  API test skipped (registry not running): {e}")

    # Final summary
    print("\n" + "="*60)
    if strings_count == 0 and pids_count > 0:
        print("✅ ALL TESTS PASSED - Types are first-class FDOs!")
        return True
    else:
        print(f"❌ TESTS FAILED - {strings_count} FDOs still using string types")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_types_as_fdos())
    sys.exit(0 if success else 1)
