#!/usr/bin/env python3
"""Test self-describing FDO records."""

import asyncio
import json
import aiohttp
from pathlib import Path
import jsonschema
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from shared.fdo_schemas import SELF_DESCRIPTION_SCHEMA


async def test_self_describing_fdos():
    """Verify FDOs have valid self-description."""

    print("="*60)
    print("TESTING SELF-DESCRIBING FDO RECORDS")
    print("="*60)

    # Test 1: Check FDO files have self_description
    print("\n1. Checking FDO files...")
    fdos_dir = Path("registry/data/fdos")

    if not fdos_dir.exists():
        print(f"   ❌ FDO directory not found: {fdos_dir}")
        return False

    total = 0
    with_self_desc = 0

    for fdo_file in fdos_dir.glob("*.json"):
        total += 1
        with open(fdo_file) as f:
            fdo = json.load(f)

        if "self_description" in fdo and fdo["self_description"]:
            with_self_desc += 1
            print(f"   ✅ {fdo_file.name}: has self_description")
        else:
            print(f"   ❌ {fdo_file.name}: NO self_description")

    print(f"\n   Summary: {with_self_desc}/{total} FDOs have self_description")

    # Test 2: Validate structure
    print("\n2. Validating self_description structure...")

    valid = 0
    invalid = 0

    for fdo_file in fdos_dir.glob("*.json"):
        with open(fdo_file) as f:
            fdo = json.load(f)

        if "self_description" not in fdo or not fdo["self_description"]:
            continue

        try:
            jsonschema.validate(
                instance=fdo["self_description"],
                schema=SELF_DESCRIPTION_SCHEMA
            )
            valid += 1
            print(f"   ✅ {fdo_file.name}: valid structure")
        except jsonschema.ValidationError as e:
            invalid += 1
            print(f"   ❌ {fdo_file.name}: {e.message}")

    print(f"\n   Summary: {valid} valid, {invalid} invalid")

    # Test 3: Test via API
    print("\n3. Testing registry API...")

    try:
        async with aiohttp.ClientSession() as session:
            # Get list of FDOs
            async with session.get("http://localhost:8000/registry/fdos") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    fdos = data.get("fdos", [])

                    if len(fdos) > 0:
                        test_pid = fdos[0]["pid"]

                        # Get self-description
                        async with session.get(
                            f"http://localhost:8000/registry/fdos/{test_pid}/self_description"
                        ) as resp2:
                            if resp2.status == 200:
                                result = await resp2.json()
                                print(f"   ✅ API endpoint works")
                                print(f"   Retrieved self-description for: {test_pid}")
                            else:
                                print(f"   ❌ API returned {resp2.status}")
                    else:
                        print(f"   ⚠️  No FDOs in registry")
                else:
                    print(f"   ❌ Registry API not responding: {resp.status}")
    except Exception as e:
        print(f"   ⚠️  API test skipped (registry not running): {e}")

    # Test 4: Check for operation schemas
    print("\n4. Checking operation schemas...")

    has_schemas = 0
    has_examples = 0

    for fdo_file in fdos_dir.glob("*.json"):
        with open(fdo_file) as f:
            fdo = json.load(f)

        if "self_description" not in fdo or not fdo["self_description"]:
            continue

        capabilities = fdo["self_description"].get("capabilities", {})

        for op_name, op_def in capabilities.items():
            if "input_schema" in op_def and "output_schema" in op_def:
                has_schemas += 1

            if "examples" in op_def and len(op_def["examples"]) > 0:
                has_examples += 1

    print(f"   Operations with schemas: {has_schemas}")
    print(f"   Operations with examples: {has_examples}")

    # Final summary
    print("\n" + "="*60)
    if with_self_desc == total and valid == with_self_desc and invalid == 0:
        print("✅ ALL TESTS PASSED - Self-describing FDOs working!")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   - FDOs with self-description: {with_self_desc}/{total}")
        print(f"   - Valid structures: {valid}/{with_self_desc if with_self_desc > 0 else 'N/A'}")
        print(f"   - Invalid structures: {invalid}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_self_describing_fdos())
    sys.exit(0 if success else 1)
