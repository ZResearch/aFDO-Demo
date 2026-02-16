"""
Wikipedia Agent

Fetches information from Wikipedia using the free REST API.
No authentication required.

Policy: Defined in policy.json
- Handles article lookups alone
- Delegates complex research to planners (discovered dynamically)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
import re
import httpx
from shared.afdo_base import aFDOBase


class WikipediaAgent(aFDOBase):
    """
    Wikipedia Agent - Fetches articles from Wikipedia.

    API: https://en.wikipedia.org/api/rest_v1/
    No authentication required.

    Capabilities:
    - get_article_summary: Get summary of article
    - search_wikipedia: Search for articles
    """

    def __init__(self):
        super().__init__(
            name="Wikipedia Agent",
            fdo_type="21.T11148/type-data-source-v1",
            operations=[
                "receive_query",  # Universal cascading entry point
                "get_article_summary",
                "search_wikipedia",
                "get_facts"
            ],
            port=8010,
            cost=0.01,  # Very cheap
            has_llm=False,
            specialization="general_knowledge"
        )

        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        self.logger.info(self.name, "📚 Wikipedia Agent initialized")

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide metadata content."""
        return {
            "description": "Provides encyclopedic knowledge, general facts, biographies, historical information, definitions, summaries about people, places, events, organizations, and concepts from Wikipedia. Best for queries about who someone is, what something is, when events happened, where places are located, general knowledge questions, factual information, and background information. NOT suitable for latest research papers or cutting-edge scientific publications.",
            "version": "1.0.0",
            "agent_role": "data_source",
            "api_source": "Wikipedia REST API v1",
            "requires_auth": False
        }

    def get_self_description(self) -> Dict[str, Any]:
        """
        Return structured self-description with detailed input schemas.

        CRITICAL: Input schemas tell delegators HOW to prepare inputs!
        Following FAIR/FDO principles for machine-actionable metadata.
        """
        return {
            "agent_info": {
                "name": "Wikipedia Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Provides encyclopedic knowledge, general facts, biographies, historical information, definitions, summaries about people, places, events, organizations, and concepts from Wikipedia. Best for queries about who someone is, what something is, when events happened, where places are located, general knowledge questions, factual information, and background information. NOT suitable for latest research papers or cutting-edge scientific publications."
            },
            "capabilities": {
                "get_article_summary": {
                    "operation_type": "data_extraction",
                    "description": "Fetch summary of a Wikipedia article",
                    "input_schema": {
                        "type": "object",
                        "required": ["topic"],
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Wikipedia article title",

                                # CRITICAL: Format requirements for delegators
                                "format_requirements": {
                                    "rules": [
                                        "Use proper Wikipedia article title format",
                                        "Remove temporal modifiers (latest, current, recent, newest)",
                                        "Use title case for proper nouns",
                                        "Be specific - use actual entity/person name if known",
                                        "Match standard Wikipedia naming conventions"
                                    ],

                                    "transformation_examples": [
                                        {
                                            "user_query": "what is the latest president of Algeria",
                                            "correct_topic": "President of Algeria",
                                            "reasoning": "Remove 'latest', use proper title 'President of Algeria'"
                                        },
                                        {
                                            "user_query": "who is the current CEO of Apple",
                                            "correct_topic": "Tim Cook",
                                            "reasoning": "Current CEO is Tim Cook - use person name"
                                        },
                                        {
                                            "user_query": "tell me about coffee",
                                            "correct_topic": "Coffee",
                                            "reasoning": "Simple topic - capitalize"
                                        },
                                        {
                                            "user_query": "recent developments in AI",
                                            "correct_topic": "Artificial intelligence",
                                            "reasoning": "Remove 'recent developments', use standard term"
                                        }
                                    ],

                                    "common_mistakes": [
                                        {
                                            "wrong": "latest president of Algeria",
                                            "correct": "President of Algeria",
                                            "issue": "Contains temporal word 'latest'"
                                        },
                                        {
                                            "wrong": "coffee",
                                            "correct": "Coffee",
                                            "issue": "Wikipedia uses title case"
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["title", "summary"],
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "url": {"type": "string"},
                            "source": {"type": "string"},
                            "extracted_by": {"type": "string"}
                        }
                    },
                    "side_effects": [],
                    "idempotent": True
                },
                "receive_query": {
                    "operation_type": "query_processing",
                    "description": "Primary source for answering factual questions, definitions, and explanations. Specializes in 'who is', 'what is', 'where is', 'when did', 'how many' questions. Provides encyclopedic information about: people (presidents, leaders, politicians, historical figures, biographies), places (countries, cities, geography), organizations, events, concepts, definitions, scientific terms, medical conditions, historical facts, current statistics, population data. Retrieves reliable factual summaries from Wikipedia encyclopedia. Use this for any factual lookup, definition request, or encyclopedic information retrieval.",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Raw user query about factual information (no transformation needed)"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "url": {"type": "string"},
                            "source": {"type": "string"},
                            "query": {"type": "string"}
                        }
                    },
                    "side_effects": [],
                    "idempotent": True
                },
                "search_wikipedia": {
                    "operation_type": "query_processing",
                    "description": "Search for Wikipedia articles",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for Wikipedia",

                                "format_requirements": {
                                    "rules": [
                                        "Can be more flexible than article titles",
                                        "Use natural search terms",
                                        "Remove question words (what, who, where)",
                                        "Keep key content words"
                                    ],

                                    "transformation_examples": [
                                        {
                                            "user_query": "what is quantum computing",
                                            "correct_query": "quantum computing",
                                            "reasoning": "Remove 'what is', keep core topic"
                                        }
                                    ]
                                }
                            },
                            "limit": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 10
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["results"],
                        "properties": {
                            "results": {"type": "array"},
                            "count": {"type": "integer"},
                            "query": {"type": "string"}
                        }
                    },
                    "side_effects": [],
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
        """
        Handle Wikipedia operations.

        NOTE: For receive_query, policy evaluation happens BEFORE this method
        is called (in handle_operation_with_policy). This method is only called
        when policy says "handle_alone" or if no policy engine exists.
        """

        if operation == "receive_query":
            return await self._receive_query(parameters)

        elif operation == "get_article_summary" or operation == "get_facts":
            return await self._get_article_summary(parameters)

        elif operation == "search_wikipedia":
            return await self._search_wikipedia(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _receive_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal entry point - receives raw user query.

        For Wikipedia, this is typically a terminal operation:
        1. Receive query
        2. Extract topic from query
        3. Fetch article summary
        4. Return result directly

        Wikipedia usually doesn't need cascading delegation - it's the terminal node.
        """
        query = parameters.get("query") or parameters.get("message")

        if not query:
            raise ValueError("Missing 'query' or 'message' parameter")

        self.logger.info(self.name, f"📨 Received query: {query}")

        # Step 1: Extract topic from natural language query
        topic = self._extract_topic_from_query(query)

        self.logger.info(self.name, f"   Extracted topic: '{topic}'")

        # Step 2: Fetch article summary (my core capability)
        try:
            result = await self._get_article_summary({"topic": topic})

            # Add query context to response
            result["query"] = query
            result["extracted_topic"] = topic

            self.logger.info(self.name, f"✅ Completed query processing")

            return result

        except Exception as e:
            self.logger.error(self.name, f"❌ Failed to process query: {e}")

            # If direct lookup fails, try searching
            self.logger.info(self.name, f"   🔄 Trying search fallback")
            try:
                search_results = await self._search_wikipedia({"query": topic, "limit": 1})
                if search_results["count"] > 0:
                    # Retry with first search result
                    first_result = search_results["results"][0]
                    result = await self._get_article_summary({"topic": first_result["title"]})
                    result["query"] = query
                    result["extracted_topic"] = topic
                    result["found_via_search"] = True
                    return result
            except Exception as search_error:
                self.logger.error(self.name, f"❌ Search fallback also failed: {search_error}")

            raise

    def _extract_topic_from_query(self, query: str) -> str:
        """
        Extract Wikipedia topic from natural language query.

        Examples:
        - "who is the president of Algeria" → "President of Algeria"
        - "what is coffee" → "Coffee"
        - "tell me about quantum computing" → "Quantum computing"
        - "latest president of France" → "President of France"
        """
        import re

        # Convert to lowercase for pattern matching
        query_lower = query.lower().strip()

        # Remove question marks and trailing whitespace
        query_lower = query_lower.rstrip('?').strip()

        # Pattern 1: "who is the [X]" → X
        match = re.match(r'^(?:who\s+is\s+(?:the\s+)?)(.*)', query_lower)
        if match:
            topic = match.group(1).strip()
            # Capitalize for Wikipedia
            return self._capitalize_topic(topic)

        # Pattern 2: "what is [X]" → X
        match = re.match(r'^(?:what\s+is\s+(?:the\s+)?)(.*)', query_lower)
        if match:
            topic = match.group(1).strip()
            return self._capitalize_topic(topic)

        # Pattern 3: "tell me about [X]" → X
        match = re.match(r'^(?:tell\s+me\s+about\s+(?:the\s+)?)(.*)', query_lower)
        if match:
            topic = match.group(1).strip()
            return self._capitalize_topic(topic)

        # Pattern 4: Remove temporal modifiers (latest, current, recent)
        topic = re.sub(r'\b(?:latest|current|recent|newest)\s+', '', query_lower)

        # Pattern 5: Remove question words at the start
        topic = re.sub(r'^\b(?:who|what|where|when|why|how)\s+', '', topic)
        topic = re.sub(r'^\b(?:is|are|was|were)\s+(?:the\s+)?', '', topic)

        # Clean up and capitalize
        topic = topic.strip()
        return self._capitalize_topic(topic)

    def _capitalize_topic(self, topic: str) -> str:
        """
        Capitalize topic according to Wikipedia conventions.
        - First letter capitalized
        - Proper nouns capitalized
        - Common words lowercase
        """
        if not topic:
            return topic

        # Title case, but Wikipedia uses sentence case
        # For simplicity, capitalize first letter and keep rest as is
        words = topic.split()
        if not words:
            return topic

        # Capitalize first word
        words[0] = words[0].capitalize()

        # Capitalize known proper nouns
        proper_nouns = {'algeria', 'france', 'america', 'usa', 'uk', 'china', 'japan',
                       'europe', 'asia', 'africa', 'wikipedia', 'google', 'apple'}

        for i, word in enumerate(words[1:], 1):
            if word.lower() in proper_nouns:
                words[i] = word.capitalize()

        return ' '.join(words)

    async def _get_article_summary(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch article summary from Wikipedia."""

        topic = parameters.get("topic")
        if not topic:
            raise ValueError("Missing 'topic' parameter")

        # Clean topic for URL
        topic_url = topic.replace(" ", "_")

        url = f"{self.base_url}/page/summary/{topic_url}"

        self.logger.info(self.name, f"📚 Fetching Wikipedia summary for: {topic}")

        try:
            headers = {"User-Agent": "aFDO-Wikipedia-Agent/1.0 (Educational Research)"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            summary = data.get("extract", "")

            # Check if this is a political office/position article
            # Try to extract current officeholder information
            current_holder = None
            if any(keyword in topic.lower() for keyword in ["president", "prime minister", "chancellor", "king", "queen", "minister", "governor", "mayor"]):
                self.logger.info(self.name, f"🔍 Detected political office - trying to extract current holder")
                current_holder = await self._extract_current_holder(topic_url)

            # If we found current holder info, enhance the summary
            if current_holder:
                summary = f"{current_holder['name']} is the current {topic.lower()}. {summary}"

            result = {
                "title": data.get("title", topic),
                "summary": summary,
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "source": "Wikipedia",
                "extracted_by": self.pid
            }

            if current_holder:
                result["current_holder"] = current_holder

            self.logger.info(self.name, f"✅ Retrieved summary ({len(result['summary'])} chars)")

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.warning(self.name, f"⚠️ Article not found: {topic}")
                return {
                    "title": topic,
                    "summary": f"No Wikipedia article found for '{topic}'",
                    "url": "",
                    "source": "Wikipedia",
                    "extracted_by": self.pid,
                    "error": "not_found"
                }
            else:
                raise
        except Exception as e:
            self.logger.error(self.name, f"❌ Failed to fetch article: {e}")
            raise

    async def _extract_current_holder(self, topic_url: str) -> Dict[str, Any]:
        """
        Extract current officeholder from Wikipedia article infobox.
        Uses MediaWiki API to get page content and parse infobox.
        """
        try:
            headers = {"User-Agent": "aFDO-Wikipedia-Agent/1.0 (Educational Research)"}
            params = {
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "format": "json",
                "titles": topic_url.replace("_", " "),
                "rvslots": "main",
                "redirects": "1"  # CRITICAL: Follow redirects to actual article
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.search_url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Extract page content
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None

            page = list(pages.values())[0]
            if "revisions" not in page:
                return None

            content = page["revisions"][0]["slots"]["main"]["*"]

            self.logger.info(self.name, f"📄 Fetched {len(content)} chars of content")

            # Debug: Check if incumbent field exists at all
            if '| incumbent' in content.lower():
                self.logger.info(self.name, "🔍 Found 'incumbent' field in content")
            else:
                self.logger.warning(self.name, "⚠️ No 'incumbent' field found in content")

            # Parse infobox for current holder
            # Look for common infobox field names
            patterns = [
                r'\|\s*incumbent\s*=\s*\[\[(.*?)\]\]',
                r'\|\s*incumbent\s*=\s*([^\n\|]+)',
                r'\|\s*holder\s*=\s*\[\[(.*?)\]\]',
                r'\|\s*holder\s*=\s*([^\n\|]+)',
                r'\|\s*current\s*=\s*\[\[(.*?)\]\]',
                r'\|\s*current\s*=\s*([^\n\|]+)'
            ]

            for i, pattern in enumerate(patterns, 1):
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    self.logger.info(self.name, f"🎯 Pattern {i} matched: {pattern}")
                    raw_match = match.group(1).strip()
                    self.logger.info(self.name, f"   Raw match: '{raw_match}'")

                    name = raw_match
                    # Clean up wiki markup
                    name = re.sub(r'\|.*$', '', name)  # Remove pipe and everything after
                    name = name.replace("{{", "").replace("}}", "")
                    name = name.strip()
                    self.logger.info(self.name, f"   After cleanup: '{name}'")

                    if name and name.lower() not in ["vacant", "none", "tbd", "tba", ""]:
                        self.logger.info(self.name, f"✅ Found current holder: {name}")
                        return {
                            "name": name,
                            "extracted_from": "infobox"
                        }
                    else:
                        self.logger.warning(self.name, f"⚠️ Name '{name}' rejected (vacant/none/empty)")

            self.logger.info(self.name, "⚠️ Could not find current holder in infobox")
            return None

        except Exception as e:
            self.logger.warning(self.name, f"⚠️ Failed to extract current holder: {e}")
            return None

    async def _search_wikipedia(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search Wikipedia articles."""

        query = parameters.get("query")
        limit = parameters.get("limit", 5)

        if not query:
            raise ValueError("Missing 'query' parameter")

        params = {
            "action": "opensearch",
            "search": query,
            "limit": min(limit, 10),
            "format": "json"
        }

        self.logger.info(self.name, f"🔍 Searching Wikipedia for: {query}")

        try:
            headers = {"User-Agent": "aFDO-Wikipedia-Agent/1.0 (Educational Research)"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.search_url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            # OpenSearch format: [query, [titles], [descriptions], [urls]]
            titles = data[1] if len(data) > 1 else []
            descriptions = data[2] if len(data) > 2 else []
            urls = data[3] if len(data) > 3 else []

            results = []
            for i in range(len(titles)):
                results.append({
                    "title": titles[i],
                    "description": descriptions[i] if i < len(descriptions) else "",
                    "url": urls[i] if i < len(urls) else ""
                })

            self.logger.info(self.name, f"✅ Found {len(results)} results")

            return {
                "results": results,
                "count": len(results),
                "query": query,
                "source": "Wikipedia",
                "extracted_by": self.pid
            }

        except Exception as e:
            self.logger.error(self.name, f"❌ Search failed: {e}")
            raise


if __name__ == "__main__":
    agent = WikipediaAgent()
    agent.run()
