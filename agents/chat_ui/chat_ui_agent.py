"""Chat UI aFDO - Intelligent dispatcher with workflow planning and budget management."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from shared.afdo_base import aFDOBase
from shared.budget_manager import BudgetManager

class ChatUIAgent(aFDOBase):
    """
    Chat UI aFDO.

    Intelligent dispatcher with:
    - Built-in LLM for query interpretation
    - Workflow planning
    - Cost estimation
    - Budget management
    - Direct marketplace interaction
    """

    def __init__(self):
        super().__init__(
            name="Chat UI",
            fdo_type="21.T11148/type-user-interface-v1",
            operations=[
                "display_message",
                "receive_user_input",
                "estimate_workflow_cost",
                "execute_workflow"
            ],
            port=8001,
            cost=0.0,  # Free UI service
            has_llm=True,
            llm_model="mistral:7b",
            selection_policy="balanced"
        )

        # Initialize OpenAI client for query interpretation
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o")  # Get model from env

        if not api_key:
            print("⚠️  Warning: OPENAI_API_KEY not set. Query interpretation disabled.")
            self.client = None
        else:
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Intelligent dispatcher with workflow planning and budget management",
            "version": "2.0.0",
            "interface_type": "web_ui",
            "capabilities": {
                "display_message": "Display message to user",
                "receive_user_input": "Receive, interpret, plan, and execute user requests",
                "estimate_workflow_cost": "Estimate cost before execution",
                "execute_workflow": "Execute planned workflows with budget tracking"
            },
            "marketplace_features": {
                "query_interpretation": True,
                "workflow_planning": True,
                "cost_estimation": True,
                "budget_management": True,
                "policy_based_selection": True
            },
            "ui_endpoint": f"http://localhost:{self.port}",
            "llm_capable": True,
            "llm_model": "mistral:7b"
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "Chat UI Agent",
                "version": "1.0.0",
                "agent_type": "interface",
                "description": "User interface and orchestration layer that receives user messages and delegates to specialized agents. Does not provide knowledge or data itself - acts as coordinator and router. Should NOT be selected for answering questions - only for receiving initial user input."
            },

            "capabilities": {
                "receive_user_input": {
                    "operation_type": "query_processing",

                    "input_schema": {
                        "type": "object",
                        "required": ["message"],
                        "properties": {
                            "message": {
                                "type": "string",
                                "minLength": 1
                            },
                            "budget": {
                                "type": "number",
                                "default": 1.0,
                                "minimum": 0.0
                            },
                            "policy": {
                                "type": "string",
                                "enum": ["cheapest", "fastest", "balanced"],
                                "default": "balanced"
                            },
                            "auto_execute": {
                                "type": "boolean",
                                "default": True
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["status"],
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["success", "insufficient_budget", "error"]
                            },
                            "message": {"type": "string"},
                            "result": {"type": "object"},
                            "budget_summary": {
                                "type": "object",
                                "properties": {
                                    "allocated": {"type": "number"},
                                    "spent": {"type": "number"},
                                    "remaining": {"type": "number"}
                                }
                            }
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 300,
                        "rate_limit": 20
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [
                    "fastapi==0.109.0",
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
        """Handle UI operations."""
        self.logger.info(self.name, f"🔥 CHAT UI handle_operation called: {operation}")
        print(f"💬 Processing '{operation}' from {caller_pid}")

        if operation == "receive_user_input":
            self.logger.info(self.name, f"🔥 CHAT UI calling _receive_user_input")
            return await self._receive_user_input(parameters)

        elif operation == "display_message":
            return await self._display_message(parameters)

        elif operation == "estimate_workflow_cost":
            return await self._estimate_workflow_cost(parameters)

        elif operation == "execute_workflow":
            return await self._execute_workflow(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _receive_user_input(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user input - PURELY POLICY-DRIVEN.

        Evaluates policy and executes the decision.
        Policy decides:
        - Greetings → handle_alone (handle locally)
        - Queries → semantic_discovery (delegate to best agent)
        """

        self.logger.info(self.name, f"📨 _receive_user_input called with parameters: {parameters}")

        message = parameters.get("message")
        if not message:
            raise ValueError("Missing 'message' parameter")

        self.logger.info(self.name, f"📨 Received user input: {message[:100]}...")

        # Evaluate policy
        if not self.policy_engine:
            raise ValueError("Policy engine not loaded")

        decision = await self.policy_engine.decide(
            operation="receive_user_input",
            parameters=parameters,
            context={"caller_pid": "web-user"}
        )

        self.logger.info(self.name, f"🧠 Policy decision: {decision.decision.value}")
        if decision.rule_id:
            self.logger.info(self.name, f"   Rule: {decision.rule_id}")
            self.logger.info(self.name, f"   Reasoning: {decision.reasoning}")

        # Execute policy decision
        from shared.policy_engine import DecisionType

        if decision.decision == DecisionType.HANDLE_ALONE:
            # Handle locally (greetings/capabilities)
            return await self._handle_capabilities_query(message)

        elif decision.decision == DecisionType.SEMANTIC_DISCOVERY:
            self.logger.info(self.name, "🎯 ENTERING SEMANTIC_DISCOVERY handler in Chat UI")

            # Use semantic discovery to find best agent and cascade
            result = await self._semantic_discovery_and_cascade(
                decision, "receive_user_input", parameters
            )

            self.logger.info(self.name, f"📦 Result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")

            # Unwrap DOIP response to get actual content
            if isinstance(result, dict) and 'data' in result:
                data = result['data']
                self.logger.info(self.name, f"📦 Data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")

                # If data is itself a DOIP response (double-nested), unwrap it
                if isinstance(data, dict) and 'data' in data and 'status' in data:
                    self.logger.info(self.name, "🔓 Unwrapping nested DOIP response")
                    data = data['data']
                    self.logger.info(self.name, f"📦 Unwrapped data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")

                # Format for UI display
                formatted = self._format_delegated_response(data)
                if formatted:
                    self.logger.info(self.name, f"✅ Returning formatted response with 'response' field")
                    return formatted

                self.logger.info(self.name, f"✅ Returning raw data")
                return data

            return result

        elif decision.decision == DecisionType.SEQUENCE:
            self.logger.info(self.name, "📋 EXECUTING SEQUENCE from policy")
            self.logger.info(self.name, f"   Parameters before calling _execute_sequence: {parameters}")

            # Execute sequence using base class handler
            result = await self._execute_sequence(
                decision, "receive_user_input", parameters
            )

            self.logger.info(self.name, f"📦 Sequence result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")

            # Unwrap and format response (same as semantic_discovery)
            if isinstance(result, dict) and 'data' in result:
                data = result['data']
                self.logger.info(self.name, f"📦 Data before unwrap: keys={list(data.keys()) if isinstance(data, dict) else 'not dict'}")

                # If data is itself a DOIP response (double-nested), unwrap it
                if isinstance(data, dict) and 'data' in data and 'status' in data:
                    self.logger.info(self.name, "🔓 Unwrapping nested DOIP response")
                    data = data['data']

                self.logger.info(self.name, f"📦 Data after unwrap: keys={list(data.keys()) if isinstance(data, dict) else 'not dict'}")

                # Format for UI display
                formatted = self._format_delegated_response(data)
                self.logger.info(self.name, f"📦 Formatted result: {formatted}")
                if formatted:
                    self.logger.info(self.name, f"✅ Returning formatted response")
                    return formatted

                self.logger.info(self.name, f"⚠️ No formatting applied, returning raw data")
                return data

            self.logger.info(self.name, f"⚠️ Result has no 'data' field, returning raw result")
            return result

        else:
            raise ValueError(f"Unexpected policy decision: {decision.decision}")

    def _format_delegated_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format response from delegated agents for user display."""
        if not isinstance(data, dict):
            return None

        # If already formatted, return as-is
        if 'response' in data and 'status' in data:
            return data

        # Format based on response type
        response_text = None

        if 'answer' in data:
            response_text = data['answer']
        elif 'summary' in data:
            response_text = f"**{data.get('title', 'Result')}**\n\n{data['summary']}"
            if 'url' in data:
                response_text += f"\n\nSource: {data['url']}"
        elif 'response' in data:
            response_text = data['response']
        elif 'papers' in data:
            papers = data['papers']
            response_text = f"Found {len(papers)} papers:\n\n"
            for i, paper in enumerate(papers[:5], 1):
                response_text += f"{i}. **{paper['title']}**\n"
                response_text += f"   Authors: {', '.join(paper['authors'][:3])}\n"
                response_text += f"   Abstract: {paper['abstract'][:200]}...\n\n"

        if response_text:
            return {
                "response": response_text,
                "status": "success",
                "delegated_to": data.get('extracted_by') or data.get('source') or "agent",
                "cascade_path": data.get('cascade_path')
            }

        return data

    async def _is_greeting_or_capability_query(self, message: str) -> bool:
        """Check if message is a greeting or capability query."""
        message_lower = message.lower().strip()

        # Greeting patterns
        greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon"]
        if any(message_lower.startswith(g) for g in greetings):
            return True

        # Capability query patterns
        capability_keywords = [
            "what can you do",
            "what you can do",
            "what can you",
            "what do you do",
            "what you do",
            "what services",
            "what agents",
            "help",
            "capabilities",
            "what are you",
            "who are you",
            "how can you help",
            "what's possible",
            "what operations",
            "available agents",
            "list agents",
            "show me",
            "tell me about"
        ]
        if any(keyword in message_lower for keyword in capability_keywords):
            return True

        return False

    async def _handle_capabilities_query(self, message: str) -> Dict[str, Any]:
        """Handle capability queries with AI-powered response."""
        print("    Generating intelligent capability response...")

        # Get current system capabilities
        greeting_data = await self._get_dynamic_greeting()

        # Generate conversational response
        message_lower = message.lower().strip()

        # Detect query type
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            # Greeting response
            response_text = self._generate_greeting_response(greeting_data)
        elif any(word in message_lower for word in ["what can", "what do", "services", "capabilities", "help", "agents"]):
            # Capabilities query
            response_text = self._generate_capabilities_response(greeting_data)
        else:
            # General welcome
            response_text = self._generate_greeting_response(greeting_data)

        # If LLM available, enhance the response
        if self.client:
            try:
                system_prompt = f"""You are a friendly AI assistant for an autonomous agent marketplace.
