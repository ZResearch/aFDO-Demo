"""LLM Endpoint aFDO - GPT-4-mini based scientific text service."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
from typing import Dict, Any
from openai import OpenAI
import tiktoken

from shared.afdo_base import aFDOBase


class LLMEndpointGPT4MiniAgent(aFDOBase):
    """
    LLM Endpoint aFDO - GPT-4-mini service.

    Cheaper LLM service specialized for scientific text.
    Other aFDOs call this for cost-effective processing.
    """

    def __init__(self):
        super().__init__(
            name="LLM Endpoint GPT-4-mini",
            fdo_type="21.T11148/type-llm-service-v1",
            operations=[
                "generate_text",
                "summarize",
                "extract_entities",
                "analyze_scientific_text"
            ],
            port=8008,
            cost=0.005,  # per 1K tokens (much cheaper)
            has_llm=True,
            llm_model="mistral:7b",
            specialization="scientific_text"
        )

        # Initialize OpenAI client (supports Ollama via base_url)
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        if not api_key:
            print("⚠️  Warning: OPENAI_API_KEY not set.")
            self.client = None
        else:
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)

        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Cost-effective LLM service specialized for scientific text analysis",
            "version": "2.0.0",
            "agent_role": "llm_service",
            "model": "gpt-4o-mini",
            "provider": "OpenAI",
            "cost_per_1k_tokens": 0.005,
            "specialization": "scientific_text",
            "capabilities": {
                "generate_text": {
                    "description": "Generate scientific text",
                    "estimated_duration": "1-8s",
                    "estimated_cost": "$0.005 per 1K tokens"
                },
                "summarize": {
                    "description": "Summarize research papers and sections",
                    "estimated_duration": "2-12s",
                    "estimated_cost": "$0.01-0.05"
                },
                "extract_entities": {
                    "description": "Extract scientific entities (methods, datasets, metrics)",
                    "estimated_duration": "1-6s",
                    "estimated_cost": "$0.005-0.02"
                },
                "analyze_scientific_text": {
                    "description": "Analyze methodology, findings, and scientific quality",
                    "input_schema": {
                        "text": "scientific text to analyze",
                        "focus": "string (methodology/findings/quality)"
                    },
                    "output_schema": {
                        "analysis": "structured analysis dict",
                        "cost": "float"
                    },
                    "estimated_duration": "3-15s",
                    "estimated_cost": "$0.01-0.08"
                }
            },
            "performance_characteristics": {
                "typical_latency": "1-8s",
                "cost_advantage": "6x cheaper than GPT-4",
                "quality_tradeoff": "suitable for most scientific tasks"
            },
            "recommended_for": [
                "research paper processing",
                "scientific entity extraction",
                "methodology analysis",
                "cost-sensitive workflows"
            ],
            "llm_capable": True
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "LLM Endpoint GPT-4-mini Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Cost-effective LLM service specialized for scientific text analysis"
            },

            "capabilities": {
                "summarize": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "required": ["text"],
                        "properties": {
                            "text": {"type": "string"},
                            "max_length": {
                                "type": "integer",
                                "default": 200
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["summary", "cost"],
                        "properties": {
                            "summary": {"type": "string"},
                            "cost": {"type": "number"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 32000,
                        "timeout_seconds": 60,
                        "rate_limit": 100
                    },

                    "examples": []
                },

                "analyze_scientific_text": {
                    "operation_type": "assessment",

                    "input_schema": {
                        "type": "object",
                        "required": ["text"],
                        "properties": {
                            "text": {"type": "string"},
                            "focus": {
                                "type": "string",
                                "enum": ["methodology", "findings", "quality"],
                                "default": "methodology"
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["analysis", "cost"],
                        "properties": {
                            "analysis": {"type": "object"},
                            "cost": {"type": "number"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 32000,
                        "timeout_seconds": 90,
                        "rate_limit": 100
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [
                    "openai==1.12.0",
                    "tiktoken==0.5.2"
                ],
                "resource_requirements": {
                    "memory_mb": 256,
                    "cpu_cores": 0.5
                }
            },

            "agent_attributes": {
                "has_llm": True,
                "autonomy_level": "task",
                "decision_policy": "hardcoded",
                "can_delegate": False
            }
        }

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost."""
        total_tokens = prompt_tokens + completion_tokens
        return (total_tokens / 1000) * self.kernel_attributes["cost"]

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle LLM operations."""
        if not self.client:
            raise ValueError("OpenAI client not initialized.")

        print(f"🧪 Processing '{operation}' from {caller_pid} (scientific)")

        if operation == "generate_text":
            return await self._generate_text(parameters)
        elif operation == "summarize":
            return await self._summarize(parameters)
        elif operation == "extract_entities":
            return await self._extract_entities(parameters)
        elif operation == "analyze_scientific_text":
            return await self._analyze_scientific_text(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _generate_text(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scientific text."""
        prompt = parameters.get("prompt")
        if not prompt:
            raise ValueError("Missing 'prompt'")

        # Add scientific context
        system_message = "You are a scientific writing assistant. Provide accurate, technical responses."

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=parameters.get("max_tokens", 500),
            temperature=0.7
        )

        result = response.choices[0].message.content
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "generated_text": result,
            "cost": round(cost, 4),
            "model": "gpt-4o-mini",
            "provider": self.pid
        }

    async def _summarize(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize scientific text."""
        text = parameters.get("text")
        if not text:
            raise ValueError("Missing 'text'")

        focus = parameters.get("focus", "general")  # methodology, findings, general

        if focus == "methodology":
            prompt = f"Summarize the methodology described in this text:\n\n{text}"
        elif focus == "findings":
            prompt = f"Summarize the key findings in this text:\n\n{text}"
        else:
            prompt = f"Provide a scientific summary of this text:\n\n{text}"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )

        summary = response.choices[0].message.content
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "summary": summary,
            "focus": focus,
            "cost": round(cost, 4),
            "provider": self.pid
        }

    async def _extract_entities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scientific entities."""
        text = parameters.get("text")
        if not text:
            raise ValueError("Missing 'text'")

        prompt = f"""Extract scientific entities from this text. Include:
- Methods/techniques
- Datasets
- Metrics
- Tools/software

Text: {text}

Return as JSON."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3
        )

        entities = response.choices[0].message.content
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "entities": entities,
            "cost": round(cost, 4),
            "provider": self.pid
        }

    async def _analyze_scientific_text(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scientific text structure."""
        text = parameters.get("text")
        if not text:
            raise ValueError("Missing 'text'")

        prompt = f"""Analyze this scientific text and identify:
1. Type (abstract, methodology, results, discussion)
2. Key claims
3. Evidence provided
4. Limitations mentioned

Text: {text}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5
        )

        analysis = response.choices[0].message.content
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "analysis": analysis,
            "cost": round(cost, 4),
            "provider": self.pid
        }


if __name__ == "__main__":
    agent = LLMEndpointGPT4MiniAgent()
    agent.run()
