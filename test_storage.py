#!/usr/bin/env python3
"""Test storage directly."""

import sys
sys.path.insert(0, '.')

from registry.file_storage import FileBasedStorage

# Create storage instance
storage = FileBasedStorage(base_dir="registry/data")

# Test list_types
types = storage.list_types()
print(f"Storage list_types() returned: {len(types)} types")

if types:
    for t in types[:3]:
        print(f"  - {t.get('pid')}")
else:
    print("ERROR: No types found!")
    print(f"Types dir: {storage.types_dir}")
    print(f"Types dir exists: {storage.types_dir.exists()}")
