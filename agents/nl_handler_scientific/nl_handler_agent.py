"""Scientific NL Handler aFDO - Interprets and coordinates scientific research queries."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
from typing import Dict, Any, List
from openai import OpenAI

from shared.afdo_base import aFDOBase
from agents.nl_handler_scientific.workflow_planner import WorkflowPlanner


class ScientificNLHandlerAgent(aFDOBase):
    """
    Scientific NL Handler aFDO.

    Composite agent that:
    - Interprets natural language queries about research/science
    - Plans multi-agent workflows
    - Discovers and coordinates other aFDOs
    - Synthesizes results

    Has built-in LLM for interpretation.
    """

    def __init__(self):
        super().__init__(
            name="Scientific NL Handler",
            fdo_type="21.T11148/type-user-interface-v1",
            operations=[
                "interpret_natural_language",
                "plan_workflow",
                "execute_workflow"
            ],
            port=8002,
            cost=0.05,
            has_llm=True,
            llm_model="gpt-4o",
            specialization="scientific_research"
        )

        # Initialize OpenAI client (supports Ollama via base_url)
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        if not api_key:
            print("⚠️  Warning: OPENAI_API_KEY not set.")
            self.client = None
        else:
            if base_url:
                print(f"🔧 Using custom LLM endpoint: {base_url}")
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)

        self.planner = WorkflowPlanner()

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Composite agent for scientific research queries using natural language",
            "version": "2.0.0",
            "agent_role": "composite_agent",
            "specialization": "scientific_research",
            "model": "gpt-4o",
            "capabilities": {
                "interpret_natural_language": {
                    "description": "Parse and understand scientific queries with context extraction",
                    "input_schema": {
                        "query": "natural language query string"
                    },
                    "output_schema": {
                        "query": "original query",
                        "interpretation": "LLM interpretation",
                        "workflow_plan": "planned execution steps",
                        "handler": "this agent's PID"
                    },
                    "estimated_duration": "2-5s",
                    "estimated_cost": "$0.05-0.10",
                    "requires_llm": True
                },
                "plan_workflow": {
                    "description": "Plan multi-agent execution workflows for complex queries",
                    "input_schema": {
                        "query": "natural language query"
                    },
                    "output_schema": {
                        "workflow": "dict with steps and agents",
                        "planner": "this agent's PID"
                    },
                    "estimated_duration": "2-5s",
                    "estimated_cost": "$0.05-0.10"
                },
                "execute_workflow": {
                    "description": "Execute planned workflows and synthesize results",
                    "input_schema": {
                        "query": "natural language query",
                        "data": "dict with context data (optional)"
                    },
                    "output_schema": {
                        "query": "original query",
                        "interpretation": "query understanding",
                        "workflow_executed": "executed workflow",
                        "steps_completed": "list of completed steps",
                        "final_result": "synthesized result string"
                    },
                    "estimated_duration": "10-60s",
                    "estimated_cost": "$0.20-1.00"
                }
            },
            "dependencies": {
                "required_services": [
                    {"type": "document_processor", "operation": "extract_text", "for": "PDF extraction"},
                    {"type": "compliance_checker", "operation": "assess_fairness", "for": "FAIR checks"},
                    {"type": "llm_service", "operation": "analyze_scientific_text", "for": "analysis"}
                ]
            },
            "performance_characteristics": {
                "typical_latency": "10-60s depending on workflow",
                "max_concurrent_requests": 5,
                "supports_streaming": False
            },
            "coordinates_with": [
                "document_processor",
                "compliance_checker",
                "llm_service"
            ],
            "llm_capable": True
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "Scientific NL Handler Agent",
                "version": "1.0.0",
                "agent_type": "interface",
                "description": "Interprets natural language queries and routes to appropriate domain agents"
            },

            "capabilities": {
                "interpret_natural_language": {
                    "operation_type": "query_processing",

                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 10000
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["query", "interpretation", "workflow_plan"],
                        "properties": {
                            "query": {"type": "string"},
                            "interpretation": {"type": "string"},
                            "workflow_plan": {
                                "type": "object",
                                "properties": {
                                    "steps": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            },
                            "handler": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 30,
                        "rate_limit": 50
                    },

                    "examples": [
                        {
                            "input": {
                                "query": "Analyze this research paper on machine learning"
                            },
                            "output": {
                                "query": "Analyze this research paper on machine learning",
                                "interpretation": "User wants to perform comprehensive analysis of a research paper",
                                "workflow_plan": {
                                    "steps": []
                                },
                                "handler": "21.T11148/afdo-scientific-nl-handler"
                            }
                        }
                    ]
                },

                "plan_workflow": {
                    "operation_type": "query_processing",

                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {"type": "string"}
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["workflow", "planner"],
                        "properties": {
                            "workflow": {
                                "type": "object",
                                "properties": {
                                    "steps": {"type": "array"}
                                }
                            },
                            "planner": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 30,
                        "rate_limit": 50
                    },

                    "examples": []
                },

                "execute_workflow": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {"type": "string"},
                            "data": {"type": "object"}
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["query", "interpretation", "workflow_executed", "steps_completed", "final_result"],
                        "properties": {
                            "query": {"type": "string"},
                            "interpretation": {"type": "string"},
                            "workflow_executed": {"type": "object"},
                            "steps_completed": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "final_result": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 300,
                        "rate_limit": 10
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [
                    "openai==1.12.0"
                ],
                "resource_requirements": {
                    "memory_mb": 256,
                    "cpu_cores": 0.5
                }
            },

            "agent_attributes": {
                "has_llm": True,
                "autonomy_level": "composite",
                "decision_policy": "autonomous",
                "can_delegate": True
            }
        }

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle NL processing operations."""
        if not self.client:
            raise ValueError("OpenAI client not initialized.")

        print(f"🧠 Processing '{operation}' from {caller_pid}")

        if operation == "interpret_natural_language":
            return await self._interpret_natural_language(parameters)

        elif operation == "plan_workflow":
            return await self._plan_workflow(parameters)

        elif operation == "execute_workflow":
            return await self._execute_workflow(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _interpret_natural_language(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpret natural language query."""
        query = parameters.get("query")
        if not query:
            raise ValueError("Missing 'query' parameter")

        print(f"  → Interpreting query: {query[:100]}...")

        # Use LLM to understand intent
        system_prompt = """You are a scientific research assistant. Analyze the user's query and determine:
1. What they want to do (analyze paper, check FAIR compliance, get information, etc.)
2. What data/inputs they're providing (PDF, metadata, text, etc.)
3. What output they expect

Be concise and specific."""

        model = os.getenv("LLM_MODEL", "gpt-4o")
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=300,
            temperature=0.3
        )

        interpretation = response.choices[0].message.content

        # Plan workflow based on interpretation
        workflow = self.planner.analyze_query(query, interpretation)

        return {
            "query": query,
            "interpretation": interpretation,
            "workflow_plan": workflow,
            "handler": self.pid
        }

    async def _plan_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Plan workflow for a query."""
        query = parameters.get("query")
        if not query:
            raise ValueError("Missing 'query'")

        # Get interpretation
        interpretation = await self._interpret_natural_language({"query": query})

        return {
            "workflow": interpretation["workflow_plan"],
            "planner": self.pid
        }

    async def _execute_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a planned workflow."""
        query = parameters.get("query")
        data = parameters.get("data", {})

        if not query:
            raise ValueError("Missing 'query'")

        print(f"  → Executing workflow for: {query[:100]}...")

        # Step 1: Interpret and plan
        interpretation = await self._interpret_natural_language({"query": query})
        workflow = interpretation["workflow_plan"]

        results = {
            "query": query,
            "interpretation": interpretation["interpretation"],
            "workflow_executed": workflow,
            "steps_completed": [],
            "final_result": None
        }

        # Step 2: Execute workflow steps
        for step in workflow["steps"]:
            print(f"    Step {step['step']}: {step['action']}")

            try:
                if step["action"] == "extract_pdf":
                    step_result = await self._execute_pdf_extraction(data)
                    results["steps_completed"].append({
                        "step": step["step"],
                        "action": step["action"],
                        "status": "success",
                        "result": step_result
                    })
                    # Store for next steps
                    data["extracted_text"] = step_result.get("text", "")

                elif step["action"] == "assess_fair":
                    step_result = await self._execute_fair_assessment(data)
                    results["steps_completed"].append({
                        "step": step["step"],
                        "action": step["action"],
                        "status": "success",
                        "result": step_result
                    })

                elif step["action"] == "analyze":
                    step_result = await self._execute_analysis(data)
                    results["steps_completed"].append({
                        "step": step["step"],
                        "action": step["action"],
                        "status": "success",
                        "result": step_result
                    })

                elif step["action"] == "respond":
                    # Direct LLM response
                    step_result = await self._generate_direct_response(query)
                    results["steps_completed"].append({
                        "step": step["step"],
                        "action": step["action"],
                        "status": "success",
                        "result": step_result
                    })

            except Exception as e:
                print(f"    ✗ Step {step['step']} failed: {e}")
                results["steps_completed"].append({
                    "step": step["step"],
                    "action": step["action"],
                    "status": "failed",
                    "error": str(e)
                })

        # Step 3: Synthesize final result
        results["final_result"] = await self._synthesize_results(
            query,
            results["steps_completed"]
        )

        return results

    async def _execute_pdf_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PDF extraction step."""
        # Discover PDF Parser
        agents = await self.discover_by_type("document_processor")
        if not agents:
            raise ValueError("No PDF parser agent found")

        pdf_parser_pid = agents[0]["pid"]

        # Call PDF Parser
        result = await self.call_other_afdo(
            target_pid=pdf_parser_pid,
            operation="extract_text",
            data={"pdf_data": data.get("pdf_data")}
        )

        return result.get("data", {})

    async def _execute_fair_assessment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute FAIR assessment step."""
        # Discover FAIR Assessor
        agents = await self.discover_by_type("compliance_checker")
        if not agents:
            raise ValueError("No FAIR assessor found")

        fair_assessor_pid = agents[0]["pid"]

        # Call FAIR Assessor
        result = await self.call_other_afdo(
            target_pid=fair_assessor_pid,
            operation="assess_fairness",
            data={"metadata": data.get("metadata", {})}
        )

        return result.get("data", {})

    async def _execute_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis step."""
        # Discover LLM service (prefer scientific)
        agents = await self.discover_by_operation("analyze_scientific_text")

        if not agents:
            # Fallback to general LLM
            agents = await self.discover_by_operation("summarize")

        if not agents:
            raise ValueError("No LLM service found")

        llm_pid = agents[0]["pid"]
        text = data.get("extracted_text", data.get("text", ""))

        # Call LLM service
        result = await self.call_other_afdo(
            target_pid=llm_pid,
            operation="analyze_scientific_text",
            data={"text": text}
        )

        return result.get("data", {})

    async def _generate_direct_response(self, query: str) -> Dict[str, Any]:
        """Generate direct response using built-in LLM."""
        model = os.getenv("LLM_MODEL", "gpt-4o")
        print(f"  🤖 Using model: {model}")
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful scientific research assistant."},
                {"role": "user", "content": query}
            ],
            max_tokens=500,
            temperature=0.7
        )

        return {
            "response": response.choices[0].message.content
        }

    async def _synthesize_results(
        self,
        query: str,
        steps: List[Dict[str, Any]]
    ) -> str:
        """Synthesize final response from workflow results."""
        # Collect all results
        results_text = f"Original query: {query}\n\n"

        for step in steps:
            if step["status"] == "success":
                results_text += f"Step {step['step']} ({step['action']}): Completed\n"

        # Use LLM to create final response
        synthesis_prompt = f"""Based on the following workflow execution, provide a clear, concise response to the user:

{results_text}

Workflow results: {steps}

Provide a helpful summary for the user."""

        response = self.client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            messages=[{"role": "user", "content": synthesis_prompt}],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content


if __name__ == "__main__":
    agent = ScientificNLHandlerAgent()
    agent.run()
