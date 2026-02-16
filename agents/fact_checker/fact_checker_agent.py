"""Fact Checker Agent - Multi-Source Verification aFDO

This agent verifies claims by gathering evidence from multiple independent sources
and synthesizing verification results. All behavior is policy-driven - no hardcoded logic.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
from shared.afdo_base import aFDOBase


class FactCheckerAgent(aFDOBase):
    """
    Fact Checker Agent aFDO.

    Verifies claims through multi-source validation:
    - Gathers evidence from multiple independent data sources
    - Synthesizes verification with confidence scoring
    - All delegation logic driven by policy (no hardcoding)

    Capabilities:
    - verify_fact: Verify a factual claim with confidence score
    - cross_validate: Cross-validate information across sources
    - check_claim: Quick claim verification
    """

    def __init__(self):
        super().__init__(
            name="Fact Checker Agent",
            fdo_type="21.T11148/type-fact-checker-v1",
            operations=[
                "receive_query",      # Universal entry point (delegates to verify_fact)
                "verify_fact",
                "cross_validate",
                "check_claim"
            ],
            port=8013,
            cost=0.05,  # Base coordination cost (delegations add to this)
            has_llm=False,  # No built-in LLM, delegates to others
            specialization="fact_verification"
        )

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Multi-source fact verification through policy-driven delegation",
            "version": "1.0.0",
            "agent_role": "composite_agent",
            "specialization": "fact_verification",
            "verification_approach": "multi_source_triangulation",
            "capabilities": {
                "verify_fact": {
                    "description": "Verify factual claims with confidence scoring",
                    "multi_source": True,
                    "synthesis": True,
                    "estimated_duration": "3-8s",
                    "estimated_cost": "$0.05-0.15 (depends on sources consulted)"
                },
                "cross_validate": {
                    "description": "Cross-validate information across multiple sources",
                    "multi_source": True,
                    "estimated_duration": "3-8s",
                    "estimated_cost": "$0.05-0.15"
                },
                "check_claim": {
                    "description": "Quick claim verification",
                    "multi_source": True,
                    "estimated_duration": "2-5s",
                    "estimated_cost": "$0.03-0.10"
                }
            },
            "delegation_strategy": "policy_driven_multi_source",
            "policy_file": "agents/fact_checker/policy.json"
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""
        return {
            "agent_info": {
                "name": "Fact Checker Agent",
                "version": "1.0.0",
                "agent_type": "composite",
                "description": (
                    "Multi-source fact verification and claim validation agent. "
                    "Specialized in verifying factual statements, checking if claims are true, "
                    "validating assertions, confirming information accuracy, and answering "
                    "'is X true?' type questions. Uses multiple independent sources to "
                    "cross-reference facts and provide confidence-scored verification. "
                    "Best for queries like: 'is X Y?', 'did X happen?', 'was X the Y?', "
                    "'verify that X', 'check if X is true', 'confirm whether X'. "
                    "All delegation behavior is policy-driven without hardcoded logic."
                )
            },
            "capabilities": {
                "receive_query": {
                    "operation_type": "assessment",
                    "description": "Verifies factual claims, statements, and assertions by consulting multiple independent sources. Specializes in validating claims from scientific publications, research papers, academic studies, journal articles, and news reports. Answers verification questions like 'is X Y?', 'is it true that X?', 'did X happen?', 'the paper/study/article/research claims X, is this correct?', 'does the scientific evidence support X?', 'verify this claim from the publication', 'are the research findings accurate?'. Uses multi-source triangulation across research databases, encyclopedias, scientific papers, and authoritative sources to provide confidence-scored verification with evidence from multiple independent sources.",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query requiring fact verification"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "answer": {
                                "type": "string",
                                "description": "Synthesized answer with verification status"
                            },
                            "verified": {"type": "boolean"},
                            "confidence": {"type": "number"},
                            "sources": {"type": "array"}
                        }
                    }
                },
                "verify_fact": {
                    "operation_type": "assessment",
                    "description": "Verify if a factual claim or statement is true by consulting multiple independent sources. Use this for 'is X true?' questions, claim validation, fact-checking, and confirming whether statements are accurate. Returns verified status with confidence score.",
                    "input_schema": {
                        "type": "object",
                        "required": ["claim"],
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": "The factual claim to verify"
                            },
                            "confidence_threshold": {
                                "type": "number",
                                "default": 0.7,
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Minimum confidence required for verification"
                            },
                            "max_sources": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 2,
                                "maximum": 10,
                                "description": "Maximum number of sources to consult"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["claim", "verified", "confidence", "evidence"],
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": "The original claim"
                            },
                            "verified": {
                                "type": "boolean",
                                "description": "Whether the claim was verified"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Confidence score (0-1)"
                            },
                            "evidence": {
                                "type": "array",
                                "description": "Evidence gathered from sources",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "source_pid": {"type": "string"},
                                        "data": {"type": "object"},
                                        "supports_claim": {"type": "boolean"}
                                    }
                                }
                            },
                            "synthesis": {
                                "type": "string",
                                "description": "Synthesized verification explanation"
                            },
                            "sources_consulted": {
                                "type": "integer",
                                "description": "Number of sources successfully consulted"
                            }
                        }
                    },
                    "constraints": {
                        "timeout_seconds": 30,
                        "rate_limit": 10
                    }
                },
                "cross_validate": {
                    "operation_type": "assessment",
                    "description": "Cross-validate information by comparing data from multiple specified sources. Checks consistency and agreement across sources to assess information reliability.",
                    "input_schema": {
                        "type": "object",
                        "required": ["claim", "sources"],
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": "Claim to cross-validate"
                            },
                            "sources": {
                                "type": "array",
                                "description": "Preferred sources to use",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["claim", "validated", "consistency_score"],
                        "properties": {
                            "claim": {"type": "string"},
                            "validated": {"type": "boolean"},
                            "consistency_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "source_results": {"type": "array"}
                        }
                    }
                },
                "check_claim": {
                    "operation_type": "assessment",
                    "description": "Quick claim verification for simple factual statements. Faster than full verification but less comprehensive. Use for straightforward 'is X Y?' questions that need quick validation.",
                    "input_schema": {
                        "type": "object",
                        "required": ["claim"],
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": "Claim to quickly check"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["claim", "likely_true", "confidence"],
                        "properties": {
                            "claim": {"type": "string"},
                            "likely_true": {"type": "boolean"},
                            "confidence": {"type": "number"}
                        }
                    }
                }
            },
            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [],
                "resource_requirements": {
                    "memory_mb": 256,
                    "cpu_cores": 0.5
                }
            },
            "agent_attributes": {
                "has_llm": False,
                "autonomy_level": "composite",
                "can_delegate": True,
                "delegation_strategy": "multi_source_policy_driven"
            }
        }

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle operations - all behavior is policy-driven.

        This method validates input and routes to policy engine.
        NO hardcoded delegation logic - all in policy.json.
        """
        self.logger.info(self.name, f"📋 Received {operation} from {caller_pid}")

        if operation == "receive_query":
            # Universal entry point - extract claim from query and verify
            query = parameters.get("query") or parameters.get("message")
            if not query:
                raise ValueError("Missing 'query' or 'message' parameter")
            # Convert query to claim format and verify
            return await self._verify_fact({"claim": query}, caller_pid)
        elif operation == "verify_fact":
            return await self._verify_fact(parameters, caller_pid)
        elif operation == "cross_validate":
            return await self._cross_validate(parameters, caller_pid)
        elif operation == "check_claim":
            return await self._check_claim(parameters, caller_pid)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _verify_fact(
        self,
        parameters: Dict[str, Any],
        caller_pid: str
    ) -> Dict[str, Any]:
        """
        Verify fact through policy-driven multi-source validation.

        NO hardcoded logic - delegates to policy engine which:
        1. Gathers evidence from multiple sources (via policy)
        2. Synthesizes verification (via policy)
        3. Returns structured result
        """
        # Validate input
        claim = parameters.get("claim")
        if not claim:
            raise ValueError("Missing required parameter: claim")

        confidence_threshold = parameters.get("confidence_threshold", 0.7)
        max_sources = parameters.get("max_sources", 5)

        self.logger.info(
            self.name,
            f"🔍 Verifying claim: '{claim[:50]}...' (threshold: {confidence_threshold})"
        )

        # Route to policy engine - all delegation logic in policy
        result = await self.handle_operation_with_policy(
            operation="verify_fact",
            caller_pid=caller_pid,
            parameters={
                "claim": claim,
                "confidence_threshold": confidence_threshold,
                "max_sources": max_sources
            }
        )

        return result

    async def _cross_validate(
        self,
        parameters: Dict[str, Any],
        caller_pid: str
    ) -> Dict[str, Any]:
        """Cross-validate through policy-driven multi-source checking."""
        claim = parameters.get("claim")
        sources = parameters.get("sources", [])

        if not claim:
            raise ValueError("Missing required parameter: claim")

        self.logger.info(
            self.name,
            f"🔄 Cross-validating: '{claim[:50]}...' across {len(sources) if sources else 'all'} sources"
        )

        # Route to policy engine
        result = await self.handle_operation_with_policy(
            operation="cross_validate",
            caller_pid=caller_pid,
            parameters={
                "claim": claim,
                "sources": sources
            }
        )

        return result

    async def _check_claim(
        self,
        parameters: Dict[str, Any],
        caller_pid: str
    ) -> Dict[str, Any]:
        """Quick claim check through policy-driven verification."""
        claim = parameters.get("claim")

        if not claim:
            raise ValueError("Missing required parameter: claim")

        self.logger.info(
            self.name,
            f"⚡ Quick check: '{claim[:50]}...'"
        )

        # Route to policy engine
        result = await self.handle_operation_with_policy(
            operation="check_claim",
            caller_pid=caller_pid,
            parameters={"claim": claim}
        )

        return result


if __name__ == "__main__":
    agent = FactCheckerAgent()
    agent.run()
