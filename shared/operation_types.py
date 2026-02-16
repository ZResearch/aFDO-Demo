"""Standard operation types vocabulary."""

OPERATION_TYPES = {
    "data_extraction": {
        "category": "extraction",
        "input_type": "binary_data",
        "output_type": "structured_data"
    },
    "data_transformation": {
        "category": "transformation",
        "input_type": "structured_data",
        "output_type": "structured_data"
    },
    "assessment": {
        "category": "evaluation",
        "input_type": "structured_data",
        "output_type": "score"
    },
    "synthesis": {
        "category": "generation",
        "input_type": "structured_data",
        "output_type": "structured_data"
    },
    "query_processing": {
        "category": "interpretation",
        "input_type": "text",
        "output_type": "structured_data"
    }
}

# Standard schema format for operations
OPERATION_SCHEMA_TEMPLATE = {
    "operation_id": "string",  # Unique identifier
    "operation_type": "string",  # From OPERATION_TYPES
    "input_schema": {},  # JSON Schema
    "output_schema": {},  # JSON Schema
    "constraints": {},  # Operational constraints
    "examples": []  # Example inputs/outputs
}
