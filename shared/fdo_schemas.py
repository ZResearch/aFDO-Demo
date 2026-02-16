"""Standard schemas for FDO self-description."""

SELF_DESCRIPTION_SCHEMA = {
    "type": "object",
    "required": ["agent_info", "capabilities", "technical_spec"],
    "properties": {
        "agent_info": {
            "type": "object",
            "required": ["name", "version", "agent_type"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},  # Semver
                "agent_type": {
                    "type": "string",
                    "enum": ["task", "composite", "interface", "planning", "infrastructure"]
                },
                "description": {"type": "string"}  # Only free text field
            }
        },
        "capabilities": {
            "type": "object",
            "patternProperties": {
                "^[a-z_]+$": {  # operation_name
                    "type": "object",
                    "required": ["operation_type", "input_schema", "output_schema"],
                    "properties": {
                        "operation_type": {
                            "type": "string",
                            "enum": [
                                "data_extraction",
                                "data_transformation",
                                "assessment",
                                "synthesis",
                                "query_processing"
                            ]
                        },
                        "input_schema": {"type": "object"},  # JSON Schema
                        "output_schema": {"type": "object"},  # JSON Schema
                        "constraints": {
                            "type": "object",
                            "properties": {
                                "max_input_size": {"type": "integer"},
                                "timeout_seconds": {"type": "integer"},
                                "rate_limit": {"type": "integer"}
                            }
                        },
                        "examples": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["input", "output"],
                                "properties": {
                                    "input": {"type": "object"},
                                    "output": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "technical_spec": {
            "type": "object",
            "required": ["runtime", "dependencies"],
            "properties": {
                "runtime": {
                    "type": "string",
                    "pattern": "^(Python|Node|Java|Go) \\d+\\.\\d+$"
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "resource_requirements": {
                    "type": "object",
                    "properties": {
                        "memory_mb": {"type": "integer"},
                        "cpu_cores": {"type": "number"}
                    }
                }
            }
        },
        "agent_attributes": {
            "type": "object",
            "properties": {
                "has_llm": {"type": "boolean"},
                "autonomy_level": {
                    "type": "string",
                    "enum": ["task", "composite", "planning"]
                },
                "decision_policy": {
                    "type": "string",
                    "enum": ["hardcoded", "autonomous", "delegated", "hybrid"]
                },
                "can_delegate": {"type": "boolean"}
            }
        }
    }
}
