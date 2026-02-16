"""FAIR Assessor aFDO - Evaluates FAIR compliance of research data and metadata."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
from shared.afdo_base import aFDOBase
from agents.fair_assessor.fair_criteria import FAIRCriteria


class FAIRAssessorAgent(aFDOBase):
    """
    FAIR Assessor aFDO.

    Evaluates datasets and research outputs for FAIR compliance.
    Based on CIKM 2025 methodology.

    Capabilities:
    - Complete FAIR assessment (F, A, I, R principles)
    - Metadata quality scoring
    - Improvement suggestions
    """

    def __init__(self):
        super().__init__(
            name="FAIR Assessor",
            fdo_type="21.T11148/type-quality-assessor-v1",
            operations=[
                "assess_fairness",
                "score_metadata",
                "suggest_improvements"
            ],
            port=8005,
            cost=0.02,
            has_llm=False,
            specialization="FAIR_compliance"
        )

        self.criteria = FAIRCriteria()

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Evaluates FAIR compliance of research data and metadata",
            "version": "2.0.0",
            "agent_role": "task_agent",
            "based_on": "CIKM 2025 - FAIR Data Assessment Using LLMs",
            "capabilities": {
                "assess_fairness": {
                    "description": "Complete FAIR assessment with scores and actionable suggestions",
                    "input_schema": {
                        "metadata": "dict with dataset/paper metadata",
                        "context": "optional context dict"
                    },
                    "output_schema": {
                        "overall_score": "float 0-1",
                        "findable_score": "float 0-1",
                        "accessible_score": "float 0-1",
                        "interoperable_score": "float 0-1",
                        "reusable_score": "float 0-1",
                        "detailed_scores": "dict with principle-level scores",
                        "suggestions": "list of improvement actions"
                    },
                    "estimated_duration": "1-3s",
                    "estimated_cost": "$0.02",
                    "requires_llm": False
                },
                "score_metadata": {
                    "description": "Score metadata quality on FAIR principles",
                    "input_schema": {
                        "metadata": "dict with metadata to evaluate"
                    },
                    "output_schema": {
                        "metadata_quality_score": "float 0-1",
                        "completeness": "float 0-1",
                        "richness": "float 0-1"
                    },
                    "estimated_duration": "0.5-1s",
                    "estimated_cost": "$0.02"
                },
                "suggest_improvements": {
                    "description": "Provide actionable improvement recommendations",
                    "input_schema": {
                        "assessment": "dict from assess_fairness",
                        "priority": "string (high/medium/low)"
                    },
                    "output_schema": {
                        "suggestions": "prioritized list of improvements",
                        "quick_wins": "list of easy improvements",
                        "long_term": "list of strategic improvements"
                    },
                    "estimated_duration": "0.5-1s",
                    "estimated_cost": "$0.02"
                }
            },
            "principles_assessed": {
                "Findable": ["F1: Global identifier", "F2: Rich metadata", "F3: Metadata in registry", "F4: Searchable"],
                "Accessible": ["A1: Retrievable via protocol", "A2: Metadata persistence"],
                "Interoperable": ["I1: Formal language", "I2: FAIR vocabularies", "I3: Qualified references"],
                "Reusable": ["R1: Usage license", "R2: Provenance", "R3: Community standards", "R4: Domain-relevant"]
            },
            "performance_characteristics": {
                "typical_latency": "1-3s",
                "max_concurrent_requests": 50,
                "deterministic": True
            },
            "llm_capable": False,
            "methodology": "Rule-based assessment with weighted scoring per CIKM 2025 methodology"
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "FAIR Assessor Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Evaluates metadata against FAIR principles using rule-based criteria"
            },

            "capabilities": {
                "assess_fairness": {
                    "operation_type": "assessment",

                    "input_schema": {
                        "type": "object",
                        "required": ["metadata"],
                        "properties": {
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "pid": {"type": "string"},
                                    "title": {"type": "string"},
                                    "authors": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "keywords": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "license": {"type": "string"},
                                    "provenance": {"type": "object"}
                                }
                            },
                            "context": {
                                "type": "object",
                                "properties": {
                                    "domain": {"type": "string"}
                                }
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["overall_score", "compliance_level"],
                        "properties": {
                            "overall_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "findable_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "accessible_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "interoperable_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "reusable_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "compliance_level": {
                                "type": "string",
                                "enum": ["Low", "Medium", "High", "Excellent"]
                            },
                            "suggestions": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "assessed_by": {"type": "string"},
                            "assessment_method": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 10,
                        "rate_limit": 100
                    },

                    "examples": [
                        {
                            "input": {
                                "metadata": {
                                    "pid": "21.T11148/example-001",
                                    "title": "Research Paper",
                                    "authors": ["Jane Smith"],
                                    "keywords": ["AI", "ML"],
                                    "license": "CC-BY-4.0"
                                }
                            },
                            "output": {
                                "overall_score": 0.75,
                                "findable_score": 0.8,
                                "accessible_score": 0.7,
                                "interoperable_score": 0.6,
                                "reusable_score": 0.9,
                                "compliance_level": "High",
                                "suggestions": [],
                                "assessed_by": "21.T11148/afdo-fair-assessor",
                                "assessment_method": "Rule-based FAIR criteria"
                            }
                        }
                    ]
                },

                "score_metadata": {
                    "operation_type": "assessment",

                    "input_schema": {
                        "type": "object",
                        "required": ["metadata"],
                        "properties": {
                            "metadata": {"type": "object"}
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["metadata_quality_score", "completeness", "richness"],
                        "properties": {
                            "metadata_quality_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "completeness": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "richness": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 5,
                        "rate_limit": 200
                    },

                    "examples": []
                },

                "suggest_improvements": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "required": ["metadata"],
                        "properties": {
                            "metadata": {"type": "object"},
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "default": "medium"
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["suggestions"],
                        "properties": {
                            "suggestions": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "quick_wins": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "long_term": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },

                    "constraints": {
                        "timeout_seconds": 5,
                        "rate_limit": 100
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": ["jsonschema==4.20.0"],
                "resource_requirements": {
                    "memory_mb": 128,
                    "cpu_cores": 0.25
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
        """Handle FAIR assessment operations."""
        print(f"✓ Processing '{operation}' request from {caller_pid}")

        # Get metadata to assess
        metadata = parameters.get("metadata")
        if not metadata:
            raise ValueError("Missing 'metadata' parameter")

        # Route to appropriate handler
        if operation == "assess_fairness":
            return await self._assess_fairness(metadata)

        elif operation == "score_metadata":
            return await self._score_metadata(metadata)

        elif operation == "suggest_improvements":
            return await self._suggest_improvements(metadata)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _assess_fairness(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Perform complete FAIR assessment."""
        assessment = self.criteria.assess_overall(metadata)

        # Add assessor info
        assessment["assessed_by"] = self.pid
        assessment["assessment_method"] = "Rule-based FAIR criteria"

        print(f"  → Overall FAIR score: {assessment['overall_score']} ({assessment['compliance_level']})")

        return assessment

    async def _score_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Score metadata quality (without detailed suggestions)."""
        assessment = self.criteria.assess_overall(metadata)

        return {
            "overall_score": assessment["overall_score"],
            "compliance_level": assessment["compliance_level"],
            "principle_scores": assessment["principle_scores"],
            "assessed_by": self.pid
        }

    async def _suggest_improvements(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Provide improvement suggestions."""
        assessment = self.criteria.assess_overall(metadata)

        # Flatten suggestions
        all_suggestions = []
        for principle, suggestions in assessment["suggestions"].items():
            for suggestion in suggestions:
                all_suggestions.append({
                    "principle": principle,
                    "suggestion": suggestion
                })

        # Prioritize by principle score (lower score = higher priority)
        scores = assessment["principle_scores"]
        priorities = {
            "findable": 1 if scores["findable"] < 0.5 else 2 if scores["findable"] < 0.8 else 3,
            "accessible": 1 if scores["accessible"] < 0.5 else 2 if scores["accessible"] < 0.8 else 3,
            "interoperable": 1 if scores["interoperable"] < 0.5 else 2 if scores["interoperable"] < 0.8 else 3,
            "reusable": 1 if scores["reusable"] < 0.5 else 2 if scores["reusable"] < 0.8 else 3
        }

        for suggestion in all_suggestions:
            suggestion["priority"] = priorities[suggestion["principle"]]

        # Sort by priority
        all_suggestions.sort(key=lambda x: x["priority"])

        return {
            "total_suggestions": len(all_suggestions),
            "suggestions": all_suggestions,
            "current_score": assessment["overall_score"],
            "improvement_potential": round(1.0 - assessment["overall_score"], 2),
            "assessed_by": self.pid
        }


if __name__ == "__main__":
    agent = FAIRAssessorAgent()
    agent.run()
