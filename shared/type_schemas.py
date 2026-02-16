"""Schemas for Type and Profile FDO records."""

TYPE_FDO_SCHEMA = {
    "type": "object",
    "required": ["pid", "name", "category", "expected_capabilities", "version"],
    "properties": {
        "pid": {
            "type": "string",
            "pattern": "^21\\.T11148/type-[a-z-]+-v\\d+$"
        },
        "name": {
            "type": "string",
            "description": "Human-readable type name"
        },
        "category": {
            "type": "string",
            "enum": [
                "data_processor",
                "analyzer",
                "coordinator",
                "interface",
                "infrastructure"
            ]
        },
        "expected_capabilities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of operation names this type must provide"
        },
        "optional_capabilities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of operation names this type may provide"
        },
        "version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+\\.\\d+$"
        },
        "description": {
            "type": "string"
        },
        "supersedes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of type PIDs this version supersedes"
        },
        "created_at": {
            "type": "string",
            "format": "date-time"
        }
    }
}

PROFILE_FDO_SCHEMA = {
    "type": "object",
    "required": ["pid", "name", "required_fields", "version"],
    "properties": {
        "pid": {
            "type": "string",
            "pattern": "^21\\.T11148/profile-[a-z-]+-v\\d+$"
        },
        "name": {
            "type": "string",
            "description": "Human-readable profile name"
        },
        "required_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Required fields in FDO records using this profile"
        },
        "optional_fields": {
            "type": "array",
            "items": {"type": "string"}
        },
        "field_schemas": {
            "type": "object",
            "description": "JSON Schema for each field",
            "patternProperties": {
                "^[a-z_]+$": {
                    "type": "object"
                }
            }
        },
        "version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+\\.\\d+$"
        },
        "description": {
            "type": "string"
        },
        "supersedes": {
            "type": "array",
            "items": {"type": "string"}
        },
        "created_at": {
            "type": "string",
            "format": "date-time"
        }
    }
}
