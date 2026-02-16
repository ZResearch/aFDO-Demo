"""Pydantic models for FDO Registry System."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class FDOProfile(BaseModel):
    """FDO Profile definition."""
    pid: str
    name: str
    description: str
    required_attributes: List[str]
    optional_attributes: List[str] = []
    created_at: str


class FDOType(BaseModel):
    """FDO Type definition."""
    pid: str
    name: str
    profile: str  # Reference to profile PID
    description: str
    metadata_schema_pid: str  # Reference to schema
    created_at: str


class Operation(BaseModel):
    """Operation definition."""
    pid: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    semantics: Optional[Dict[str, Any]] = None
    created_at: str


class MetadataSchema(BaseModel):
    """Metadata schema definition."""
    pid: str
    name: str
    for_type: str  # Which FDO type this schema is for
    schema: Dict[str, Any]  # JSON Schema
    created_at: str


class FDORecord(BaseModel):
    """FDO Record (agent or metadata)."""
    pid: str
    fdo_type_pid: str  # PID reference to type
    fdo_profile_pid: str  # PID reference to profile
    operation_pids: List[str] = []  # List of operation PIDs this FDO can perform
    metadata_pointer: Optional[str] = None  # PID of associated metadata (deprecated, kept for compatibility)
    # Inline self-description (NEW - replaces external metadata_pointer)
    self_description: Optional[Dict[str, Any]] = None
    # Activity log supports both old (list) and new (dict with calls_made/calls_received) formats
    activity_log: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]] = Field(default_factory=dict)
    kernel_attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    # Heartbeat and lifecycle tracking
    status: Optional[str] = 'active'  # 'active', 'inactive', 'unknown'
    last_heartbeat: Optional[float] = None  # Unix timestamp
    inactive_since: Optional[float] = None  # Unix timestamp when marked inactive

    @model_validator(mode='before')
    @classmethod
    def handle_legacy_format(cls, data: Any) -> Any:
        """Handle legacy format where fdo_type/fdo_profile/operations are plain strings."""
        if isinstance(data, dict):
            # Convert old 'fdo_type' to 'fdo_type_pid' if needed
            if 'fdo_type' in data and 'fdo_type_pid' not in data:
                fdo_type = data.pop('fdo_type')
                # If it's not already a PID, assume it's just the type name
                data['fdo_type_pid'] = fdo_type

            # Convert old 'fdo_profile' to 'fdo_profile_pid' if needed
            if 'fdo_profile' in data and 'fdo_profile_pid' not in data:
                fdo_profile = data.pop('fdo_profile')
                # If it's not already a PID, assume it's just the profile name
                data['fdo_profile_pid'] = fdo_profile

            # Convert old 'operations' to 'operation_pids' if needed
            if 'operations' in data and 'operation_pids' not in data:
                operations = data.pop('operations')
                # If they're not already PIDs, assume they're just operation names
                data['operation_pids'] = operations if operations else []

        return data

    @property
    def fdo_type(self) -> str:
        """Get type name from PID for backward compatibility."""
        # Extract type name from PID like "21.T11148/type-natural-language-handler"
        # or just return the PID if it doesn't match expected format
        if '/' in self.fdo_type_pid:
            type_part = self.fdo_type_pid.split('/')[-1]
            if type_part.startswith('type-'):
                return type_part.replace('type-', '')
            return type_part
        return self.fdo_type_pid

    @property
    def fdo_profile(self) -> str:
        """Get profile name from PID for backward compatibility."""
        if '/' in self.fdo_profile_pid:
            profile_part = self.fdo_profile_pid.split('/')[-1]
            if profile_part.startswith('profile-'):
                return profile_part.replace('profile-', '')
            return profile_part
        return self.fdo_profile_pid

    @property
    def operations(self) -> List[str]:
        """Get operation names from PIDs for backward compatibility."""
        result = []
        for pid in self.operation_pids:
            if '/' in pid:
                op_part = pid.split('/')[-1]
                # Look for 'op-' anywhere in the string
                if '-op-' in op_part:
                    # Extract the part after '-op-'
                    operation_name = op_part.split('-op-', 1)[1]
                    result.append(operation_name)
                elif op_part.startswith('op-'):
                    result.append(op_part.replace('op-', '', 1))
                else:
                    result.append(op_part)
            else:
                result.append(pid)
        return result


class MetadataRecord(BaseModel):
    """Metadata Record."""
    pid: str
    associated_fdo: str  # PID of the FDO this metadata describes
    content: Dict[str, Any]
    created_at: str
    updated_at: str
    schema_version: str = "1.0.0"
    created_by: Optional[str] = None  # PID of creator
    provenance: Optional[Dict[str, Any]] = None
    semantic_links: Optional[List[Dict[str, str]]] = None
    license: Optional[str] = "research-use"


class DOIPRequest(BaseModel):
    """DOIP request message."""
    protocol_version: str = "2.0"
    operation: str  # e.g., "0.DOIP/Op.Create"
    target_pid: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DOIPResponse(BaseModel):
    """DOIP response message."""
    protocol_version: str = "2.0"
    status: str  # "success" or "error"
    message: Optional[str] = None
    data: Optional[Any] = None
