"""Paper Analyzer aFDO - Autonomous composite agent for research paper analysis."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
from typing import Dict, Any, Optional
from openai import OpenAI

from shared.afdo_base import aFDOBase
from shared.budget_manager import BudgetManager
from agents.paper_analyzer.analysis_templates import AnalysisTemplates

class PaperAnalyzerAgent(aFDOBase):
    """
    Paper Analyzer aFDO.

    Autonomous composite agent for research paper analysis.

    Capabilities:
    - Complete paper analysis (methodology, findings, reproducibility)
    - Autonomously discovers and hires service providers
    - Budget-aware with cost tracking
    - Automatic failure recovery with alternatives
    - Has built-in LLM for synthesis
    - Can self-improve through Creator agent
    """

    def __init__(self):
        super().__init__(
            name="Paper Analyzer",
            fdo_type="21.T11148/type-workflow-coordinator-v1",
            operations=[
                "analyze_paper",
                "analyze_paper_budget",  # New budget-aware version
                "extract_key_findings",
                "assess_methodology",
                "check_reproducibility"
            ],
            port=8003,
            cost=0.05,  # Reduced - only coordination fee
            has_llm=True,
            llm_model="gpt-4o",
            specialization="research_papers",
            selection_policy="balanced"  # Use balanced policy
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

        self.templates = AnalysisTemplates()

        # Performance tracking (for self-improvement)
        self.performance_stats = {
            "total_analyses": 0,
            "successful": 0,
            "failed": 0
        }

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Autonomous composite agent for research paper analysis",
            "version": "2.0.0",
            "agent_role": "composite_agent",
            "decision_policy": "autonomous",
            "specialization": "research_papers",
            "model": "gpt-4o",
            "capabilities": {
                "analyze_paper": {
                    "description": "Comprehensive paper analysis including methodology, findings, and FAIR compliance",
                    "input_schema": {
                        "pdf_data": "base64 encoded PDF content (optional if text provided)",
                        "text": "extracted text (optional if pdf_data provided)",
                        "metadata": "dict with paper metadata (optional)"
                    },
                    "output_schema": {
                        "methodology": "detailed methodology analysis",
                        "key_findings": "extracted main findings",
                        "reproducibility_score": "float 0-1",
                        "fair_assessment": "FAIR compliance scores",
                        "cost_breakdown": "dict of service costs"
                    },
                    "estimated_duration": "15-30s",
                    "estimated_cost": "$0.30-0.60",
                    "requires_llm": True
                },
                "analyze_paper_budget": {
                    "description": "Budget-aware comprehensive paper analysis with cost control",
                    "input_schema": {
                        "pdf_data": "base64 encoded PDF content",
                        "budget": "float maximum cost allowed",
                        "priority": "string (speed/balanced/quality)"
                    },
                    "output_schema": {
                        "analysis": "complete paper analysis dict",
                        "budget_used": "float actual cost",
                        "budget_remaining": "float",
                        "services_used": "list of PIDs"
                    },
                    "estimated_duration": "15-30s",
                    "estimated_cost": "up to budget limit",
                    "requires_llm": True
                },
                "extract_key_findings": {
                    "description": "Extract and summarize main findings from paper",
                    "input_schema": {
                        "text": "paper text content"
                    },
                    "output_schema": {
                        "findings": "list of key findings",
                        "summary": "brief summary"
                    },
                    "estimated_duration": "5-10s",
                    "estimated_cost": "$0.10-0.20"
                },
                "assess_methodology": {
                    "description": "Evaluate research methodology quality",
                    "input_schema": {
                        "text": "paper text content"
                    },
                    "output_schema": {
                        "methodology_type": "string",
                        "rigor_score": "float 0-1",
                        "strengths": "list",
                        "weaknesses": "list"
                    },
                    "estimated_duration": "5-10s",
                    "estimated_cost": "$0.10-0.20"
                },
                "check_reproducibility": {
                    "description": "Assess reproducibility of research",
                    "input_schema": {
                        "text": "paper text content"
                    },
                    "output_schema": {
                        "reproducibility_score": "float 0-1",
                        "data_availability": "boolean",
                        "code_availability": "boolean",
                        "documentation_quality": "string"
                    },
                    "estimated_duration": "5-10s",
                    "estimated_cost": "$0.10-0.20"
                }
            },
            "dependencies": {
                "required_services": [
                    {"type": "document_processor", "operation": "extract_text", "for": "PDF parsing"},
                    {"type": "compliance_checker", "operation": "assess_fairness", "for": "FAIR assessment"},
                    {"type": "llm_service", "operation": "summarize", "for": "synthesis"}
                ],
                "optional_services": [
                    {"type": "creator", "operation": "improve_agent", "for": "self-improvement"}
                ]
            },
            "performance_characteristics": {
                "typical_latency": "15-30s",
                "max_concurrent_requests": 10,
                "failure_recovery": "automatic with alternative providers",
                "budget_control": "strict enforcement with cost tracking"
            },
            "marketplace_features": {
                "budget_aware": True,
                "failure_recovery": True,
                "policy_based_selection": True,
                "cost_tracking": True
            },
            "coordinates_with": [
                "document_processor",
                "compliance_checker",
                "llm_service"
            ],
            "llm_capable": True,
            "can_self_improve": True
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description for composite agent."""

        return {
            "agent_info": {
                "name": "Paper Analyzer Agent",
                "version": "1.0.0",
                "agent_type": "composite",
                "description": "Coordinates research paper analysis workflow using marketplace services"
            },

            "capabilities": {
                "analyze_paper_budget": {
                    "operation_type": "synthesis",

                    "input_schema": {
                        "type": "object",
                        "required": ["pdf_data", "budget"],
                        "properties": {
                            "pdf_data": {
                                "type": "string",
                                "format": "base64",
                                "contentEncoding": "base64"
                            },
                            "budget": {
                                "type": "number",
                                "minimum": 0.0
                            },
                            "selection_policy": {
                                "type": "string",
                                "enum": ["cheapest", "fastest", "balanced", "premium"],
                                "default": "balanced"
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["analysis", "fair_assessment", "cost_breakdown"],
                        "properties": {
                            "analysis": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string"},
                                    "key_findings": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "methodology": {"type": "string"},
                                    "contributions": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "fair_assessment": {
                                "type": "object",
                                "properties": {
                                    "overall_score": {"type": "number"},
                                    "findable_score": {"type": "number"},
                                    "accessible_score": {"type": "number"},
                                    "interoperable_score": {"type": "number"},
                                    "reusable_score": {"type": "number"}
                                }
                            },
                            "cost_breakdown": {
                                "type": "object",
                                "properties": {
                                    "total_cost": {"type": "number"},
                                    "services_used": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "service_pid": {"type": "string"},
                                                "operation": {"type": "string"},
                                                "cost": {"type": "number"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },

                    "constraints": {
                        "max_input_size": 52428800,  # 50MB
                        "timeout_seconds": 300,
                        "rate_limit": 10
                    },

                    "examples": [
                        {
                            "input": {
                                "pdf_data": "JVBERi0xLjQK...",
                                "budget": 1.0,
                                "selection_policy": "balanced"
                            },
                            "output": {
                                "analysis": {
                                    "summary": "This paper presents...",
                                    "key_findings": ["Finding 1", "Finding 2"],
                                    "methodology": "Experimental study",
                                    "contributions": ["Novel algorithm", "Benchmark dataset"]
                                },
                                "fair_assessment": {
                                    "overall_score": 0.85,
                                    "findable_score": 0.9,
                                    "accessible_score": 0.8,
                                    "interoperable_score": 0.85,
                                    "reusable_score": 0.85
                                },
                                "cost_breakdown": {
                                    "total_cost": 0.45,
                                    "services_used": [
                                        {
                                            "service_pid": "21.T11148/afdo-pdf-parser",
                                            "operation": "extract_text",
                                            "cost": 0.05
                                        },
                                        {
                                            "service_pid": "21.T11148/afdo-llm-service",
                                            "operation": "analyze_text",
                                            "cost": 0.35
                                        },
                                        {
                                            "service_pid": "21.T11148/afdo-fair-assessor",
                                            "operation": "assess_fairness",
                                            "cost": 0.05
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [
                    "openai==1.12.0",
                    "anthropic==0.18.1"
                ],
                "resource_requirements": {
                    "memory_mb": 512,
                    "cpu_cores": 1.0
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
        """Handle paper analysis operations."""
        if not self.client:
            raise ValueError("OpenAI client not initialized.")

        print(f"📄 Processing '{operation}' from {caller_pid}")

        try:
            if operation == "analyze_paper":
                result = await self._analyze_paper(parameters)
                self.performance_stats["successful"] += 1
                return result

            elif operation == "analyze_paper_budget":
                result = await self._analyze_paper_budget(parameters)
                self.performance_stats["successful"] += 1
                return result

            elif operation == "extract_key_findings":
                return await self._extract_key_findings(parameters)

            elif operation == "assess_methodology":
                return await self._assess_methodology(parameters)

            elif operation == "check_reproducibility":
                return await self._check_reproducibility(parameters)

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            self.performance_stats["failed"] += 1
            raise

        finally:
            self.performance_stats["total_analyses"] += 1

    async def _analyze_paper(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive paper analysis.

        Workflow:
        1. Extract text from PDF (if provided)
        2. Analyze content with LLM
        3. Assess FAIR compliance
        4. Synthesize results
        """
        pdf_data = parameters.get("pdf_data")
        paper_text = parameters.get("text")
        metadata = parameters.get("metadata", {})

        print("  → Starting comprehensive analysis...")

        results = {
            "analysis_type": "comprehensive",
            "analyzer": self.pid,
            "steps_completed": []
        }

        # Step 1: Get paper text (from PDF or direct)
        if pdf_data and not paper_text:
            print("    Step 1: Extracting text from PDF...")
            try:
                # Discover PDF Parser
                parsers = await self.discover_by_operation("extract_text")
                if not parsers:
                    raise ValueError("No PDF parser available")

                pdf_parser_pid = parsers[0]["pid"]

                # Call PDF Parser
                pdf_result = await self.call_other_afdo(
                    target_pid=pdf_parser_pid,
                    operation="extract_text",
                    data={"pdf_data": pdf_data}
                )

                paper_text = pdf_result.get("data", {}).get("text", "")
                results["steps_completed"].append({
                    "step": "pdf_extraction",
                    "status": "success",
                    "agent": pdf_parser_pid
                })
                print("    ✓ Text extracted")

            except Exception as e:
                print(f"    ✗ PDF extraction failed: {e}")
                results["steps_completed"].append({
                    "step": "pdf_extraction",
                    "status": "failed",
                    "error": str(e)
                })
                # Try to continue with what we have

        if not paper_text:
            raise ValueError("No paper text available (provide 'pdf_data' or 'text')")

        # Step 2: Analyze content with built-in LLM
        print("    Step 2: Analyzing content...")
        try:
            analysis_prompt = self.templates.get_comprehensive_analysis_prompt(paper_text)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=1000,
                temperature=0.5
            )

            analysis = response.choices[0].message.content
            results["content_analysis"] = analysis
            results["steps_completed"].append({
                "step": "content_analysis",
                "status": "success"
            })
            print("    ✓ Content analyzed")

        except Exception as e:
            print(f"    ✗ Content analysis failed: {e}")
            results["steps_completed"].append({
                "step": "content_analysis",
                "status": "failed",
                "error": str(e)
            })

        # Step 3: FAIR assessment (if metadata provided)
        if metadata:
            print("    Step 3: Assessing FAIR compliance...")
            try:
                # Discover FAIR Assessor
                assessors = await self.discover_by_operation("assess_fairness")
                if assessors:
                    fair_assessor_pid = assessors[0]["pid"]

                    # Call FAIR Assessor
                    fair_result = await self.call_other_afdo(
                        target_pid=fair_assessor_pid,
                        operation="assess_fairness",
                        data={"metadata": metadata}
                    )

                    results["fair_assessment"] = fair_result.get("data", {})
                    results["steps_completed"].append({
                        "step": "fair_assessment",
                        "status": "success",
                        "agent": fair_assessor_pid
                    })
                    print("    ✓ FAIR assessment completed")
                else:
                    print("    ⚠ No FAIR assessor available")

            except Exception as e:
                print(f"    ✗ FAIR assessment failed: {e}")
                results["steps_completed"].append({
                    "step": "fair_assessment",
                    "status": "failed",
                    "error": str(e)
                })

        # Step 4: Synthesize final summary
        print("    Step 4: Synthesizing results...")
        results["summary"] = self._synthesize_summary(results)
        results["performance_stats"] = self.performance_stats

        print("  ✓ Analysis complete")
        return results

    async def _analyze_paper_budget(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Budget-aware comprehensive paper analysis using marketplace.

        Workflow:
        1. Reserve coordination fee from budget
        2. Extract text from PDF using marketplace selection
        3. Analyze content with built-in LLM (or hire external)
        4. Assess FAIR compliance using marketplace
        5. Return results with budget breakdown
        """
        # Extract parameters
        pdf_data = parameters.get("pdf_data")
        paper_text = parameters.get("text")
        metadata = parameters.get("metadata", {})
        budget_amount = parameters.get("budget", 1.0)
        policy = parameters.get("policy", "balanced")

        print(f"  → Starting budget-aware analysis (budget: ${budget_amount:.2f})...")

        # Create budget manager
        budget = BudgetManager(total_budget=budget_amount)

        # Reserve coordination fee
        coord_reservation = budget.reserve(self.kernel_attributes["cost"], "coordination", self.pid)
        if not coord_reservation:
            raise ValueError(f"Insufficient budget for coordination fee (${self.kernel_attributes['cost']:.2f})")

        results = {
            "analysis_type": "comprehensive_budget_aware",
            "analyzer": self.pid,
            "policy": policy,
            "steps_completed": [],
            "costs_breakdown": {}
        }

        # Step 1: Get paper text (from PDF or direct)
        if pdf_data and not paper_text:
            print(f"    Step 1: Extracting text from PDF (budget: ${budget.get_available():.2f})...")
            try:
                # Use marketplace to find and call PDF parser
                pdf_result = await self.call_with_alternatives(
                    operation="extract_text",
                    parameters={"pdf_data": pdf_data},
                    budget=budget,
                    max_retries=2
                )

                paper_text = pdf_result.get("data", {}).get("text", "")
                pdf_cost = pdf_result.get("cost", 0.0)

                results["steps_completed"].append({
                    "step": "pdf_extraction",
                    "status": "success",
                    "provider": pdf_result.get("provider"),
                    "cost": pdf_cost,
                    "duration": pdf_result.get("duration", 0)
                })
                results["costs_breakdown"]["pdf_extraction"] = pdf_cost
                print(f"    ✓ Text extracted (cost: ${pdf_cost:.4f})")

            except Exception as e:
                print(f"    ✗ PDF extraction failed: {e}")
                results["steps_completed"].append({
                    "step": "pdf_extraction",
                    "status": "failed",
                    "error": str(e)
                })
                # Continue if we have text from other source

        if not paper_text:
            budget.release(coord_reservation)
            raise ValueError("No paper text available (provide 'pdf_data' or 'text')")

        # Step 2: Analyze content with built-in LLM
        print(f"    Step 2: Analyzing content (budget: ${budget.get_available():.2f})...")
        try:
            analysis_prompt = self.templates.get_comprehensive_analysis_prompt(paper_text)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=1000,
                temperature=0.5
            )

            analysis = response.choices[0].message.content
            results["content_analysis"] = analysis

            # Built-in LLM costs are included in coordination fee
            results["steps_completed"].append({
                "step": "content_analysis",
                "status": "success",
                "provider": self.pid,
                "cost": 0.0  # Included in coordination
            })
            print("    ✓ Content analyzed (internal)")

        except Exception as e:
            print(f"    ✗ Content analysis failed: {e}")
            results["steps_completed"].append({
                "step": "content_analysis",
                "status": "failed",
                "error": str(e)
            })

        # Step 3: FAIR assessment (if metadata provided and budget allows)
        if metadata and budget.get_available() > 0.01:
            print(f"    Step 3: Assessing FAIR compliance (budget: ${budget.get_available():.2f})...")
            try:
                # Use marketplace to find and call FAIR assessor
                fair_result = await self.call_with_alternatives(
                    operation="assess_fairness",
                    parameters={"metadata": metadata},
                    budget=budget,
                    max_retries=2
                )

                fair_cost = fair_result.get("cost", 0.0)
                results["fair_assessment"] = fair_result.get("data", {})

                results["steps_completed"].append({
                    "step": "fair_assessment",
                    "status": "success",
                    "provider": fair_result.get("provider"),
                    "cost": fair_cost,
                    "duration": fair_result.get("duration", 0)
                })
                results["costs_breakdown"]["fair_assessment"] = fair_cost
                print(f"    ✓ FAIR assessment completed (cost: ${fair_cost:.4f})")

            except Exception as e:
                print(f"    ✗ FAIR assessment failed: {e}")
                results["steps_completed"].append({
                    "step": "fair_assessment",
                    "status": "failed",
                    "error": str(e)
                })
        elif metadata:
            print(f"    ⚠ Skipping FAIR assessment (insufficient budget: ${budget.get_available():.2f})")

        # Commit coordination fee
        budget.commit(coord_reservation, self.kernel_attributes["cost"])
        results["costs_breakdown"]["coordination"] = self.kernel_attributes["cost"]

        # Step 4: Synthesize final summary
        print("    Step 4: Synthesizing results...")
        results["summary"] = self._synthesize_summary(results)
        results["performance_stats"] = self.performance_stats

        # Add budget summary
        results["budget_summary"] = budget.get_breakdown()

        print(f"  ✓ Analysis complete (spent: ${budget.spent:.4f} of ${budget.total_budget:.2f})")
        return results

    async def _extract_key_findings(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key findings from paper."""
        paper_text = parameters.get("text")
        if not paper_text:
            raise ValueError("Missing 'text' parameter")

        prompt = self.templates.get_findings_prompt(paper_text)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5
        )

        return {
            "key_findings": response.choices[0].message.content,
            "analyzer": self.pid
        }

    async def _assess_methodology(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess research methodology."""
        paper_text = parameters.get("text")
        if not paper_text:
            raise ValueError("Missing 'text' parameter")

        prompt = self.templates.get_methodology_prompt(paper_text)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5
        )

        return {
            "methodology_assessment": response.choices[0].message.content,
            "analyzer": self.pid
        }

    async def _check_reproducibility(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check reproducibility of research."""
        paper_text = parameters.get("text")
        if not paper_text:
            raise ValueError("Missing 'text' parameter")

        prompt = self.templates.get_reproducibility_prompt(paper_text)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5
        )

        return {
            "reproducibility_assessment": response.choices[0].message.content,
            "analyzer": self.pid
        }

    def _synthesize_summary(self, results: Dict[str, Any]) -> str:
        """Synthesize final summary from all results."""
        summary_parts = []

        if "content_analysis" in results:
            summary_parts.append("Content Analysis:\n" + results["content_analysis"])

        if "fair_assessment" in results:
            fair = results["fair_assessment"]
            summary_parts.append(
                f"\nFAIR Compliance: {fair.get('overall_score', 'N/A')} "
                f"({fair.get('compliance_level', 'Unknown')})"
            )

        summary_parts.append(
            f"\nSteps completed: {len([s for s in results['steps_completed'] if s['status'] == 'success'])}"
        )

        return "\n".join(summary_parts)

if __name__ == "__main__":
    agent = PaperAnalyzerAgent()
    agent.run()
