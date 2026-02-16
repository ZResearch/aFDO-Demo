"""
LLM Consultant Agent

Generates workflows dynamically based on task analysis.

Does NOT use predefined templates.
Analyzes each task and creates custom workflow from scratch.

Operations:
- generate_workflow: Generate workflow for a task
- advise_strategy: Provide strategic advice
- analyze_task: Break down task into components
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import uuid
import json
from typing import Dict, Any
from openai import AsyncOpenAI
from shared.afdo_base import aFDOBase


class LLMConsultantAgent(aFDOBase):
    """
    LLM Consultant Agent - Dynamic workflow generation.
    
    This agent is the KEY to avoiding hardcoded workflows.
    It analyzes tasks and generates workflows on-the-fly.
    """
    
    def __init__(self):
        super().__init__(
            name="LLM Consultant",
            fdo_type="21.T11148/type-data-source-v1",
            operations=[
                "receive_query",  # Universal cascading entry point
                "generate_workflow",
                "advise_strategy",
                "analyze_task",
                "analyze_query_intent"
            ],
            port=8014,
            cost=0.03,  # Small cost for consultation
            has_llm=True,
            specialization="workflow_planning"
        )

        # Initialize OpenAI client with environment config
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

        if not api_key:
            raise ValueError("OPENAI_API_KEY not set - LLM Consultant requires LLM access")

        if base_url:
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self.logger.info(self.name, f"Using custom API base: {base_url}")
        else:
            self.client = AsyncOpenAI(api_key=api_key)

        self.logger.info(self.name, f"🧠 LLM Consultant initialized - model: {self.model}")
    
    def get_metadata_content(self) -> Dict[str, Any]:
        return {
            "description": "Generates workflows dynamically based on task analysis",
            "version": "1.0.0",
            "agent_role": "consultant",
            "workflow_generation": "dynamic"
        }
    
    def get_self_description(self) -> Dict[str, Any]:
        return {
            "agent_info": {
                "name": "LLM Consultant",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Analyzes, synthesizes, and explains information using LLM. Specializes in understanding user intent, analyzing queries, and transforming natural language questions into abstract capability descriptions for agent matching. Generates workflows dynamically based on task analysis. Best for query intent detection, synthesis, comparison, explanation, and reasoning tasks."
            },
            "capabilities": {
                "generate_workflow": {
                    "operation_type": "query_processing",
                    "input_schema": {
                        "type": "object",
                        "required": ["task_description", "requester_capabilities"],
                        "properties": {
                            "task_description": {
                                "type": "string",
                                "description": "Description of the task to plan"
                            },
                            "requester_capabilities": {
                                "type": "array",
                                "description": "Operations the requesting agent can perform",
                                "items": {"type": "string"}
                            },
                            "requester_pid": {
                                "type": "string",
                                "description": "PID of requesting agent"
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context (budget, preferences, etc.)"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["workflow"],
                        "properties": {
                            "workflow": {
                                "type": "object",
                                "description": "Generated workflow following workflow_protocol.json schema"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Explanation of workflow design"
                            }
                        }
                    },
                    "constraints": {
                        "timeout_seconds": 30,
                        "rate_limit": 20
                    },
                    "examples": []
                },
                "receive_query": {
                    "operation_type": "synthesis",
                    "description": "ONLY for complex synthesis, comparison, and interpretation tasks when you already possess the required data. Exclusively use for: comparing multiple perspectives side-by-side, synthesizing information from multiple sources you already gathered, generating insights from existing data, interpreting complex relationships between concepts. NEVER use for: factual questions, information retrieval, database searches, data lookup, verifying claims or facts, fact-checking, checking if statements are true, finding definitions, answering who/what/where/when/is questions, searching for current information, or validation tasks. This is a cognitive processing and synthesis tool only, not an information retrieval, search, verification, or fact-checking tool.",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query or request for synthesis/analysis/explanation"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "response": {"type": "string"},
                            "source": {"type": "string"}
                        }
                    },
                    "side_effects": ["uses_llm_tokens"],
                    "idempotent": False
                },
                "advise_strategy": {
                    "operation_type": "assessment",
                    "input_schema": {
                        "type": "object",
                        "required": ["situation"],
                        "properties": {
                            "situation": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "advice": {"type": "string"},
                            "options": {"type": "array"}
                        }
                    },
                    "constraints": {
                        "timeout_seconds": 20
                    },
                    "examples": []
                },
                "analyze_task": {
                    "operation_type": "assessment",
                    "input_schema": {
                        "type": "object",
                        "required": ["task"],
                        "properties": {
                            "task": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "complexity": {"type": "string"},
                            "requirements": {"type": "array"},
                            "suggested_approach": {"type": "string"}
                        }
                    },
                    "constraints": {
                        "timeout_seconds": 15
                    },
                    "examples": []
                },
                "analyze_query_intent": {
                    "operation_type": "query_processing",
                    "description": "Analyzes user queries to understand intent and generate abstract capability descriptions. Transforms natural language questions into structured descriptions of required agent capabilities suitable for semantic matching.",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Raw user query to analyze"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["capability_description"],
                        "properties": {
                            "capability_description": {
                                "type": "string",
                                "description": "Abstract description of agent capabilities needed to handle this query"
                            },
                            "query_type": {
                                "type": "string",
                                "description": "Type of query (factual, research, synthesis, etc.)"
                            },
                            "key_requirements": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of key capability requirements"
                            }
                        }
                    },
                    "side_effects": ["uses_llm_tokens"],
                    "idempotent": True,
                    "constraints": {
                        "timeout_seconds": 10
                    },
                    "examples": [
                        {
                            "input": {"query": "who is the president of Algeria"},
                            "output": {
                                "capability_description": "Agent that provides current factual information about world leaders, political positions, government officials, and country-specific information. Should have access to encyclopedic knowledge and be able to answer biographical and political queries.",
                                "query_type": "factual",
                                "key_requirements": ["current information", "political knowledge", "biographical data", "country-specific facts"]
                            }
                        }
                    ]
                }
            },
            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": ["openai==1.12.0"],
                "resource_requirements": {
                    "memory_mb": 256,
                    "cpu_cores": 0.5
                }
            },
            "agent_attributes": {
                "has_llm": True,
                "autonomy_level": "task",
                "decision_policy": "autonomous",
                "can_delegate": False
            }
        }
    
    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle consultant operations.

        Required by aFDOBase abstract method.
        """

        self.logger.info(self.name, f"Handling operation: {operation} from {caller_pid}")

        if operation == "receive_query":
            return await self._receive_query(parameters)

        elif operation == "generate_workflow":
            return await self._generate_workflow(parameters)

        elif operation == "advise_strategy":
            return await self._advise_strategy(parameters)

        elif operation == "analyze_task":
            return await self._analyze_task(parameters)

        elif operation == "analyze_query_intent":
            return await self._analyze_query_intent(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _receive_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal entry point - receives queries for synthesis/analysis/explanation.

        For LLM Consultant, this is a terminal operation:
        1. Receive query
        2. Process with LLM
        3. Return synthesized response

        LLM Consultant uses its language model to understand, analyze, synthesize,
        and generate natural language responses.
        """
        query = parameters.get("query") or parameters.get("message")

        if not query:
            raise ValueError("Missing 'query' or 'message' parameter")

        self.logger.info(self.name, f"📨 Received query for synthesis/analysis")

        try:
            # Use LLM to process the query
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that synthesizes information, explains concepts, compares ideas, and provides insights. Provide clear, concise, accurate responses based on the information provided."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

            self.logger.info(self.name, f"🧠 Calling LLM for synthesis...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            synthesis_text = response.choices[0].message.content.strip()

            self.logger.info(self.name, f"✅ Synthesis complete ({len(synthesis_text)} chars)")

            return {
                "response": synthesis_text,
                "source": "LLM Consultant",
                "model": self.model,
                "query": query
            }

        except Exception as e:
            self.logger.error(self.name, f"❌ Synthesis failed: {e}")
            raise

    async def _generate_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate workflow dynamically based on task analysis.
        
        This is the CORE method - NO predefined templates!
        """
        
        task_description = parameters.get("task_description")
        requester_capabilities = parameters.get("requester_capabilities", [])
        requester_pid = parameters.get("requester_pid", "unknown")
        context = parameters.get("context", {})
        
        self.logger.info(f"🧠 Generating workflow for: {task_description[:100]}...")
        self.logger.info(f"   Requester: {requester_pid}")
        self.logger.info(f"   Capabilities: {requester_capabilities}")
        
        # Create prompt for LLM
        workflow_id = f"wf_generated_{uuid.uuid4().hex[:8]}"
        timestamp = self._get_timestamp()
        
        prompt = f"""You are an expert workflow planning consultant for autonomous agents.

TASK: {task_description}

CONTEXT:
- Requesting agent PID: {requester_pid}
- Requesting agent's capabilities: {requester_capabilities}
- Budget: {context.get('budget', 'unlimited')}
- Quality preference: {context.get('quality_preference', 'balanced')}

YOUR JOB:
Generate a workflow (JSON) that accomplishes this task efficiently.

WORKFLOW RULES:
1. Break task into logical steps
2. For each step specify:
   - step_id: unique identifier (e.g., "step_01", "step_02")
   - name: short descriptive name
   - description: what this step does
   - operation: the operation to perform
   - executor: "self" (if requester can do it) OR "discover" (if need to find helper)
   - discovery_query: if executor="discover", specify what operation to search for
   - depends_on: array of step_ids that must complete first
   - input_mapping: where inputs come from (e.g., "workflow.input.question" or "step_01.result.data")
   - on_failure: "abort" | "continue" | "retry" | "fallback"

3. Use "self" executor only for operations in requester's capabilities: {requester_capabilities}
4. Use "discover" executor for operations requester doesn't have
5. Be smart about dependencies - maximize parallelism where possible
6. Be budget-conscious - use cheaper agents where appropriate

RESPONSE FORMAT (JSON only, no markdown):
{{
  "workflow_id": "{workflow_id}",
  "name": "Descriptive workflow name",
  "description": "Brief description",
  "created_by": "{requester_pid}",
  "created_at": "{timestamp}",
  "status": "draft",
  "input_schema": {{
    "type": "object",
    "required": ["question"],
    "properties": {{
      "question": {{"type": "string"}}
    }}
  }},
  "output_schema": {{
    "type": "object",
    "properties": {{
      "answer": {{"type": "string"}}
    }}
  }},
  "steps": [
    {{
      "step_id": "step_01",
      "name": "Step name",
      "description": "What this does",
      "operation": "operation_name",
      "executor": "self|discover",
      "discovery_query": {{
        "operation": "operation_to_find",
        "selection_criteria": "cheapest|fastest|balanced|best_reputation"
      }},
      "depends_on": [],
      "input_mapping": {{
        "param_name": "workflow.input.field"
      }},
      "on_failure": "abort|continue|retry|fallback"
    }}
  ]
}}

IMPORTANT: Return ONLY valid JSON, no explanation or markdown."""

        try:
            # Call LLM to generate workflow
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse generated workflow
            workflow_json = json.loads(response.choices[0].message.content)
            
            self.logger.info(f"✅ Generated workflow: {workflow_json.get('name')}")
            self.logger.info(f"   Steps: {len(workflow_json.get('steps', []))}")
            
            # Log the workflow for debugging
            for i, step in enumerate(workflow_json.get('steps', []), 1):
                self.logger.info(f"   {i}. {step.get('name')} ({step.get('executor')})")
            
            return {
                "workflow": workflow_json,
                "reasoning": f"Generated {len(workflow_json.get('steps', []))} step workflow based on task analysis"
            }
        
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            
            # Fallback: create simple workflow
            return self._create_fallback_workflow(task_description, requester_capabilities, requester_pid)
        
        except Exception as e:
            self.logger.error(f"❌ Workflow generation failed: {e}")
            raise
    
    def _create_fallback_workflow(
        self,
        task: str,
        capabilities: list,
        requester_pid: str
    ) -> Dict[str, Any]:
        """
        Create simple fallback workflow if LLM generation fails.
        
        This is a safety net - still generated dynamically!
        """
        
        self.logger.warning("⚠️ Using fallback workflow generation")
        
        workflow = {
            "workflow_id": f"wf_fallback_{uuid.uuid4().hex[:8]}",
            "name": "Simple Fallback Workflow",
            "description": "Fallback workflow when LLM generation fails",
            "created_by": requester_pid,
            "created_at": self._get_timestamp(),
            "status": "draft",
            "input_schema": {
                "type": "object",
                "required": ["question"],
                "properties": {
                    "question": {"type": "string"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            "steps": [
                {
                    "step_id": "step_01",
                    "name": "Process Task",
                    "description": "Process task with available capabilities",
                    "operation": capabilities[0] if capabilities else "process",
                    "executor": "self",
                    "depends_on": [],
                    "input_mapping": {
                        "data": "workflow.input.question"
                    },
                    "on_failure": "abort"
                }
            ]
        }
        
        return {
            "workflow": workflow,
            "reasoning": "Fallback workflow - LLM generation failed"
        }
    
    async def _advise_strategy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Provide strategic advice for a situation."""
        
        situation = parameters.get("situation")
        
        prompt = f"""You are a strategic advisor for autonomous agents.

SITUATION: {situation}

Provide clear, actionable advice including:
1. Analysis of the situation
2. 2-3 strategic options
3. Recommendation

Be concise and practical."""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model for advice
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        
        advice = response.choices[0].message.content
        
        return {
            "advice": advice,
            "options": []  # Could parse from advice
        }
    
    async def _analyze_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task complexity and requirements."""
        
        task = parameters.get("task")
        
        prompt = f"""Analyze this task:

TASK: {task}

Provide brief analysis as JSON:
{{
  "complexity": "simple|moderate|complex|very_complex",
  "requirements": ["requirement1", "requirement2"],
  "estimated_steps": 3,
  "suggested_approach": "Brief approach"
}}"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        return analysis

    async def _analyze_query_intent(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user query to extract intent and generate capability description.

        This transforms a raw user query into an abstract description of what
        kind of agent capabilities are needed to handle it.
        """

        query = parameters.get("query", "")

        if not query:
            raise ValueError("query parameter is required")

        prompt = f"""Analyze this user query and describe what is needed to answer it.

USER QUERY: "{query}"

Your task: Understand what the user is asking for and describe it simply. Do NOT prescribe HOW to answer it.

Identify the query type:
- FACTUAL RETRIEVAL: "what is X?", "who is Y?", "where is Z?", "when did X?" → need factual information
- VERIFICATION: "is X Y?", "did X happen?", "is it true that X?" → need to verify if statement is true
- COMPARISON: "compare X and Y", "difference between X and Y" → need to compare things
- EXPLANATION: "why X?", "how does X work?" → need explanation with reasoning

Provide simple capability description - just describe WHAT information is needed, not verification, synthesis, or processing methods.

Examples:
- "What is quantum computing?" → "Provide factual information about quantum computing"
- "Is Paris the capital of France?" → "Verify if Paris is the capital of France"
- "Compare X and Y" → "Compare X and Y"
- "The study claims X, is it true?" → "Verify claim that X from study"

Provide your analysis as JSON:
{{
  "capability_description": "Simple description of what information or verification is needed. Focus on the core need, not on methods.",
  "query_type": "retrieval|verification|comparison|explanation",
  "key_requirements": ["main requirement"],
  "domain": "general|science|politics|history|technology|etc"
}}

Generate the capability description:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            self.logger.info(self.name, f"📋 Query Analysis:")
            self.logger.info(self.name, f"   Query: {query}")
            self.logger.info(self.name, f"   Type: {result.get('query_type', 'unknown')}")
            self.logger.info(self.name, f"   Domain: {result.get('domain', 'unknown')}")
            self.logger.info(self.name, f"   Capability: {result.get('capability_description', '')[:100]}...")

            return result

        except Exception as e:
            self.logger.error(self.name, f"❌ Query analysis failed: {e}")
            # Fallback: return the query itself as capability description
            return {
                "capability_description": f"Agent capable of handling queries like: {query}",
                "query_type": "unknown",
                "key_requirements": ["general query handling"],
                "domain": "general"
            }

    def _get_timestamp(self) -> str:
        """Get ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


if __name__ == "__main__":
    agent = LLMConsultantAgent()
    agent.run()
