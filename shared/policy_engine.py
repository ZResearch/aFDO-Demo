"""
Policy Engine - Interprets and executes policy files.

The engine reads JSON policy files and makes decisions based on rules.
It does NOT contain the policies themselves.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum


class DecisionType(Enum):
    """Types of decisions."""
    HANDLE_ALONE = "handle_alone"
    DECOMPOSE_AND_COORDINATE = "decompose_and_coordinate"
    QUERY_REGISTRY_FOR_HELPER = "query_registry_for_helper"
    QUERY_REGISTRY_FOR_PLANNER = "query_registry_for_planner"
    QUERY_REGISTRY_FOR_COORDINATOR = "query_registry_for_coordinator"
    DELEGATE_FULLY = "delegate_fully"  # DEPRECATED
    COLLABORATE = "collaborate"
    ESCALATE = "escalate"
    CONSULT_FOR_WORKFLOW = "consult_for_workflow"
    SEMANTIC_DISCOVERY = "semantic_discovery"  # NEW: Use registry semantic search + cascade
    CONSULT_LLM_FOR_ROUTING = "consult_llm_for_routing"  # NEW: Ask LLM Consultant for routing advice
    SEQUENCE = "sequence"  # Execute a sequence of steps defined in policy
    CUSTOM = "custom"


class PolicyDecision:
    """Result of policy evaluation."""

    def __init__(
        self,
        decision: DecisionType,
        reasoning: str,
        rule_id: str = None,
        parameters: Dict[str, Any] = None,
        fallback: Dict[str, Any] = None
    ):
        self.decision = decision
        self.reasoning = reasoning
        self.rule_id = rule_id
        self.parameters = parameters or {}
        self.fallback = fallback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "rule_id": self.rule_id,
            "parameters": self.parameters,
            "fallback": self.fallback
        }


class PolicyEngine:
    """
    Policy Engine - Interprets policy JSON files and executes decisions.

    This is the INTERPRETER. The policies are DATA (JSON files).
    """

    def __init__(
        self,
        agent_pid: str,
        agent_capabilities: List[str],
        policy_file: str = None,
        policy_dict: Dict[str, Any] = None
    ):
        """
        Initialize policy engine.

        Args:
            agent_pid: Agent's PID
            agent_capabilities: List of operations agent can perform
            policy_file: Path to policy JSON file
            policy_dict: Policy as dictionary (from FDO record)
        """
        self.agent_pid = agent_pid
        self.agent_capabilities = agent_capabilities
        self.logger = logging.getLogger(f"PolicyEngine[{agent_pid}]")

        # Load policy
        if policy_dict:
            self.policy = policy_dict
            self.logger.info(f"📋 Loaded policy from dict: {self.policy.get('policy_id')}")
        elif policy_file:
            self.policy = self._load_policy_file(policy_file)
            self.logger.info(f"📋 Loaded policy from file: {policy_file}")
        else:
            raise ValueError("Must provide either policy_file or policy_dict")

        # Sort rules by priority
        self.rules = sorted(
            self.policy.get("rules", []),
            key=lambda r: r.get("priority", 0),
            reverse=True
        )

        self.default_action = self.policy.get("default_action", "handle_alone")

    def _load_policy_file(self, policy_file: str) -> Dict[str, Any]:
        """Load policy from JSON file."""
        try:
            with open(policy_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load policy file {policy_file}: {e}")
            raise

    async def decide(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> PolicyDecision:
        """
        Make a decision based on policy rules.

        Args:
            operation: Operation being requested
            parameters: Operation parameters
            context: Additional context (budget, caller, etc.)

        Returns:
            PolicyDecision
        """
        context = context or {}

        # Build evaluation context
        eval_context = self._build_evaluation_context(operation, parameters, context)

        self.logger.info(f"🎯 Evaluating policy for operation: {operation}")
        self.logger.debug(f"   Context: {eval_context}")

        # Evaluate rules in priority order
        for rule in self.rules:
            if self._evaluate_conditions(rule.get("conditions", {}), eval_context):
                self.logger.info(f"✅ Matched rule: {rule['rule_id']}")
                return self._create_decision_from_rule(rule, eval_context)

        # No rules matched - use default
        self.logger.info(f"⚠️ No rules matched, using default: {self.default_action}")
        return PolicyDecision(
            decision=DecisionType(self.default_action),
            reasoning="No policy rules matched - using default action"
        )

    def _build_evaluation_context(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for policy evaluation."""

        # Assess complexity
        complexity = self._assess_complexity(parameters)

        # Assess if query requires synthesis (Task: Enable multi-level cascading)
        query_requires_synthesis = self._query_requires_synthesis(parameters)

        # Get budget, defaulting to infinity if not provided or None
        budget = context.get("budget")
        if budget is None:
            budget = float('inf')

        return {
            "operation": operation,
            "parameters": parameters,  # Added for message_pattern matching
            "has_capability": operation in self.agent_capabilities,
            "complexity": complexity,
            "parameter_count": len(parameters),
            "query_requires_synthesis": query_requires_synthesis,
            "budget": budget,
            "budget_available": budget > 0.1,
            "caller_pid": context.get("caller_pid"),
            "custom": context.get("custom", {})
        }

    def _assess_complexity(self, parameters: Dict[str, Any]) -> str:
        """Assess task complexity based on parameters."""
        param_count = len(parameters)
        has_nested = any(isinstance(v, (dict, list)) for v in parameters.values())

        if param_count <= 2 and not has_nested:
            return "simple"
        elif param_count <= 4:
            return "moderate"
        elif param_count <= 6:
            return "complex"
        else:
            return "very_complex"

    def _query_requires_synthesis(self, parameters: Dict[str, Any]) -> bool:
        """
        Assess if query requires synthesis, comparison, or reasoning beyond simple lookup.

        Enables multi-level cascading: Data source agents can delegate synthesis
        queries to LLM agents via SEMANTIC_DISCOVERY.
        """
        # Extract query text from parameters
        query = parameters.get("query") or parameters.get("message") or ""
        if not isinstance(query, str):
            return False

        query_lower = query.lower()

        # Synthesis indicators: compare, analyze, explain, evaluate
        synthesis_keywords = [
            "compare", "versus", "vs", "difference between",
            "analyze", "analysis", "evaluate", "assessment",
            "explain", "why", "how does", "what makes",
            "synthesize", "summarize", "relate",
            "implications", "impact", "effect",
            "pros and cons", "advantages", "disadvantages",
            "better", "worse", "best", "optimal"
        ]

        return any(keyword in query_lower for keyword in synthesis_keywords)

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if conditions match context.

        This is where the engine INTERPRETS the policy.
        """
        # Check operation match
        if "operation" in conditions:
            op_condition = conditions["operation"]
            if isinstance(op_condition, list):
                if context["operation"] not in op_condition:
                    return False
            elif context["operation"] != op_condition:
                return False

        # Check has_capability
        if "has_capability" in conditions:
            if context["has_capability"] != conditions["has_capability"]:
                return False

        # Check complexity
        if "complexity" in conditions:
            if context["complexity"] != conditions["complexity"]:
                return False

        # Check query_requires_synthesis (Task: Enable multi-level cascading)
        if "query_requires_synthesis" in conditions:
            if context.get("query_requires_synthesis", False) != conditions["query_requires_synthesis"]:
                return False

        # Check parameter_count
        if "parameter_count" in conditions:
            pc = conditions["parameter_count"]
            operator = pc["operator"]
            value = pc["value"]
            actual = context["parameter_count"]

            if operator == ">":
                if not (actual > value):
                    return False
            elif operator == "<":
                if not (actual < value):
                    return False
            elif operator == ">=":
                if not (actual >= value):
                    return False
            elif operator == "<=":
                if not (actual <= value):
                    return False
            elif operator == "==":
                if not (actual == value):
                    return False

        # Check budget_threshold
        if "budget_threshold" in conditions:
            if context["budget"] < conditions["budget_threshold"]:
                return False

        # Check message_pattern (for user input matching)
        if "message_pattern" in conditions:
            import re
            # Get message from parameters (for receive_user_input operation)
            message = context.get("parameters", {}).get("message", "")
            pattern = conditions["message_pattern"]

            # Use case-insensitive regex matching
            if not re.search(pattern, message, re.IGNORECASE):
                return False

            self.logger.debug(f"   ✓ Message pattern matched: '{pattern}' in '{message[:50]}'")

        # Check custom conditions (agent-specific)
        if "custom" in conditions:
            # Custom conditions are passed to agent for evaluation
            # This allows agents to define their own condition logic
            pass

        # All conditions passed
        return True

    def _create_decision_from_rule(
        self,
        rule: Dict[str, Any],
        context: Dict[str, Any]
    ) -> PolicyDecision:
        """Create PolicyDecision from matched rule."""

        action = rule["action"]
        action_type = action["type"]

        # Map action type to DecisionType
        decision = DecisionType(action_type)

        # Extract parameters
        parameters = action.get("parameters", {}).copy()

        # Process registry_query if present
        if "registry_query" in parameters:
            query = parameters["registry_query"].copy()

            # Replace "from_request" with actual operation
            if query.get("operation") == "from_request":
                query["operation"] = context["operation"]

            # Replace "from_analysis" with analyzed needs
            if query.get("operation") == "from_analysis":
                # Agent will analyze and fill this in
                query["operation"] = "to_be_determined"

            parameters["registry_query"] = query

        return PolicyDecision(
            decision=decision,
            reasoning=action.get("reasoning", rule.get("description", "")),
            rule_id=rule["rule_id"],
            parameters=parameters,
            fallback=action.get("fallback")
        )

    def get_policy_info(self) -> Dict[str, Any]:
        """Get policy metadata."""
        return {
            "policy_id": self.policy.get("policy_id"),
            "policy_version": self.policy.get("policy_version"),
            "description": self.policy.get("description"),
            "rule_count": len(self.rules),
            "default_action": self.default_action
        }
