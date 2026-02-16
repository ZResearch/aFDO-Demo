"""Creator aFDO - Meta-agent that creates and registers new aFDOs."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, Optional
from shared.afdo_base import aFDOBase
from shared.utils import generate_pid, current_timestamp
from agents.creator.afdo_templates import aFDOTemplate


class CreatorAgent(aFDOBase):
    """
    Creator aFDO - Meta-agent with registry write privileges.

    Capabilities:
    - Create new aFDOs from specifications
    - Fork existing aFDOs to new versions
    - Register operations in operation registry
    - Maintain provenance chains

    This is a META-AGENT with special privileges.
    """

    def __init__(self):
        super().__init__(
            name="Creator",
            fdo_type="21.T11148/type-agent-creator-v1",
            operations=[
                "create_afdo",
                "fork_afdo",
                "register_operation",
                "validate_specification"
            ],
            port=8006,
            cost=0.0,  # Meta-agents typically free
            has_llm=False,
            is_meta_agent=True
        )

        self.template = aFDOTemplate()

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Meta-agent that creates and registers new aFDOs",
            "version": "1.0.0",
            "agent_type": "meta_agent",
            "privileges": [
                "create_fdo_records",
                "create_metadata_records",
                "register_operations",
                "maintain_provenance"
            ],
            "capabilities": {
                "create_afdo": "Create new aFDO from specification",
                "fork_afdo": "Fork existing aFDO to improved version",
                "register_operation": "Register new operation in registry",
                "validate_specification": "Validate aFDO specification before creation"
            },
            "llm_capable": False
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "Creator Agent",
                "version": "1.0.0",
                "agent_type": "infrastructure",
                "description": "Meta-agent that creates and registers new aFDOs"
            },

            "capabilities": {
                "create_afdo": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "required": ["specification"],
                        "properties": {
                            "specification": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "fdo_type": {"type": "string"},
                                    "operations": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "port": {"type": "integer"}
                                }
                            },
                            "metadata": {"type": "object"}
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["success", "pid"],
                        "properties": {
                            "success": {"type": "boolean"},
                            "pid": {"type": "string"},
                            "message": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 60,
                        "rate_limit": 10
                    },

                    "examples": []
                },

                "validate_specification": {
                    "operation_type": "assessment",

                    "input_schema": {
                        "type": "object",
                        "required": ["specification"],
                        "properties": {
                            "specification": {"type": "object"}
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["valid"],
                        "properties": {
                            "valid": {"type": "boolean"},
                            "error": {"type": ["string", "null"]},
                            "validated_by": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 10,
                        "rate_limit": 100
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [],
                "resource_requirements": {
                    "memory_mb": 128,
                    "cpu_cores": 0.25
                }
            },

            "agent_attributes": {
                "has_llm": False,
                "autonomy_level": "task",
                "decision_policy": "hardcoded",
                "can_delegate": False
            }
        }

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle creation operations."""
        print(f"🏭 Processing '{operation}' request from {caller_pid}")

        if operation == "create_afdo":
            return await self._create_afdo(caller_pid, parameters)

        elif operation == "fork_afdo":
            return await self._fork_afdo(caller_pid, parameters)

        elif operation == "register_operation":
            return await self._register_operation(parameters)

        elif operation == "validate_specification":
            return await self._validate_specification(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _validate_specification(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate aFDO specification."""
        spec = parameters.get("specification")
        if not spec:
            raise ValueError("Missing 'specification' parameter")

        valid, error = self.template.validate_specification(spec)

        return {
            "valid": valid,
            "error": error,
            "validated_by": self.pid
        }

    async def _create_afdo(
        self,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new aFDO.

        Parameters should include:
        - specification: Dict with name, fdo_type, operations, port, etc.
        - metadata: Dict with description, version, etc.
        """
        spec = parameters.get("specification")
        metadata_spec = parameters.get("metadata", {})

        if not spec:
            raise ValueError("Missing 'specification' parameter")

        # Validate specification
        valid, error = self.template.validate_specification(spec)
        if not valid:
            raise ValueError(f"Invalid specification: {error}")

        print(f"  → Creating new aFDO: {spec['name']}")

        # Create FDO record
        fdo_record = self.template.create_fdo_record(**spec)

        # Create metadata record
        metadata_record = self.template.create_metadata_record(
            fdo_pid=fdo_record["pid"],
            name=spec["name"],
            description=metadata_spec.get("description", f"aFDO: {spec['name']}"),
            version=metadata_spec.get("version", "1.0.0"),
            **metadata_spec
        )

        # Register in registry
        try:
            # Register metadata first
            await self.registry_client.create_metadata(metadata_record)
            print(f"  ✓ Metadata registered: {metadata_record['pid']}")

            # Register FDO
            await self.registry_client.create_fdo(fdo_record)
            print(f"  ✓ FDO registered: {fdo_record['pid']}")

            return {
                "status": "created",
                "fdo_pid": fdo_record["pid"],
                "metadata_pid": metadata_record["pid"],
                "message": f"Successfully created {spec['name']}",
                "created_by": self.pid,
                "requested_by": caller_pid
            }

        except Exception as e:
            print(f"  ✗ Creation failed: {e}")
            raise ValueError(f"Failed to register aFDO: {e}")

    async def _fork_afdo(
        self,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fork existing aFDO to new version.

        Parameters:
        - parent_pid: PID of aFDO to fork
        - improvements: Description of improvements
        - updated_spec: Updated specification (optional, uses parent's if not provided)
        """
        parent_pid = parameters.get("parent_pid")
        improvements = parameters.get("improvements", "Improved version")
        updated_spec = parameters.get("updated_spec", {})

        if not parent_pid:
            raise ValueError("Missing 'parent_pid' parameter")

        print(f"  → Forking aFDO: {parent_pid}")

        # Get parent FDO info
        try:
            parent_info = await self.registry_client.read_fdo(parent_pid)
            parent_data = parent_info.get("data", {})
        except Exception as e:
            raise ValueError(f"Parent FDO not found: {e}")

        # Get parent metadata
        try:
            parent_metadata_pid = parent_data.get("metadata_pointer")
            parent_metadata_info = await self.registry_client.read_metadata(parent_metadata_pid)
            parent_metadata = parent_metadata_info.get("data", {}).get("content", {})
        except:
            parent_metadata = {}

        # Determine new version
        parent_version = parent_metadata.get("version", "1.0.0")
        version_parts = parent_version.split(".")
        new_version = f"{version_parts[0]}.{int(version_parts[1]) + 1}.0"

        # Create forked specification (use parent + updates)
        fork_spec = {
            "name": updated_spec.get("name", parent_metadata.get("name", "Forked Agent")),
            "fdo_type": updated_spec.get("fdo_type", parent_data.get("fdo_type")),
            "operations": updated_spec.get("operations", parent_data.get("operations")),
            "port": updated_spec.get("port", parent_data.get("kernel_attributes", {}).get("port", 8020)),
            "cost": updated_spec.get("cost", parent_data.get("kernel_attributes", {}).get("cost", 0.0)),
            "has_llm": updated_spec.get("has_llm", parent_data.get("kernel_attributes", {}).get("has_llm", False)),
            "parent_pid": parent_pid
        }

        # Inherit reputation but slightly lower (needs to prove itself)
        parent_reputation = parent_data.get("kernel_attributes", {}).get("reputation", 0.85)
        fork_spec["reputation"] = max(0.75, parent_reputation - 0.05)

        # Create forked FDO record
        fdo_record = self.template.create_fdo_record(**fork_spec)

        # Create forked metadata with provenance
        metadata_record = self.template.create_metadata_record(
            fdo_pid=fdo_record["pid"],
            name=fork_spec["name"],
            description=updated_spec.get("description", parent_metadata.get("description", "")),
            version=new_version,
            parent_pid=parent_pid,
            improvements=improvements
        )

        # Register fork
        try:
            await self.registry_client.create_metadata(metadata_record)
            print(f"  ✓ Forked metadata registered: {metadata_record['pid']}")

            await self.registry_client.create_fdo(fdo_record)
            print(f"  ✓ Forked FDO registered: {fdo_record['pid']}")

            return {
                "status": "forked",
                "fdo_pid": fdo_record["pid"],
                "metadata_pid": metadata_record["pid"],
                "parent_pid": parent_pid,
                "version": new_version,
                "improvements": improvements,
                "message": f"Successfully forked to version {new_version}",
                "created_by": self.pid,
                "requested_by": caller_pid
            }

        except Exception as e:
            print(f"  ✗ Fork failed: {e}")
            raise ValueError(f"Failed to fork aFDO: {e}")

    async def _register_operation(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Register new operation in operation registry."""
        operation_spec = parameters.get("operation")
        if not operation_spec:
            raise ValueError("Missing 'operation' parameter")

        # Ensure operation has PID
        if "pid" not in operation_spec:
            operation_spec["pid"] = generate_pid() + f"-op-{operation_spec['name']}"

        # Ensure created_at timestamp
        if "created_at" not in operation_spec:
            operation_spec["created_at"] = current_timestamp()

        try:
            await self.registry_client.create_operation(operation_spec)
            print(f"  ✓ Operation registered: {operation_spec['name']}")

            return {
                "status": "registered",
                "operation_pid": operation_spec["pid"],
                "operation_name": operation_spec["name"],
                "registered_by": self.pid
            }
        except Exception as e:
            raise ValueError(f"Failed to register operation: {e}")


if __name__ == "__main__":
    agent = CreatorAgent()
    agent.run()