Current system state:
- {greeting_data.get('agent_summary', {}).get('total_agents', 0)} active agents
- Available capabilities: {', '.join([cap['operation'].replace('_', ' ') for cap in greeting_data.get('capabilities', [])[:5]])}

Enhance this response to be more conversational and helpful, but keep it concise (2-3 sentences):
{response_text}

User said: "{message}" """

                response = self.client.chat.completions.create(
                    model="mistral:7b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Make this more conversational"}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )

                response_text = response.choices[0].message.content
                print(f"    ✓ LLM enhanced response")

            except Exception as e:
                print(f"    ⚠ LLM enhancement failed (using template): {e}")
                # Continue with template response

        return {
            "status": "success",
            "response": response_text,  # Changed from "message" to "response" for frontend compatibility
            "available_capabilities": greeting_data.get("capabilities", []),
            "agent_summary": greeting_data.get("agent_summary", {}),
            "query_type": "capability_query"
        }

    def _generate_greeting_response(self, greeting_data: Dict[str, Any]) -> str:
        """Generate a friendly greeting response."""
        total_agents = greeting_data.get("agent_summary", {}).get("total_agents", 0)

        greetings = [
            f"Hello! I'm your AI assistant for the autonomous agent marketplace. We have {total_agents} specialized agents ready to help you analyze papers, check FAIR compliance, and more. What can I help you with today?",
            f"Hi there! I coordinate {total_agents} AI agents that can analyze research papers, assess FAIR compliance, and handle various data processing tasks. How can I assist you?",
            f"Greetings! I'm here to help you work with our {total_agents} intelligent agents. They can analyze papers, check metadata compliance, and much more. What would you like to do?"
        ]

        import random
        return random.choice(greetings)

    def _generate_capabilities_response(self, greeting_data: Dict[str, Any]) -> str:
        """Generate response about available capabilities."""
        total_agents = greeting_data.get("agent_summary", {}).get("total_agents", 0)
        total_ops = greeting_data.get("agent_summary", {}).get("total_operations", 0)
        capabilities = greeting_data.get("capabilities", [])

        # Group by agent
        agents_dict = {}
        for cap in capabilities:
            agent = cap.get("agent", "Unknown")
            if agent not in agents_dict:
                agents_dict[agent] = []
            agents_dict[agent].append(cap.get("operation", "").replace("_", " "))

        response = f"I coordinate {total_agents} specialized agents with {total_ops} total operations:\n\n"

        for agent, ops in list(agents_dict.items())[:5]:  # Show first 5 agents
            response += f"• **{agent}**: {', '.join(ops[:3])}"
            if len(ops) > 3:
                response += f" (+ {len(ops)-3} more)"
            response += "\n"

        if len(agents_dict) > 5:
            response += f"\n...and {len(agents_dict)-5} more agents.\n"

        response += "\nJust tell me what you need, and I'll coordinate the right agents for you!"

        return response

    async def _get_dynamic_greeting(self) -> Dict[str, Any]:
        """Generate dynamic greeting based on available agents."""
        try:
            # Discover active agents from registry
            agents = await self._discover_available_agents()

            print(f"    🤖 Discovered {len(agents)} agents for greeting")

            if not agents or len(agents) == 0:
                print("    ⚠ No agents found - returning startup message")
                return {
                    "message": "Hello! I'm an autonomous agent marketplace. The system is starting up - please try again in a moment.",
                    "capabilities": [],
                    "agent_summary": {}
                }

            # Categorize agents by type
            agent_categories = {
                "analysis": [],
                "compliance": [],
                "llm": [],
                "creation": [],
                "processing": []
            }

            for agent in agents:
                # Get name from kernel_attributes or main level
                kernel_attrs = agent.get("kernel_attributes", {})
                name = kernel_attrs.get("name", "") or agent.get("name", "")
                if not name:
                    name = agent.get("pid", "").split("/")[-1] if agent.get("pid") else "Unknown"

                name_lower = name.lower()

                # Get operations from kernel_attributes or main level
                operations = agent.get("operations", [])
                if not operations and kernel_attrs:
                    operations = kernel_attrs.get("operations", [])

                # Store name for display
                agent["display_name"] = name
                agent["operations"] = operations

                if "analyzer" in name_lower or "parse" in name_lower:
                    agent_categories["analysis"].append(agent)
                elif "fair" in name_lower or "assess" in name_lower:
                    agent_categories["compliance"].append(agent)
                elif "llm" in name_lower or "gpt" in name_lower:
                    agent_categories["llm"].append(agent)
                elif "creator" in name_lower or "create" in name_lower:
                    agent_categories["creation"].append(agent)
                else:
                    agent_categories["processing"].append(agent)

            # Build capability list
            capabilities = []
            for agent in agents:
                agent_name = agent.get("display_name", agent.get("name", "Unknown"))
                operations = agent.get("operations", [])

                # Get cost from kernel_attributes or main level
                kernel_attrs = agent.get("kernel_attributes", {})
                cost = kernel_attrs.get("cost", agent.get("current_cost", 0.0))

                for op in operations:
                    capabilities.append({
                        "agent": agent_name,
                        "operation": op,
                        "cost": cost,
                        "pid": agent.get("pid")
                    })

            # Generate friendly message
            total_agents = len(agents)
            total_operations = sum(len(agent.get("operations", [])) for agent in agents)

            message = f"""Hello! I'm an intelligent dispatcher for an autonomous agent marketplace.

