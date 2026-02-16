"""LLM Endpoint aFDO - GPT-4 based general-purpose LLM service."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
from typing import Dict, Any, Optional
from openai import OpenAI
import tiktoken

from shared.afdo_base import aFDOBase


class LLMEndpointGPT4Agent(aFDOBase):
    """
    LLM Endpoint aFDO - GPT-4 service.

    Pure LLM service agent that other aFDOs call for:
    - Text generation
    - Summarization
    - Entity extraction
    - Classification

    This is a SERVICE agent, not an orchestrator.
    """

    def __init__(self):
        super().__init__(
            name="LLM Endpoint GPT-4",
            fdo_type="21.T11148/type-llm-service-v1",
            operations=[
                "generate_text",
                "summarize",
                "extract_entities",
                "classify"
            ],
            port=8007,
            cost=0.03,  # per 1K tokens
            has_llm=True,
            llm_model="mistral:7b"
        )

        # Initialize OpenAI client (supports Ollama via base_url)
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        if not api_key:
            print("⚠️  Warning: OPENAI_API_KEY not set. LLM operations will fail.")
            self.client = None
        else:
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)

        # Token encoder for cost calculation
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "General-purpose LLM service using GPT-4",
            "version": "2.0.0",
            "agent_role": "llm_service",
            "model": "gpt-4o",
            "provider": "OpenAI",
            "cost_per_1k_tokens": 0.03,
            "capabilities": {
                "generate_text": {
                    "description": "Generate text completion from prompt",
                    "input_schema": {
                        "prompt": "string prompt or messages list",
                        "max_tokens": "integer max output tokens (default 500)"
                    },
                    "output_schema": {
                        "text": "generated text string",
                        "tokens_used": "integer total tokens",
                        "cost": "float operation cost"
                    },
                    "estimated_duration": "2-10s",
                    "estimated_cost": "$0.03 per 1K tokens"
                },
                "summarize": {
                    "description": "Summarize long text into concise form",
                    "input_schema": {
                        "text": "text to summarize",
                        "max_length": "integer words (default 200)"
                    },
                    "output_schema": {
                        "summary": "summarized text",
                        "compression_ratio": "float",
                        "cost": "float"
                    },
                    "estimated_duration": "3-15s",
                    "estimated_cost": "$0.05-0.20"
                },
                "extract_entities": {
                    "description": "Extract named entities from text",
                    "input_schema": {
                        "text": "text to analyze",
                        "entity_types": "list of types to extract (optional)"
                    },
                    "output_schema": {
                        "entities": "list of extracted entities with types",
                        "cost": "float"
                    },
                    "estimated_duration": "2-8s",
                    "estimated_cost": "$0.03-0.10"
                },
                "classify": {
                    "description": "Classify text into categories",
                    "input_schema": {
                        "text": "text to classify",
                        "categories": "list of possible categories"
                    },
                    "output_schema": {
                        "category": "predicted category string",
                        "confidence": "float 0-1",
                        "cost": "float"
                    },
                    "estimated_duration": "2-5s",
                    "estimated_cost": "$0.03-0.08"
                }
            },
            "performance_characteristics": {
                "typical_latency": "2-10s depending on length",
                "max_tokens_per_request": 8000,
                "supports_streaming": False,
                "rate_limit": "90K tokens/minute"
            },
            "service_type": "llm_endpoint",
            "specialization": "general_purpose",
            "llm_capable": True
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "LLM Endpoint GPT-4 Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "General-purpose LLM service using GPT-4"
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
                                "default": 200,
                                "minimum": 50,
                                "maximum": 1000
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["summary", "cost"],
                        "properties": {
                            "summary": {"type": "string"},
                            "compression_ratio": {"type": "number"},
                            "cost": {"type": "number"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 32000,
                        "timeout_seconds": 60,
                        "rate_limit": 50
                    },

                    "examples": []
                },

                "generate_text": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "required": ["prompt"],
                        "properties": {
                            "prompt": {"type": "string"},
                            "max_tokens": {
                                "type": "integer",
                                "default": 500,
                                "minimum": 1,
                                "maximum": 4000
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["text", "tokens_used", "cost"],
                        "properties": {
                            "text": {"type": "string"},
                            "tokens_used": {"type": "integer"},
                            "cost": {"type": "number"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 8000,
                        "timeout_seconds": 60,
                        "rate_limit": 50
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

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoder.encode(text))
        except:
            # Fallback: rough estimate
            return len(text) // 4

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate operation cost."""
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
            raise ValueError("OpenAI client not initialized. Set OPENAI_API_KEY.")

        print(f"🤖 Processing '{operation}' from {caller_pid}")

        if operation == "generate_text":
            return await self._generate_text(parameters)

        elif operation == "summarize":
            return await self._summarize(parameters)

        elif operation == "extract_entities":
            return await self._extract_entities(parameters)

        elif operation == "classify":
            return await self._classify(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _generate_text(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text from prompt."""
        prompt = parameters.get("prompt")
        if not prompt:
            raise ValueError("Missing 'prompt' parameter")

        max_tokens = parameters.get("max_tokens", 500)
        temperature = parameters.get("temperature", 0.7)

        # Call OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )

        result_text = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = self._calculate_cost(prompt_tokens, completion_tokens)

        return {
            "generated_text": result_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": round(cost, 4),
            "model": "gpt-4o",
            "provider": self.pid
        }

    async def _summarize(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text."""
        text = parameters.get("text")
        if not text:
            raise ValueError("Missing 'text' parameter")

        max_length = parameters.get("max_length", 200)

        prompt = f"""Summarize the following text in approximately {max_length} words:

{text}

Summary:"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_length * 2,  # Words to tokens approx
            temperature=0.5
        )

        summary = response.choices[0].message.content
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "cost": round(cost, 4),
            "provider": self.pid
        }

    async def _extract_entities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract named entities."""
        text = parameters.get("text")
        if not text:
            raise ValueError("Missing 'text' parameter")

        entity_types = parameters.get("entity_types", ["person", "organization", "location"])

        prompt = f"""Extract the following types of entities from the text: {', '.join(entity_types)}

Text: {text}

Return entities as JSON with format: {{"entity_type": ["entity1", "entity2", ...]}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )

        result = response.choices[0].message.content
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "entities_raw": result,
            "cost": round(cost, 4),
            "provider": self.pid
        }

    async def _classify(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Classify text into categories."""
        text = parameters.get("text")
        categories = parameters.get("categories")

        if not text or not categories:
            raise ValueError("Missing 'text' or 'categories' parameters")

        prompt = f"""Classify the following text into one of these categories: {', '.join(categories)}

Text: {text}

Return only the category name."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.3
        )

        classification = response.choices[0].message.content.strip()
        cost = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return {
            "classification": classification,
            "categories": categories,
            "cost": round(cost, 4),
            "provider": self.pid
        }


if __name__ == "__main__":
    agent = LLMEndpointGPT4Agent()
    agent.run()
