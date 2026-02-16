"""Workflow planning logic for Scientific NL Handler."""

from typing import Dict, Any, List, Optional


class WorkflowPlanner:
    """Plans multi-agent workflows based on user queries."""

    @staticmethod
    def analyze_query(query: str, llm_response: str) -> Dict[str, Any]:
        """
        Analyze query and LLM interpretation to plan workflow.

        Args:
            query: User's natural language query
            llm_response: LLM's interpretation

        Returns:
            Workflow plan
        """
        query_lower = query.lower()

        # Determine if PDF processing needed
        needs_pdf = any(word in query_lower for word in ["paper", "pdf", "document", "article"])

        # Determine if FAIR assessment needed
        needs_fair = any(word in query_lower for word in ["fair", "compliance", "metadata", "quality"])

        # Determine if analysis needed
        needs_analysis = any(word in query_lower for word in ["analyze", "summary", "explain", "assess"])

        workflow = {
            "steps": [],
            "required_agents": [],
            "estimated_cost": 0.0
        }

        # Build workflow steps
        if needs_pdf:
            workflow["steps"].append({
                "step": 1,
                "action": "extract_pdf",
                "agent_type": "document_processor",
                "operation": "extract_text"
            })
            workflow["required_agents"].append("document_processor")
            workflow["estimated_cost"] += 0.05

        if needs_fair:
            workflow["steps"].append({
                "step": len(workflow["steps"]) + 1,
                "action": "assess_fair",
                "agent_type": "compliance_checker",
                "operation": "assess_fairness"
            })
            workflow["required_agents"].append("compliance_checker")
            workflow["estimated_cost"] += 0.02

        if needs_analysis:
            workflow["steps"].append({
                "step": len(workflow["steps"]) + 1,
                "action": "analyze",
                "agent_type": "llm_service",
                "operation": "analyze_scientific_text"
            })
            workflow["required_agents"].append("llm_service")
            workflow["estimated_cost"] += 0.01

        # If no specific workflow, default to general response
        if len(workflow["steps"]) == 0:
            workflow["steps"].append({
                "step": 1,
                "action": "respond",
                "method": "direct_llm"
            })

        return workflow