🤖 **Active Agents**: {total_agents} agents with {total_operations} total operations

**Available Capabilities**:"""

            if agent_categories["analysis"]:
                analysis_agents = [a.get("display_name", a.get("name", "Unknown")) for a in agent_categories["analysis"]]
                message += f"\n• 📄 **Paper Analysis**: {', '.join(analysis_agents)}"

            if agent_categories["compliance"]:
                compliance_agents = [a.get("display_name", a.get("name", "Unknown")) for a in agent_categories["compliance"]]
                message += f"\n• ✓ **FAIR Compliance**: {', '.join(compliance_agents)}"

            if agent_categories["llm"]:
                llm_count = len(agent_categories["llm"])
                message += f"\n• 🧠 **LLM Services**: {llm_count} language model endpoint(s)"

            if agent_categories["creation"]:
                creation_agents = [a.get("display_name", a.get("name", "Unknown")) for a in agent_categories["creation"]]
                message += f"\n• 🔧 **Content Creation**: {', '.join(creation_agents)}"

            message += """\n\n**What I can do for you**:
• Analyze research papers (PDF or text)
• Check FAIR metadata compliance
• Coordinate complex workflows across multiple agents
• Estimate costs and manage budgets
• Answer questions using LLM agents

**Examples**:
- "Analyze this paper: [PDF data]"
- "Check FAIR compliance for this metadata"
- "What are the key findings in this research?"

