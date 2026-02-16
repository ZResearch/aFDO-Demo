#!/usr/bin/env python3
"""Initialize standard type and profile FDO records."""

import json
from pathlib import Path
from datetime import datetime


def create_standard_types():
    """Create standard type FDO records."""

    types_dir = Path("registry/data/types")
    types_dir.mkdir(parents=True, exist_ok=True)

    types = [
        {
            "pid": "21.T11148/type-document-processor-v1",
            "name": "Document Processor",
            "category": "data_processor",
            "expected_capabilities": ["extract_text"],
            "optional_capabilities": ["extract_metadata", "extract_images", "extract_tables", "extract_first_page"],
            "version": "1.0.0",
            "description": "Agents that process documents (PDF, Word, etc.) to extract content",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-text-analyzer-v1",
            "name": "Text Analyzer",
            "category": "analyzer",
            "expected_capabilities": ["analyze_text"],
            "optional_capabilities": ["summarize", "extract_entities"],
            "version": "1.0.0",
            "description": "Agents that analyze text content using LLMs or NLP",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-quality-assessor-v1",
            "name": "Quality Assessor",
            "category": "analyzer",
            "expected_capabilities": ["assess_fairness"],
            "optional_capabilities": ["score_metadata", "validate_structure", "suggest_improvements"],
            "version": "1.0.0",
            "description": "Agents that assess data quality, FAIR compliance, or metadata completeness",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-workflow-coordinator-v1",
            "name": "Workflow Coordinator",
            "category": "coordinator",
            "expected_capabilities": [],  # Coordinators have domain-specific operations
            "optional_capabilities": [],
            "version": "1.0.0",
            "description": "Composite agents that coordinate multi-step workflows by discovering and hiring services",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-user-interface-v1",
            "name": "User Interface",
            "category": "interface",
            "expected_capabilities": ["receive_user_input"],
            "optional_capabilities": ["interpret_natural_language", "display_message", "plan_workflow", "execute_workflow"],
            "version": "1.0.0",
            "description": "Agents that handle user interaction and input processing",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-llm-service-v1",
            "name": "LLM Service",
            "category": "data_processor",
            "expected_capabilities": ["generate_text"],
            "optional_capabilities": ["summarize", "analyze_text", "answer_question", "analyze_scientific_text", "extract_entities", "classify"],
            "version": "1.0.0",
            "description": "Agents that provide LLM-based text generation and analysis",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-agent-creator-v1",
            "name": "Agent Creator",
            "category": "infrastructure",
            "expected_capabilities": ["create_afdo"],
            "optional_capabilities": ["validate_specification", "fork_afdo", "register_operation"],
            "version": "1.0.0",
            "description": "Infrastructure agents that create and register new aFDO agents",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-data-source-v1",
            "name": "Data Source",
            "category": "data_provider",
            "expected_capabilities": [],  # Varies by source
            "optional_capabilities": [
                "search",
                "get_data",
                "query"
            ],
            "version": "1.0.0",
            "description": "Agents that fetch data from external APIs (Wikipedia, ArXiv, databases, etc.)",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        {
            "pid": "21.T11148/type-fact-checker-v1",
            "name": "Fact Checker",
            "category": "coordinator",
            "expected_capabilities": ["verify_fact"],
            "optional_capabilities": [
                "cross_validate",
                "check_claim",
                "assess_credibility"
            ],
            "version": "1.0.0",
            "description": "Agents that verify factual claims through multi-source validation and evidence synthesis",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    ]

    created_count = 0

    for type_def in types:
        pid = type_def["pid"]
        filename = f"{pid.replace('/', '-')}.json"
        filepath = types_dir / filename

        with open(filepath, 'w') as f:
            json.dump(type_def, f, indent=2)

        print(f"✅ Created type: {pid}")
        created_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Created {created_count} type definitions")
    print(f"{'='*60}")

    return created_count


def create_standard_profiles():
    """Create standard profile FDO records."""

    profiles_dir = Path("registry/data/profiles")
    profiles_dir.mkdir(parents=True, exist_ok=True)

    profiles = [
        {
            "pid": "21.T11148/profile-ai-agent-v1",
            "name": "AI Agent Profile",
            "required_fields": [
                "pid",
                "fdo_type_pid",
                "fdo_profile_pid",
                "self_description",
                "activity_log",
                "kernel_attributes"
            ],
            "optional_fields": [
                "economic_attributes",
                "reputation",
                "metadata_pointer"
            ],
            "field_schemas": {
                "pid": {
                    "type": "string",
                    "pattern": "^21\\.T11148/afdo-[a-z-]+(-[0-9]+)?$"
                },
                "fdo_type_pid": {
                    "type": "string",
                    "pattern": "^21\\.T11148/type-[a-z-]+-v\\d+$"
                },
                "fdo_profile_pid": {
                    "type": "string",
                    "pattern": "^21\\.T11148/profile-[a-z-]+-v\\d+$"
                },
                "self_description": {
                    "type": "object"
                },
                "activity_log": {
                    "type": "object",
                    "properties": {
                        "calls_made": {"type": "array"},
                        "calls_received": {"type": "array"}
                    }
                },
                "kernel_attributes": {
                    "type": "object",
                    "required": ["port", "endpoint", "protocol", "status"],
                    "properties": {
                        "port": {"type": "integer"},
                        "endpoint": {"type": "string"},
                        "protocol": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            },
            "version": "1.0.0",
            "description": "Standard profile for autonomous AI agents in the aFDO system",
            "supersedes": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    ]

    created_count = 0

    for profile_def in profiles:
        pid = profile_def["pid"]
        filename = f"{pid.replace('/', '-')}.json"
        filepath = profiles_dir / filename

        with open(filepath, 'w') as f:
            json.dump(profile_def, f, indent=2)

        print(f"✅ Created profile: {pid}")
        created_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Created {created_count} profile definitions")
    print(f"{'='*60}")

    return created_count


if __name__ == "__main__":
    print("Initializing Type and Profile FDO Records...")
    print("="*60)

    types_count = create_standard_types()
    profiles_count = create_standard_profiles()

    print(f"\n🎉 Initialization complete!")
    print(f"   Types: {types_count}")
    print(f"   Profiles: {profiles_count}")
