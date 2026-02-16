"""Templates and utilities for creating new aFDOs."""

from typing import Dict, Any, Optional
from shared.utils import generate_pid, current_timestamp


class aFDOTemplate:
    """Templates for creating new aFDOs."""

    @staticmethod
    def create_fdo_record(
        name: str,
        fdo_type: str,
        operations: list,
        port: int,
        cost: float = 0.0,
        has_llm: bool = False,
        parent_pid: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create FDO record structure.

        Args:
            name: Agent name
            fdo_type: FDO type
            operations: List of operation names
            port: Port number
            cost: Cost per operation
            has_llm: Has built-in LLM
            parent_pid: Parent FDO PID (for forks)
            **kwargs: Additional kernel attributes

        Returns:
            FDO record dictionary
        """
        pid = generate_pid() + f"-{name.lower().replace(' ', '-')}"
        metadata_pid = generate_pid() + f"-metadata-{name.lower().replace(' ', '-')}"

        kernel_attributes = {
            "reputation": 0.85,  # Default for new agents
            "cost": cost,
            "status": "active",
            "has_llm": has_llm,
            "port": port,
            **kwargs
        }

        # Add parent info if forking
        if parent_pid:
            kernel_attributes["parent_pid"] = parent_pid
            kernel_attributes["forked_from"] = parent_pid

        return {
            "pid": pid,
            "fdo_type": fdo_type,
            "fdo_profile": "ai_agent_v1",
            "operations": operations,
            "metadata_pointer": metadata_pid,
            "activity_log": [],
            "kernel_attributes": kernel_attributes,
            "created_at": current_timestamp(),
            "updated_at": current_timestamp()
        }

    @staticmethod
    def create_metadata_record(
        fdo_pid: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        parent_pid: Optional[str] = None,
        improvements: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create metadata record.

        Args:
            fdo_pid: Associated FDO PID
            name: Agent name
            description: Description
            version: Version number
            parent_pid: Parent FDO (for forks)
            improvements: Description of improvements (for forks)
            **kwargs: Additional metadata

        Returns:
            Metadata record dictionary
        """
        metadata_pid = generate_pid() + f"-metadata-{name.lower().replace(' ', '-')}"

        content = {
            "name": name,
            "description": description,
            "version": version,
            "created_at": current_timestamp(),
            **kwargs
        }

        # Add provenance if forking
        if parent_pid:
            content["parent_pid"] = parent_pid
            content["fork_type"] = "improvement"
            if improvements:
                content["improvements"] = improvements

        return {
            "pid": metadata_pid,
            "associated_fdo": fdo_pid,
            "content": content,
            "created_at": current_timestamp(),
            "updated_at": current_timestamp()
        }

    @staticmethod
    def validate_specification(spec: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate aFDO specification.

        Args:
            spec: aFDO specification

        Returns:
            (valid, error_message) tuple
        """
        required_fields = ["name", "fdo_type", "operations", "port"]

        for field in required_fields:
            if field not in spec:
                return False, f"Missing required field: {field}"

        # Validate operations list
        if not isinstance(spec["operations"], list) or len(spec["operations"]) == 0:
            return False, "Operations must be non-empty list"

        # Validate port
        if not isinstance(spec["port"], int) or spec["port"] < 1024 or spec["port"] > 65535:
            return False, "Port must be integer between 1024 and 65535"

        return True, None
