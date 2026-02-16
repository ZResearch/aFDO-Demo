"""
ArXiv Agent

Searches scientific papers from ArXiv using the free API.
No authentication required.

Policy: Defined in policy.json
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
import httpx
import xml.etree.ElementTree as ET
from shared.afdo_base import aFDOBase


class ArxivAgent(aFDOBase):
    """
    ArXiv Agent - Searches scientific papers.

    API: http://export.arxiv.org/api/query
    No authentication required.

    Capabilities:
    - search_papers: Search for research papers
    - get_paper_abstract: Get specific paper by ID
    """

    def __init__(self):
        super().__init__(
            name="ArXiv Agent",
            fdo_type="21.T11148/type-data-source-v1",
            operations=[
                "receive_query",  # Universal cascading entry point
                "search_papers",
                "get_paper_abstract",
                "find_research"
            ],
            port=8011,
            cost=0.02,
            has_llm=False,
            specialization="scientific_research"
        )

        self.base_url = "https://export.arxiv.org/api/query"
        self.logger.info(self.name, "📄 ArXiv Agent initialized")

    def get_metadata_content(self) -> Dict[str, Any]:
        return {
            "description": "Searches and retrieves the latest research papers, scientific publications, academic papers, pre-prints, scholarly articles, and technical reports from arXiv repository. Specializes in machine learning papers, AI research, deep learning publications, neural networks, LLM research, multi-agent systems, and computer science papers. Best for queries about recent papers, latest research, new publications, and cutting-edge scientific work.",
            "version": "1.0.0",
            "agent_role": "data_source",
            "api_source": "ArXiv API",
            "requires_auth": False
        }

    def get_self_description(self) -> Dict[str, Any]:
        """
        Return self-description with input schema.

        CRITICAL: Input schemas tell delegators HOW to prepare inputs!
        Following FAIR/FDO principles for machine-actionable metadata.
        """
        return {
            "agent_info": {
                "name": "ArXiv Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Searches and retrieves the latest research papers, scientific publications, academic papers, pre-prints, scholarly articles, and technical reports from arXiv repository. Specializes in machine learning papers, AI research, deep learning publications, neural networks, LLM research, multi-agent systems, and computer science papers. Best for queries about recent papers, latest research, new publications, and cutting-edge scientific work."
            },
            "capabilities": {
                "search_papers": {
                    "operation_type": "data_extraction",
                    "description": "Search for scientific papers on ArXiv",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Research keywords for ArXiv search",

                                "format_requirements": {
                                    "rules": [
                                        "Extract research keywords and technical terms",
                                        "Remove conversational phrases (recent, papers about, studies on)",
                                        "Use standard academic terminology",
                                        "Keep field-specific terms intact",
                                        "Combine related terms appropriately"
                                    ],

                                    "transformation_examples": [
                                        {
                                            "user_query": "recent advances in quantum computing",
                                            "correct_query": "quantum computing",
                                            "reasoning": "Remove 'recent advances', keep technical term"
                                        },
                                        {
                                            "user_query": "papers about neural networks",
                                            "correct_query": "neural networks",
                                            "reasoning": "Remove 'papers about', keep research term"
                                        },
                                        {
                                            "user_query": "machine learning research",
                                            "correct_query": "machine learning",
                                            "reasoning": "Remove generic 'research', keep technical term"
                                        }
                                    ]
                                }
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["papers", "count"],
                        "properties": {
                            "papers": {"type": "array"},
                            "count": {"type": "integer"},
                            "query": {"type": "string"}
                        }
                    },
                    "side_effects": [],
                    "idempotent": True
                },
                "get_paper_abstract": {
                    "operation_type": "data_extraction",
                    "input_schema": {
                        "type": "object",
                        "required": ["arxiv_id"],
                        "properties": {
                            "arxiv_id": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "abstract": {"type": "string"},
                            "authors": {"type": "array"}
                        }
                    },
                    "side_effects": [],
                    "idempotent": True
                },
                "receive_query": {
                    "operation_type": "query_processing",
                    "description": "Universal entry point - receives raw user queries about research papers, analyzes them, searches for papers, and can cascade delegation to other agents (like LLM Consultant) for synthesis if needed. Handles queries about latest papers, breakthroughs, research trends, paper comparisons, etc.",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Raw user query about research papers (no transformation needed)"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "papers": {"type": "array"},
                            "answer": {"type": "string"},
                            "source": {"type": "string"},
                            "cascade_path": {"type": "string"}
                        }
                    },
                    "side_effects": ["may_delegate_to_llm"],
                    "idempotent": True
                }
            },
            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": ["httpx==0.27.0"],
                "resource_requirements": {
                    "memory_mb": 128,
                    "cpu_cores": 0.25
                }
            },
            "agent_attributes": {
                "has_llm": False,
                "autonomy_level": "task",
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
        """Handle ArXiv operations."""

        if operation == "receive_query":
            return await self._receive_query(parameters)

        elif operation == "search_papers" or operation == "find_research":
            return await self._search_papers(parameters)

        elif operation == "get_paper_abstract":
            return await self._get_paper_abstract(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _receive_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal entry point - receives raw user query.

        This is the cascading delegation pattern:
        1. Receive query
        2. Do what I can (search papers)
        3. Decide if I need help (synthesis/analysis)
        4. Delegate if needed
        5. Return complete answer
        """
        query = parameters.get("query") or parameters.get("message")

        if not query:
            raise ValueError("Missing 'query' or 'message' parameter")

        self.logger.info(self.name, f"📨 Received query: {query}")

        # Step 1: Search for papers (my core capability)
        search_result = await self._search_papers({"query": query, "max_results": 5})
        papers = search_result.get("papers", [])

        self.logger.info(self.name, f"   Found {len(papers)} papers")

        # Step 2: Check if user needs synthesis/analysis
        # Keywords that indicate need for deeper analysis
        needs_synthesis = any(keyword in query.lower() for keyword in [
            "breakthrough", "compare", "analyze", "summarize",
            "explain", "what are", "how do", "synthesize"
        ])

        if needs_synthesis and papers:
            self.logger.info(self.name, f"   🔄 Query needs synthesis - delegating to LLM Consultant")

            # Step 3: Delegate to LLM Consultant for synthesis
            try:
                # Find LLM Consultant via semantic discovery
                llm_agents = await self.discover_by_operation_query(
                    query="synthesize and explain research papers",
                    top_k=1,
                    min_score=0.0
                )

                if llm_agents and len(llm_agents) > 0:
                    llm_operation = llm_agents[0]
                    providers = llm_operation.get('providers', [])

                    # Filter out self to prevent infinite recursion
                    providers = [p for p in providers if p['agent_pid'] != self.pid]

                    if providers:
                        llm_provider = providers[0]
                        llm_pid = llm_provider['agent_pid']
                        llm_name = llm_provider['agent_name']

                        self.logger.info(self.name, f"   🎯 Delegating synthesis to: {llm_name}")

                        # Build context for LLM
                        papers_text = "\n\n".join([
                            f"Paper {i+1}: {p['title']}\nAuthors: {', '.join(p['authors'])}\nAbstract: {p['abstract'][:500]}..."
                            for i, p in enumerate(papers[:3])  # Top 3 papers
                        ])

                        synthesis_query = f"Based on these recent papers, {query}\n\nPapers:\n{papers_text}"

                        # Cascade: Delegate to LLM Consultant
                        llm_result = await self.call_other_afdo(
                            target_pid=llm_pid,
                            operation="receive_query",  # Universal operation!
                            data={"query": synthesis_query}
                        )

                        # Return synthesized answer
                        return {
                            "answer": llm_result.get('data', {}).get('response', 'Synthesis unavailable'),
                            "papers": papers,
                            "source": "ArXiv + LLM Synthesis",
                            "cascade_path": f"ArXiv Agent → {llm_name}"
                        }

            except Exception as e:
                self.logger.warning(self.name, f"   ⚠️ Synthesis delegation failed: {e}, returning raw papers")

        # Step 4: Return papers directly if no synthesis needed
        return {
            "papers": papers,
            "count": len(papers),
            "query": query,
            "source": "ArXiv",
            "extracted_by": self.pid
        }

    async def _search_papers(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search ArXiv for papers."""

        # Accept both 'query' and 'topic' for backward compatibility
        query = parameters.get("query") or parameters.get("topic")
        max_results = parameters.get("max_results", 5)

        if not query:
            raise ValueError("Missing 'query' or 'topic' parameter")

        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(max_results, 20)
        }

        self.logger.info(self.name, f"📄 Searching ArXiv for: {query} (max {max_results})")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                xml_data = response.text

            # Parse XML
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            papers = []
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                published_elem = entry.find('atom:published', ns)
                id_elem = entry.find('atom:id', ns)

                paper = {
                    "title": title_elem.text.strip() if title_elem is not None else "",
                    "authors": [
                        author.find('atom:name', ns).text
                        for author in entry.findall('atom:author', ns)
                    ],
                    "abstract": summary_elem.text.strip() if summary_elem is not None else "",
                    "published": published_elem.text if published_elem is not None else "",
                    "arxiv_id": id_elem.text.split('/abs/')[-1] if id_elem is not None else "",
                    "url": id_elem.text if id_elem is not None else ""
                }
                papers.append(paper)

            self.logger.info(self.name, f"✅ Found {len(papers)} papers")

            return {
                "papers": papers,
                "count": len(papers),
                "query": query,
                "source": "ArXiv",
                "extracted_by": self.pid
            }

        except Exception as e:
            self.logger.error(self.name, f"❌ Search failed: {e}")
            raise

    async def _get_paper_abstract(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific paper by ArXiv ID."""

        arxiv_id = parameters.get("arxiv_id")
        if not arxiv_id:
            raise ValueError("Missing 'arxiv_id' parameter")

        params = {"id_list": arxiv_id}

        self.logger.info(self.name, f"📄 Fetching paper: {arxiv_id}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                xml_data = response.text

            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            entry = root.find('atom:entry', ns)
            if entry is None:
                raise ValueError(f"Paper not found: {arxiv_id}")

            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)

            paper = {
                "title": title_elem.text.strip() if title_elem is not None else "",
                "abstract": summary_elem.text.strip() if summary_elem is not None else "",
                "authors": [
                    author.find('atom:name', ns).text
                    for author in entry.findall('atom:author', ns)
                ],
                "published": published_elem.text if published_elem is not None else "",
                "arxiv_id": arxiv_id,
                "url": entry.find('atom:id', ns).text,
                "source": "ArXiv",
                "extracted_by": self.pid
            }

            self.logger.info(self.name, f"✅ Retrieved paper")

            return paper

        except Exception as e:
            self.logger.error(self.name, f"❌ Failed to fetch paper: {e}")
            raise


if __name__ == "__main__":
    agent = ArxivAgent()
    agent.run()