Ask me anything or provide a task to get started!"""

            return {
                "message": message,
                "capabilities": capabilities,
                "agent_summary": {
                    "total_agents": total_agents,
                    "total_operations": total_operations,
                    "categories": {k: len(v) for k, v in agent_categories.items() if v}
                }
            }

        except Exception as e:
            print(f"    ⚠ Dynamic greeting generation failed: {e}")
            # Fallback to static greeting
            return {
                "message": "Hello! I'm an autonomous agent marketplace system. I can help you:\n\n• Analyze research papers (provide a PDF or text)\n• Check FAIR compliance (provide metadata)\n• Coordinate with specialized agents\n\nWhat would you like to do?",
                "capabilities": [],
                "agent_summary": {}
            }

    async def _discover_available_agents(self) -> List[Dict[str, Any]]:
        """Query registry to discover all available agents."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get all registered agents from market endpoint
                response = await client.get(f"{self.registry_url}/market/agents/all")

                if response.status_code != 200:
                    print(f"    ⚠ Registry query failed: {response.status_code}")
                    return []

                data = response.json()
                agents = data.get("data", [])

                print(f"    📊 Found {len(agents)} total registered agents")

                # Filter out the Chat UI itself
                filtered = []
                for a in agents:
                    pid = a.get("pid", "")

                    # Skip self
                    if pid == self.pid:
                        print(f"    ⊗ Skipping self: {pid}")
                        continue

                    # Fetch full FDO record to get name and operations
                    try:
                        fdo_response = await client.get(
                            f"{self.registry_url}/doip/read/fdo/{pid.replace('/', '%2F')}"
                        )

                        if fdo_response.status_code == 200:
                            fdo_data = fdo_response.json().get("data", {})
                            kernel_attrs = fdo_data.get("kernel_attributes", {})

                            # Get name from kernel_attributes
                            name = kernel_attrs.get("name", "Unknown")

                            # Get operations from operation_pids
                            operation_pids = fdo_data.get("operation_pids", [])

                            # Convert operation PIDs to simple names
                            operations = []
                            for op_pid in operation_pids:
                                # Extract operation name from PID like "21.T11148/afdo-xxx-op-extract-text"
                                if "-op-" in op_pid:
                                    op_name = op_pid.split("-op-")[-1].replace("-", "_")
                                    operations.append(op_name)

                            # Enrich agent data
                            a["name"] = name
                            a["display_name"] = name
                            a["operations"] = operations
                            a["kernel_attributes"] = kernel_attrs

                            filtered.append(a)
                            print(f"    ✓ Including: {name} with {len(operations)} operations")

                    except Exception as e:
                        print(f"    ⚠ Failed to fetch FDO for {pid}: {e}")
                        continue

                print(f"    ✅ Returning {len(filtered)} filtered agents")
                return filtered

        except Exception as e:
            print(f"    ⚠ Failed to discover agents: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _interpret_user_intent(self, message: str) -> Dict[str, Any]:
        """
        Interpret user intent using LLM.

        Enhanced to provide better analysis for dynamic planning.
        """

        self.logger.info(self.name, f"🧠 Interpreting user intent: {message[:100]}...")

        if not self.client:
            # Fallback to simple interpretation
            return {
                "query_type": "unclear",
                "complexity": "simple",
                "requires": [],
                "can_answer_directly": True
            }

        prompt = f"""Analyze this user query and determine what they need:

User: {message}

Analyze:
1. Query type: factual_question | how_to | opinion | task_request | analysis_request | greeting | capability_query | unclear
2. Domain: general | science | technology | history | entertainment | other
3. Complexity: simple | moderate | complex
4. Requires: What capabilities are needed to answer this?
   - factual_lookup (Wikipedia, encyclopedia)
   - research (scientific papers, academic sources)
   - books (book references, literature)
   - text_generation (LLM writing, summarization)
   - data_analysis (processing, computation)
   - other

Return JSON:
{{
  "query_type": "factual_question",
  "domain": "general",
  "complexity": "simple",
  "requires": ["factual_lookup"],
  "suggested_approach": "Query Wikipedia for article about the topic",
  "keywords": ["coffee", "beverage"],
  "can_answer_directly": false
}}

Be specific about what's needed to answer the question."""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            interpretation = json.loads(response.choices[0].message.content)

            self.logger.info(self.name, f"   Type: {interpretation.get('query_type')}")
            self.logger.info(self.name, f"   Complexity: {interpretation.get('complexity')}")
            self.logger.info(self.name, f"   Requires: {interpretation.get('requires')}")

            return interpretation

        except Exception as e:
            self.logger.error(self.name, f"❌ Intent interpretation failed: {e}")
            return {
                "query_type": "unclear",
                "complexity": "simple",
                "requires": [],
                "can_answer_directly": True
            }


    async def _estimate_cost(self, workflow: Dict[str, Any], policy: str) -> float:
        """Estimate total workflow cost."""
        total_estimate = 0.0

        for step in workflow.get("steps", []):
            try:
                # Get market info from registry
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{self.registry_url}/market/agents/by_operation/{step['operation']}",
                        params={"sort_by": policy, "limit": 1}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        agents = data.get("data", [])
                        if agents:
                            # Use best agent's current cost
                            total_estimate += agents[0].get("current_cost", 0.05)
            except:
                # Fallback estimate
                total_estimate += 0.10

        return total_estimate

    async def _execute_workflow_internal(
        self,
        workflow: Dict[str, Any],
        budget: float,
        policy: str
    ) -> Dict[str, Any]:
        """Execute planned workflow with budget tracking."""
        budget_manager = BudgetManager(total_budget=budget)
        results = []

        for step in workflow.get("steps", []):
            try:
                result = await self.call_with_alternatives(
                    operation=step["operation"],
                    parameters=step["parameters"],
                    budget=budget_manager,
                    max_retries=2
                )
                results.append({
                    "step": step["operation"],
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                if step.get("required", True):
                    return {
                        "status": "error",
                        "message": f"Required step failed: {step['operation']}",
                        "error": str(e),
                        "budget_summary": budget_manager.get_breakdown()
                    }
                else:
                    results.append({
                        "step": step["operation"],
                        "status": "skipped",
                        "error": str(e)
                    })

        return {
            "status": "success",
            "message": "Workflow completed successfully",
            "workflow": workflow,
            "results": results,
            "budget_summary": budget_manager.get_breakdown()
        }

    async def _estimate_workflow_cost(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate workflow cost without executing."""
        message = parameters.get("message")
        policy = parameters.get("policy", "balanced")

        interpretation = await self._interpret_query(message)
        workflow = await self._plan_workflow(interpretation, parameters)
        estimate = await self._estimate_cost(workflow, policy)

        return {
            "workflow": workflow,
            "estimated_cost": estimate,
            "policy": policy
        }

    async def _execute_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pre-planned workflow."""
        workflow = parameters.get("workflow")
        budget = parameters.get("budget", 1.0)
        policy = parameters.get("policy", "balanced")

        if not workflow:
            raise ValueError("Missing 'workflow' parameter")

        return await self._execute_workflow_internal(workflow, budget, policy)

    async def _suggest_cheaper_alternatives(self, workflow: Dict[str, Any]) -> List[str]:
        """Suggest cheaper alternatives for a workflow."""
        suggestions = [
            "Try using 'cheapest' policy instead of 'balanced'",
            "Reduce the scope of analysis if possible",
            "Increase your budget allocation"
        ]
        return suggestions

    async def _display_message(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Display message to user (for agent-initiated messages)."""
        message = parameters.get("message")
        if not message:
            raise ValueError("Missing 'message'")

        return {
            "displayed": True,
            "message": message
        }

    async def _plan_subtasks(
        self,
        operation: str,
        parameters: Dict[str, Any],
        delegate_types: list
    ) -> list:
        """
        Override: Plan specific subtasks based on query interpretation.

        This replaces hardcoded _plan_workflow() with dynamic planning!

        Args:
            operation: Original operation (receive_user_input)
            parameters: Contains user message
            delegate_types: Types of work to delegate

        Returns:
            List of specific subtasks to delegate
        """

        message = parameters.get("message", "")

        self.logger.info(self.name, f"📋 Planning subtasks for: {message[:100]}...")

        # Step 1: Interpret user intent (enhanced)
        interpretation = await self._interpret_user_intent(message)

        query_type = interpretation.get("query_type")
        requires = interpretation.get("requires", [])
        complexity = interpretation.get("complexity")
        can_answer_directly = interpretation.get("can_answer_directly", False)

        # Step 2: Check if we can answer directly with LLM
        if can_answer_directly or not requires:
            self.logger.info(self.name, "   Can answer directly with LLM - no subtasks needed")
            return []  # Empty list = handle with LLM directly

        # Step 3: Discover available agents
        self.logger.info(self.name, "   🔍 Discovering available agents...")

        try:
            # Use the method from _get_dynamic_greeting that discovers all agents
            all_agents = await self._discover_available_agents()

            # Build capability map
            available_ops = {}
            for agent in all_agents:
                ops = agent.get("operations", [])
                for op in ops:
                    if op not in available_ops:
                        available_ops[op] = []
                    available_ops[op].append({
                        "name": agent.get("display_name") or agent.get("name", "Unknown"),
                        "pid": agent.get("pid"),
                        "cost": agent.get("kernel_attributes", {}).get("cost", 0.01)
                    })

            self.logger.info(self.name, f"   Found {len(all_agents)} agents with {len(available_ops)} operations")

        except Exception as e:
            self.logger.error(self.name, f"   ⚠️ Agent discovery failed: {e}")
            available_ops = {}

        if not available_ops:
            self.logger.info(self.name, "   No agents available - will answer with LLM")
            return []

        # Step 4: Use LLM to plan specific subtasks
        prompt = f"""Plan specific subtasks to answer this query:

User query: {message}

Query analysis:
- Type: {query_type}
- Complexity: {complexity}
- Requires: {requires}

Available operations:
{json.dumps(list(available_ops.keys())[:20], indent=2)}

Plan SPECIFIC subtasks (not "answer the question"):
- Each subtask = concrete operation with specific input
- Good: "get_article_summary about coffee"
- Bad: "explain coffee"

If query is simple factual question:
- Use get_article_summary (Wikipedia)
- Or search_data operations

If query needs research:
- Use search_papers (ArXiv)
- Use search_books (OpenLibrary)

If query needs text generation:
- Use synthesize_text or answer_question

Return JSON:
{{
  "approach": "single_source" | "multi_source" | "research" | "synthesis",
  "subtasks": [
    {{
      "operation": "get_article_summary",
      "parameters": {{"topic": "coffee"}},
      "description": "Get Wikipedia article about coffee",
      "optional": false,
      "fallback_operations": ["search_data", "get_facts"],
      "selection_criteria": "cheapest"
    }}
  ],
  "reasoning": "Why these subtasks"
}}

If query is too vague or unclear, return empty subtasks list."""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            approach = result.get("approach")
            subtasks = result.get("subtasks", [])
            reasoning = result.get("reasoning", "")

            self.logger.info(self.name, f"   ✅ Approach: {approach}")
            self.logger.info(self.name, f"   ✅ Planned {len(subtasks)} subtasks")
            if reasoning:
                self.logger.info(self.name, f"   ℹ️ Reasoning: {reasoning}")

            return subtasks

        except Exception as e:
            self.logger.error(self.name, f"❌ Subtask planning failed: {e}")
            return []  # Empty = fallback to direct LLM answer

    async def _compose_results(
        self,
        operation: str,
        original_parameters: Dict[str, Any],
        subtask_results: list
    ) -> Dict[str, Any]:
        """
        Override: Compose user-friendly response from subtask results.

        Args:
            operation: Original operation
            original_parameters: Contains user message
            subtask_results: Results from delegated subtasks

        Returns:
            User-friendly response
        """

        message = original_parameters.get("message", "")

        self.logger.info(self.name, f"🎨 Composing response from {len(subtask_results)} subtasks")

        # Filter successful results
        successful_results = [
            r for r in subtask_results
            if not r.get("skipped") and not r.get("failed")
        ]

        if not successful_results:
            self.logger.warning(self.name, "⚠️ No successful subtask results")
            # Fallback to direct LLM answer
            return await self._answer_with_llm(message, context="No agents available")

        # Prepare data for synthesis
        sources = []
        for item in successful_results:
            sources.append({
                "source": item.get("agent"),
                "operation": item.get("operation"),
                "content": item.get("result")
            })

        # Use LLM to synthesize into natural answer
        prompt = f"""Synthesize these results into a helpful, natural response:

Original question: {message}

Information gathered:
{json.dumps(sources, indent=2)}

Provide a conversational answer that:
1. Directly answers the user's question
2. Uses information from the sources
3. Is clear and concise
4. Sounds natural (not robotic)
5. Doesn't mention "subtasks" or technical details

Just give the answer as if you're having a conversation."""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )

            answer = response.choices[0].message.content

            return {
                "status": "success",
                "message": answer,
                "sources_used": [s["source"] for s in sources],
                "subtasks_completed": len(successful_results)
            }

        except Exception as e:
            self.logger.error(self.name, f"❌ Composition failed: {e}")

            # Fallback: just return first result
            if successful_results:
                first_result = successful_results[0].get("result", {})
                if isinstance(first_result, dict):
                    result_data = first_result.get("data", first_result)
                    if isinstance(result_data, dict):
                        summary = result_data.get("summary") or result_data.get("message") or str(result_data)
                    else:
                        summary = str(result_data)

                    return {
                        "status": "success",
                        "message": summary[:500],  # Truncate if too long
                        "source": successful_results[0].get("agent")
                    }

            return {
                "status": "error",
                "message": "I encountered an error while composing the response.",
                "error": str(e)
            }

    async def _answer_with_llm(
        self,
        message: str,
        context: str = None
    ) -> Dict[str, Any]:
        """
        Answer question directly with LLM.

        CRITICAL: NEVER suggest commands or agent names to user!

        Args:
            message: User's question
            context: Optional context about why using LLM

        Returns:
            Response dictionary
        """

        self.logger.info(self.name, f"💬 Direct LLM answer: {message[:100]}...")

        # STRICT prompt: NO command suggestions allowed
        prompt = f"""You are a helpful AI assistant.

User question: {message}

ABSOLUTE RULES - YOU MUST FOLLOW THESE:
1. Answer the question directly and naturally
2. NEVER mention agent names (Wikipedia Agent, ArXiv Agent, etc.)
3. NEVER suggest commands (search_wikipedia, get_article_summary, etc.)
4. NEVER say "I recommend using..." or "You can use..."
5. NEVER tell user to do anything manually
6. Just provide a clear, helpful answer
7. If you don't have confident information, say so directly
8. Be conversational and natural

EXAMPLES OF FORBIDDEN RESPONSES:
❌ "Coffee is a drink. I recommend using Wikipedia Agent..."
❌ "You can search for more with the command 'search_wikipedia coffee'"
❌ "Try asking the Wikipedia Agent for details"

EXAMPLES OF CORRECT RESPONSES:
✅ "Coffee is a brewed drink prepared from roasted coffee beans..."
✅ "I don't have detailed information about that specific topic."

Provide your answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )

            answer = response.choices[0].message.content

            # SAFETY CHECK: Remove any accidental command suggestions
            forbidden_phrases = [
                "recommend using",
                "you can use",
                "try the",
                "command",
                "search_",
                "get_",
                "agent"
            ]

            lower_answer = answer.lower()
            for phrase in forbidden_phrases:
                if phrase in lower_answer:
                    self.logger.warning(self.name, f"⚠️ LLM mentioned forbidden phrase: '{phrase}' - removing")
                    # Truncate at the suggestion
                    idx = lower_answer.find(phrase)
                    answer = answer[:idx].strip()
                    # Clean up any trailing punctuation
                    answer = answer.rstrip(".,;:!? ")
                    break

            return {
                "status": "success",
                "message": answer
            }

        except Exception as e:
            self.logger.error(self.name, f"❌ Direct LLM answer failed: {e}")
            return {
                "status": "error",
                "message": "I apologize, but I encountered an error processing your question.",
                "error": str(e)
            }

    def create_app(self) -> FastAPI:
        """Create FastAPI app with static file serving."""
        app = super().create_app()

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Serve static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

            @app.get("/ui")
            async def serve_ui():
                """Serve the chat UI."""
                return FileResponse(str(static_dir / "index.html"))

            def load_trace_with_children(request_id: str, trace_dir: Path) -> Optional[Dict[str, Any]]:
                """
                Recursively load trace and all child traces.

                Args:
                    request_id: The request ID to load
                    trace_dir: Directory containing trace files

                Returns:
                    Trace data with nested child_traces, or None if not found
                """
                import glob

                # Find trace file by request_id
                pattern = str(trace_dir / f"{request_id}_*.json")
                matches = glob.glob(pattern)

                if not matches:
                    return None

                # Load the trace
                with open(matches[0], 'r') as f:
                    trace_data = json.load(f)

                # Find all child traces (traces with this request_id as parent)
                all_traces = glob.glob(str(trace_dir / "req_*.json"))
                child_traces = []

                for trace_path in all_traces:
                    try:
                        with open(trace_path, 'r') as f:
                            child_data = json.load(f)
                            child_summary = child_data.get('summary', {})
                            parent_id = child_summary.get('parent_request_id')

                            if parent_id == request_id:
                                # This is a child trace - recursively load its children
                                child_id = child_summary.get('request_id')
                                child_with_nested = load_trace_with_children(child_id, trace_dir)
                                if child_with_nested:
                                    child_traces.append(child_with_nested)
                    except Exception:
                        pass  # Skip malformed traces

                # Add children to trace data
                if child_traces:
                    trace_data['child_traces'] = child_traces

                    # IMPORTANT: Aggregate agents_involved from all children into parent summary
                    # This makes cascading delegation visible in the trace
                    summary = trace_data.get('summary', {})
                    parent_agents = set(summary.get('agents_involved', []))

                    def collect_agents_recursively(trace):
                        """Recursively collect all agents from trace and its children."""
                        agents = set(trace.get('summary', {}).get('agents_involved', []))
                        for child in trace.get('child_traces', []):
                            agents.update(collect_agents_recursively(child))
                        return agents

                    # Collect all agents from children recursively
                    all_child_agents = set()
                    for child in child_traces:
                        all_child_agents.update(collect_agents_recursively(child))

                    # Update parent's agents_involved list
                    parent_agents.update(all_child_agents)
                    summary['agents_involved'] = sorted(list(parent_agents))

                    # Also aggregate total cost from children
                    total_cost = summary.get('total_cost', 0.0)
                    for child in child_traces:
                        child_cost = child.get('summary', {}).get('total_cost', 0.0)
                        total_cost += child_cost
                    summary['total_cost'] = total_cost

                return trace_data

            @app.get("/trace/{trace_file}")
            async def get_trace(trace_file: str):
                """Serve execution trace file with nested child traces."""
                from fastapi.responses import JSONResponse
                trace_dir = Path("/tmp/afdo_traces")

                # Extract request_id from filename (format: req_xxxxx_timestamp.json)
                request_id = trace_file.split('_')[0] + '_' + trace_file.split('_')[1]

                try:
                    # Load trace with all nested children
                    trace_data = load_trace_with_children(request_id, trace_dir)

                    if not trace_data:
                        return JSONResponse(
                            {"error": "Trace file not found"},
                            status_code=404
                        )

                    return JSONResponse(trace_data)

                except Exception as e:
                    return JSONResponse(
                        {"error": f"Failed to read trace: {str(e)}"},
                        status_code=500
                    )

        return app

if __name__ == "__main__":
    agent = ChatUIAgent()
    print("\n" + "="*60)
    print("🌐 Chat UI is ready!")
    print(f"📱 Open in browser: http://localhost:8001/ui")
    print("="*60 + "\n")
    agent.run()
