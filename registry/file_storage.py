"""File-based storage for FDO Registry System."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    FDOProfile, FDOType, Operation, MetadataSchema,
    FDORecord, MetadataRecord
)


class FileBasedStorage:
    """File-based storage for FDO Registry with individual files."""

    def __init__(self, base_dir: str = "registry/data"):
        """Initialize file-based storage."""
        self.base_dir = Path(base_dir)

        # Create directory structure
        self.profiles_dir = self.base_dir / "profiles"
        self.types_dir = self.base_dir / "types"
        self.operations_dir = self.base_dir / "operations"
        self.schemas_dir = self.base_dir / "schemas"
        self.fdos_dir = self.base_dir / "fdos"
        self.metadata_dir = self.base_dir / "metadata"

        for directory in [
            self.profiles_dir, self.types_dir, self.operations_dir,
            self.schemas_dir, self.fdos_dir, self.metadata_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        # Index file for fast lookups
        self.index_file = self.base_dir / "index.json"
        self.index = self._load_index()

        print(f"📂 File-based registry initialized at {self.base_dir}")

    def _load_index(self) -> Dict[str, str]:
        """Load PID → filepath index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_index(self):
        """Save PID → filepath index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _sanitize_filename(self, pid: str) -> str:
        """Convert PID to safe filename."""
        # Replace / with - and remove special chars
        return pid.replace('/', '-').replace(':', '-')

    def _save_object(self, obj: Any, directory: Path, pid: str):
        """Save object to file."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = directory / filename

        with open(filepath, 'w') as f:
            json.dump(obj.dict(), f, indent=2)

        # Update index - path should be relative to base_dir
        self.index[pid] = str(filepath.relative_to(self.base_dir))
        self._save_index()

    def _load_object(self, filepath: Path, model_class):
        """Load object from file."""
        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return model_class(**data)
        except Exception as e:
            print(f"⚠️  Failed to load {filepath}: {e}")
            return None

    def _delete_object(self, directory: Path, pid: str):
        """Delete object file."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = directory / filename

        if filepath.exists():
            filepath.unlink()

        # Update index
        if pid in self.index:
            del self.index[pid]
            self._save_index()

    def _list_objects(self, directory: Path, model_class) -> List[Any]:
        """List all objects in directory."""
        objects = []
        for filepath in directory.glob("*.json"):
            obj = self._load_object(filepath, model_class)
            if obj:
                objects.append(obj)
        return objects

    # PROFILE OPERATIONS
    def create_profile(self, profile: FDOProfile) -> FDOProfile:
        """Create profile."""
        filepath = self.profiles_dir / (self._sanitize_filename(profile.pid) + ".json")
        if filepath.exists():
            raise ValueError(f"Profile {profile.pid} already exists")

        self._save_object(profile, self.profiles_dir, profile.pid)
        print(f"✅ Profile saved: {filepath.name}")
        return profile

    def get_profile(self, pid: str) -> Optional[FDOProfile]:
        """Get profile by PID."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.profiles_dir / filename
        return self._load_object(filepath, FDOProfile)

    def list_profiles(self) -> List[FDOProfile]:
        """List all profiles."""
        return self._list_objects(self.profiles_dir, FDOProfile)

    # TYPE OPERATIONS
    def create_type(self, fdo_type: FDOType) -> FDOType:
        """Create type."""
        filepath = self.types_dir / (self._sanitize_filename(fdo_type.pid) + ".json")
        if filepath.exists():
            raise ValueError(f"Type {fdo_type.pid} already exists")

        self._save_object(fdo_type, self.types_dir, fdo_type.pid)
        print(f"✅ Type saved: {filepath.name}")
        return fdo_type

    def get_type(self, pid: str) -> Optional[FDOType]:
        """Get type by PID."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.types_dir / filename
        return self._load_object(filepath, FDOType)

    def list_types(self) -> List[FDOType]:
        """List all types."""
        return self._list_objects(self.types_dir, FDOType)

    # OPERATION OPERATIONS
    def create_operation(self, operation: Operation) -> Operation:
        """Create operation."""
        filepath = self.operations_dir / (self._sanitize_filename(operation.pid) + ".json")
        if filepath.exists():
            raise ValueError(f"Operation {operation.pid} already exists")

        self._save_object(operation, self.operations_dir, operation.pid)
        print(f"✅ Operation saved: {filepath.name}")
        return operation

    def update_operation(self, pid: str, operation: Operation) -> Optional[Operation]:
        """Update existing operation."""
        filepath = self.operations_dir / (self._sanitize_filename(pid) + ".json")
        if not filepath.exists():
            return None

        self._save_object(operation, self.operations_dir, pid)
        print(f"✅ Operation updated: {filepath.name}")
        return operation

    def get_operation(self, pid: str) -> Optional[Operation]:
        """Get operation by PID."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.operations_dir / filename
        return self._load_object(filepath, Operation)

    def search_operations(self, name: Optional[str] = None) -> List[Operation]:
        """Search operations."""
        operations = self._list_objects(self.operations_dir, Operation)
        if name:
            return [op for op in operations if op.name == name]
        return operations

    # SCHEMA OPERATIONS
    def create_schema(self, schema: MetadataSchema) -> MetadataSchema:
        """Create metadata schema."""
        filepath = self.schemas_dir / (self._sanitize_filename(schema.pid) + ".json")
        if filepath.exists():
            raise ValueError(f"Schema {schema.pid} already exists")

        self._save_object(schema, self.schemas_dir, schema.pid)
        print(f"✅ Schema saved: {filepath.name}")
        return schema

    def get_schema(self, pid: str) -> Optional[MetadataSchema]:
        """Get schema by PID."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.schemas_dir / filename
        return self._load_object(filepath, MetadataSchema)

    # FDO RECORD OPERATIONS
    def create_fdo(self, fdo: FDORecord) -> FDORecord:
        """Create or update FDO record (upsert)."""
        filepath = self.fdos_dir / (self._sanitize_filename(fdo.pid) + ".json")
        action = "updated" if filepath.exists() else "created"

        self._save_object(fdo, self.fdos_dir, fdo.pid)
        print(f"✅ FDO {action}: {filepath.name}")
        return fdo

    def get_fdo(self, pid: str) -> Optional[FDORecord]:
        """Get FDO by PID."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.fdos_dir / filename
        return self._load_object(filepath, FDORecord)

    def update_fdo(self, pid: str, updates: Dict[str, Any]) -> Optional[FDORecord]:
        """Update FDO record."""
        fdo = self.get_fdo(pid)
        if not fdo:
            return None

        for key, value in updates.items():
            if hasattr(fdo, key):
                setattr(fdo, key, value)

        fdo.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_object(fdo, self.fdos_dir, pid)
        return fdo

    def delete_fdo(self, pid: str) -> bool:
        """Delete FDO record."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.fdos_dir / filename

        if filepath.exists():
            self._delete_object(self.fdos_dir, pid)
            return True
        return False

    def search_fdos(
        self,
        fdo_type: Optional[str] = None,
        operation: Optional[str] = None,
        profile: Optional[str] = None
    ) -> List[FDORecord]:
        """Search FDO records."""
        fdos = self._list_objects(self.fdos_dir, FDORecord)

        if fdo_type:
            fdos = [fdo for fdo in fdos if fdo.fdo_type == fdo_type]

        if operation:
            # Normalize operation name for comparison (handle both underscores and hyphens)
            normalized_op = operation.replace('_', '-')
            fdos = [
                fdo for fdo in fdos
                if normalized_op in [op.replace('_', '-') for op in fdo.operations]
            ]

        if profile:
            fdos = [fdo for fdo in fdos if fdo.fdo_profile == profile]

        return fdos

    # METADATA OPERATIONS
    def create_metadata(self, metadata: MetadataRecord) -> MetadataRecord:
        """Create or update metadata record (upsert)."""
        filepath = self.metadata_dir / (self._sanitize_filename(metadata.pid) + ".json")
        action = "updated" if filepath.exists() else "created"

        self._save_object(metadata, self.metadata_dir, metadata.pid)
        print(f"✅ Metadata {action}: {filepath.name}")
        return metadata

    def get_metadata(self, pid: str) -> Optional[MetadataRecord]:
        """Get metadata by PID."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.metadata_dir / filename
        return self._load_object(filepath, MetadataRecord)

    def delete_metadata(self, pid: str) -> bool:
        """Delete metadata record."""
        filename = self._sanitize_filename(pid) + ".json"
        filepath = self.metadata_dir / filename

        if filepath.exists():
            filepath.unlink()
            print(f"🗑️  Metadata deleted: {filename}")
            return True
        return False

    # TYPE OPERATIONS
    def get_type(self, type_pid: str) -> Optional[Dict[str, Any]]:
        """Get type FDO record.

        Args:
            type_pid: Type PID (e.g., "21.T11148/type-document-processor-v1")

        Returns:
            Type FDO record or None
        """
        filename = self._sanitize_filename(type_pid) + ".json"
        filepath = self.types_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            return json.load(f)

    def list_types(self) -> List[Dict[str, Any]]:
        """List all type FDO records."""
        import sys
        sys.stderr.write(f"[FILE_STORAGE] list_types called: types_dir={self.types_dir}\n")
        sys.stderr.flush()
        if not self.types_dir.exists():
            sys.stderr.write(f"[FILE_STORAGE] types_dir does not exist!\n")
            sys.stderr.flush()
            return []

        types = []
        files_found = list(self.types_dir.glob("*.json"))
        sys.stderr.write(f"[FILE_STORAGE] Found {len(files_found)} type files\n")
        sys.stderr.flush()
        for file_path in files_found:
            with open(file_path) as f:
                type_data = json.load(f)
                types.append(type_data)

        sys.stderr.write(f"[FILE_STORAGE] Returning {len(types)} types\n")
        sys.stderr.flush()
        return types

    # PROFILE OPERATIONS
    def get_profile(self, profile_pid: str) -> Optional[Dict[str, Any]]:
        """Get profile FDO record.

        Args:
            profile_pid: Profile PID (e.g., "21.T11148/profile-ai-agent-v1")

        Returns:
            Profile FDO record or None
        """
        filename = self._sanitize_filename(profile_pid) + ".json"
        filepath = self.profiles_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            return json.load(f)

    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all profile FDO records."""
        if not self.profiles_dir.exists():
            return []

        profiles = []
        for file_path in self.profiles_dir.glob("*.json"):
            with open(file_path) as f:
                profiles.append(json.load(f))

        return profiles
