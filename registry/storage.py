"""In-memory storage for FDO Registry System."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from registry.models import (
    FDOProfile, FDOType, Operation, MetadataSchema,
    FDORecord, MetadataRecord
)


class RegistryStorage:
    """In-memory storage for all registries."""

    def __init__(self, storage_file: str = "registry_data.json"):
        """Initialize registries with file persistence."""
        self.storage_file = Path(storage_file)

        self.profiles: Dict[str, FDOProfile] = {}
        self.types: Dict[str, FDOType] = {}
        self.operations: Dict[str, Operation] = {}
        self.schemas: Dict[str, MetadataSchema] = {}
        self.fdo_records: Dict[str, FDORecord] = {}
        self.metadata_records: Dict[str, MetadataRecord] = {}

        # Load existing data if file exists
        self._load_from_file()

    def _load_from_file(self):
        """Load registry data from JSON file."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)

                # Reconstruct Pydantic objects from JSON
                self.profiles = {k: FDOProfile(**v) for k, v in data.get('profiles', {}).items()}
                self.types = {k: FDOType(**v) for k, v in data.get('types', {}).items()}
                self.operations = {k: Operation(**v) for k, v in data.get('operations', {}).items()}
                self.schemas = {k: MetadataSchema(**v) for k, v in data.get('schemas', {}).items()}
                self.fdo_records = {k: FDORecord(**v) for k, v in data.get('fdo_records', {}).items()}
                self.metadata_records = {k: MetadataRecord(**v) for k, v in data.get('metadata_records', {}).items()}

                print(f"📂 Loaded registry from {self.storage_file}")
                print(f"   - {len(self.fdo_records)} FDOs")
                print(f"   - {len(self.operations)} operations")
            except Exception as e:
                print(f"⚠️  Failed to load registry: {e}")

    def _save_to_file(self):
        """Save registry data to JSON file."""
        try:
            data = {
                'profiles': {k: v.dict() for k, v in self.profiles.items()},
                'types': {k: v.dict() for k, v in self.types.items()},
                'operations': {k: v.dict() for k, v in self.operations.items()},
                'schemas': {k: v.dict() for k, v in self.schemas.items()},
                'fdo_records': {k: v.dict() for k, v in self.fdo_records.items()},
                'metadata_records': {k: v.dict() for k, v in self.metadata_records.items()},
                'last_updated': datetime.utcnow().isoformat() + "Z"
            }

            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save registry: {e}")

    # PROFILE OPERATIONS
    def create_profile(self, profile: FDOProfile) -> FDOProfile:
        """Create a new profile."""
        if profile.pid in self.profiles:
            raise ValueError(f"Profile {profile.pid} already exists")
        self.profiles[profile.pid] = profile
        self._save_to_file()
        return profile

    def get_profile(self, pid: str) -> Optional[FDOProfile]:
        """Get profile by PID."""
        return self.profiles.get(pid)

    def list_profiles(self) -> List[FDOProfile]:
        """List all profiles."""
        return list(self.profiles.values())

    # TYPE OPERATIONS
    def create_type(self, fdo_type: FDOType) -> FDOType:
        """Create a new FDO type."""
        if fdo_type.pid in self.types:
            raise ValueError(f"Type {fdo_type.pid} already exists")
        self.types[fdo_type.pid] = fdo_type
        self._save_to_file()
        return fdo_type

    def get_type(self, pid: str) -> Optional[FDOType]:
        """Get type by PID."""
        return self.types.get(pid)

    # OPERATION OPERATIONS
    def create_operation(self, operation: Operation) -> Operation:
        """Create a new operation."""
        if operation.pid in self.operations:
            raise ValueError(f"Operation {operation.pid} already exists")
        self.operations[operation.pid] = operation
        self._save_to_file()
        return operation

    def get_operation(self, pid: str) -> Optional[Operation]:
        """Get operation by PID."""
        return self.operations.get(pid)

    def search_operations(self, name: Optional[str] = None) -> List[Operation]:
        """Search operations by name."""
        if name:
            return [op for op in self.operations.values() if op.name == name]
        return list(self.operations.values())

    # FDO RECORD OPERATIONS
    def create_fdo(self, fdo: FDORecord) -> FDORecord:
        """Create a new FDO record."""
        if fdo.pid in self.fdo_records:
            raise ValueError(f"FDO {fdo.pid} already exists")
        self.fdo_records[fdo.pid] = fdo
        self._save_to_file()
        return fdo

    def get_fdo(self, pid: str) -> Optional[FDORecord]:
        """Get FDO by PID."""
        return self.fdo_records.get(pid)

    def update_fdo(self, pid: str, updates: Dict[str, Any]) -> Optional[FDORecord]:
        """Update FDO record."""
        fdo = self.fdo_records.get(pid)
        if not fdo:
            return None

        for key, value in updates.items():
            if hasattr(fdo, key):
                setattr(fdo, key, value)

        fdo.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_to_file()
        return fdo

    def delete_fdo(self, pid: str) -> bool:
        """Delete FDO record."""
        if pid in self.fdo_records:
            del self.fdo_records[pid]
            self._save_to_file()
            return True
        return False

    def search_fdos(
        self,
        fdo_type: Optional[str] = None,
        operation: Optional[str] = None,
        profile: Optional[str] = None
    ) -> List[FDORecord]:
        """Search FDO records by criteria."""
        results = list(self.fdo_records.values())

        if fdo_type:
            results = [fdo for fdo in results if fdo.fdo_type == fdo_type]

        if operation:
            results = [fdo for fdo in results if operation in fdo.operations]

        if profile:
            results = [fdo for fdo in results if fdo.fdo_profile == profile]

        return results

    # METADATA OPERATIONS
    def create_metadata(self, metadata: MetadataRecord) -> MetadataRecord:
        """Create metadata record."""
        if metadata.pid in self.metadata_records:
            raise ValueError(f"Metadata {metadata.pid} already exists")
        self.metadata_records[metadata.pid] = metadata
        self._save_to_file()
        return metadata

    def get_metadata(self, pid: str) -> Optional[MetadataRecord]:
        """Get metadata by PID."""
        return self.metadata_records.get(pid)
