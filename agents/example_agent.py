"""Example agent demonstrating aFDO base class usage."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any
from shared.afdo_base import aFDOBase


class ExampleAgent(aFDOBase):
    """Example agent showing how to use aFDO base class."""

    def __init__(self):
        super().__init__(
            name="Example Agent",
            fdo_type="example_agent",
            operations=["echo", "greet"],
            port=8010,
            cost=0.01,
            has_llm=False
        )

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Example agent demonstrating aFDO framework",
            "version": "1.0.0",
            "author": "IJCAI Demo Team",
            "capabilities": {
                "echo": "Returns the input message",
                "greet": "Returns a greeting"
            }
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "Example Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Example agent demonstrating aFDO framework"
            },

            "capabilities": {
                "echo": {
                    "operation_type": "data_transformation",

                    "input_schema": {
                        "type": "object",
                        "required": ["message"],
                        "properties": {
                            "message": {"type": "string"}
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["echoed", "from"],
                        "properties": {
                            "echoed": {"type": "string"},
                            "from": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 5,
                        "rate_limit": 1000
                    },

                    "examples": []
                },

                "greet": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "default": "friend"
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["greeting", "from"],
                        "properties": {
                            "greeting": {"type": "string"},
                            "from": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 5,
                        "rate_limit": 1000
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [],
                "resource_requirements": {
                    "memory_mb": 64,
                    "cpu_cores": 0.1
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
        """Handle operations."""
        print(f"📥 Received '{operation}' from {caller_pid}")

        if operation == "echo":
            message = parameters.get("message", "")
            return {
                "echoed": message,
                "from": self.pid
            }

        elif operation == "greet":
            name = parameters.get("name", "friend")
            return {
                "greeting": f"Hello {name}! I'm {self.name}",
                "from": self.pid
            }

        else:
            raise ValueError(f"Unknown operation: {operation}")


if __name__ == "__main__":
    agent = ExampleAgent()
    agent.run()
