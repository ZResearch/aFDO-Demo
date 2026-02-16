"""
Policy Action Definitions

Defines all valid policy actions and their behavior.
"""

from enum import Enum
from typing import Dict, Any


class PolicyActionType(Enum):
    """Valid policy action types."""

    # Core actions
    HANDLE_ALONE = "handle_alone"
    DECOMPOSE_AND_COORDINATE = "decompose_and_coordinate"
    QUERY_REGISTRY_FOR_HELPER = "query_registry_for_helper"
    CONSULT_FOR_WORKFLOW = "consult_for_workflow"

    # Legacy (to be removed)
    DELEGATE_FULLY = "delegate_fully"  # DEPRECATED - causes chains


# Action definitions
POLICY_ACTIONS = {
    "handle_alone": {
        "description": "Execute operation using own capabilities",
        "requires_registry": False,
        "does_work": True,
        "delegates": False,
        "example": "Agent handles greeting directly"
    },

    "decompose_and_coordinate": {
        "description": """
        Break task into subtasks, delegate specific subtasks, compose results.

        Pattern:
        1. Agent does its own work (analysis, planning)
        2. Agent identifies specific subtasks to delegate
        3. Agent delegates each subtask with specific input
        4. Agent processes results from subtasks
        5. Agent returns composed final result

        Key: Agent does WORK, not just passes task along!
        """,
        "requires_registry": True,
        "does_work": True,
        "delegates": True,
        "delegation_type": "subtasks_only",
        "example": """
        Chat UI receives: "Explain quantum computing research"

        Chat UI does:
        1. [MY WORK] Analyzes request → needs history + papers
        2. [MY WORK] Plans subtasks:
           - Subtask A: "get_article_summary('quantum computing')"
           - Subtask B: "search_papers('quantum computing')"
        3. [DELEGATE] Subtask A → Wikipedia (specific input!)
        4. [DELEGATE] Subtask B → ArXiv (specific input!)
        5. [MY WORK] Composes: history + papers → explanation
        6. [MY WORK] Returns: final answer
        """
    },

    "query_registry_for_helper": {
        "description": """
        Find agent to help with SPECIFIC subtask (not whole task).

        Used when agent needs help with one specific operation.
        Agent still does its own work before/after delegation.
        """,
        "requires_registry": True,
        "does_work": True,
        "delegates": True,
        "delegation_type": "single_subtask",
        "parameters": {
            "registry_query": {
                "operations": ["list", "Operations to search for"],
                "fallback_operations": ["list", "Try these if primary not found"],
                "selection_criteria": ["string", "cheapest|fastest|balanced|best_reputation"]
            }
        },
        "fallback_required": True,
        "example": """
        PDF Parser receives: scanned PDF

        PDF Parser does:
        1. [MY WORK] Detects: PDF is scanned, needs OCR
        2. [QUERY] "Who has operation 'ocr_text'?"
        3. [DELEGATE] OCR subtask → OCR Agent
        4. [MY WORK] Receives text, processes it
        5. [MY WORK] Returns: processed text
        """
    },

    "consult_for_workflow": {
        "description": """
        Ask LLM consultant to generate workflow for very complex task.

        Used when task is so complex agent doesn't know how to break it down.
        Consultant returns workflow (JSON), agent executes workflow.
        """,
        "requires_registry": True,
        "does_work": True,
        "delegates": True,
        "delegation_type": "workflow_generation",
        "parameters": {
            "consultant_query": {
                "operations": ["generate_workflow", "plan_task"],
                "selection_criteria": "balanced"
            }
        },
        "fallback_required": True
    },

    # DEPRECATED - DO NOT USE
    "delegate_fully": {
        "description": "DEPRECATED - Delegates entire task, creates delegation chains",
        "deprecated": True,
        "reason": "Creates bureaucracy pattern where only last agent does work",
        "replacement": "Use 'decompose_and_coordinate' instead",
        "warning": "This action will be removed in future version"
    }
}


def validate_policy_action(action: Dict[str, Any]) -> tuple:
    """
    Validate policy action definition.

    Returns:
        (is_valid, error_message)
    """

    action_type = action.get("type")

    if not action_type:
        return False, "Action must have 'type' field"

    if action_type not in POLICY_ACTIONS:
        return False, f"Unknown action type: {action_type}"

    action_def = POLICY_ACTIONS[action_type]

    # Check if deprecated
    if action_def.get("deprecated"):
        return False, f"Action '{action_type}' is deprecated: {action_def.get('reason')}"

    # Check if fallback required
    if action_def.get("fallback_required") and "fallback" not in action:
        return False, f"Action '{action_type}' requires fallback strategy"

    # Check parameters if required
    if "parameters" in action_def:
        action_params = action.get("parameters", {})
        required_params = action_def["parameters"]

        for param_name, param_def in required_params.items():
            if param_name not in action_params:
                return False, f"Action '{action_type}' requires parameter: {param_name}"

    return True, ""
