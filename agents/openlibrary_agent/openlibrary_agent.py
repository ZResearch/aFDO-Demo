"""
Open Library Agent

Searches books from Open Library using the free API.
No authentication required.

Policy: Defined in policy.json
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
import httpx
from shared.afdo_base import aFDOBase


class OpenLibraryAgent(aFDOBase):
    """
    Open Library Agent - Searches books and references.

    API: https://openlibrary.org/dev/docs/api/search
    No authentication required.

    Capabilities:
    - search_books: Search for books
    - get_book_info: Get detailed book information
    """

    def __init__(self):
        super().__init__(
            name="Open Library Agent",
            fdo_type="21.T11148/type-data-source-v1",
            operations=[
                "search_books",
                "get_book_info",
                "find_references"
            ],
            port=8012,
            cost=0.01,
            has_llm=False,
            specialization="books_references"
        )

        self.base_url = "https://openlibrary.org"
        self.logger.info(self.name, "📚 Open Library Agent initialized")

    def get_metadata_content(self) -> Dict[str, Any]:
        return {
            "description": "Searches books from Open Library",
            "version": "1.0.0",
            "agent_role": "data_source",
            "api_source": "Open Library API",
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
                "name": "Open Library Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Searches books from Open Library"
            },
            "capabilities": {
                "search_books": {
                    "operation_type": "data_extraction",
                    "description": "Search for books",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Book title, author, or subject",

                                "format_requirements": {
                                    "rules": [
                                        "Extract book title, author name, or subject",
                                        "Remove conversational words (books about, find me)",
                                        "Preserve exact titles and author names",
                                        "For subjects, use broad categories"
                                    ],

                                    "transformation_examples": [
                                        {
                                            "user_query": "books about coffee",
                                            "correct_query": "coffee",
                                            "reasoning": "Remove 'books about', keep subject"
                                        },
                                        {
                                            "user_query": "1984 by George Orwell",
                                            "correct_query": "1984 Orwell",
                                            "reasoning": "Keep title and author, remove 'by'"
                                        },
                                        {
                                            "user_query": "find me books by Asimov",
                                            "correct_query": "Asimov",
                                            "reasoning": "Extract author name only"
                                        }
                                    ]
                                }
                            },
                            "limit": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["books", "count"],
                        "properties": {
                            "books": {"type": "array"},
                            "count": {"type": "integer"}
                        }
                    },
                    "side_effects": [],
                    "idempotent": True
                },
                "get_book_info": {
                    "operation_type": "data_extraction",
                    "input_schema": {
                        "type": "object",
                        "required": ["work_id"],
                        "properties": {
                            "work_id": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "subjects": {"type": "array"}
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
        """Handle Open Library operations."""

        if operation == "search_books" or operation == "find_references":
            return await self._search_books(parameters)

        elif operation == "get_book_info":
            return await self._get_book_info(parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _search_books(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search Open Library for books."""

        query = parameters.get("query")
        limit = parameters.get("limit", 5)

        if not query:
            raise ValueError("Missing 'query' parameter")

        url = f"{self.base_url}/search.json"
        params = {
            "q": query,
            "limit": min(limit, 20)
        }

        self.logger.info(self.name, f"📚 Searching books for: {query}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            books = []
            for doc in data.get("docs", []):
                book = {
                    "title": doc.get("title", ""),
                    "authors": doc.get("author_name", []),
                    "first_publish_year": doc.get("first_publish_year"),
                    "isbn": doc.get("isbn", [None])[0] if doc.get("isbn") else None,
                    "subject": doc.get("subject", [])[:3],
                    "work_id": doc.get("key", "").replace("/works/", "")
                }
                books.append(book)

            self.logger.info(self.name, f"✅ Found {len(books)} books")

            return {
                "books": books,
                "count": len(books),
                "query": query,
                "source": "Open Library",
                "extracted_by": self.pid
            }

        except Exception as e:
            self.logger.error(self.name, f"❌ Search failed: {e}")
            raise

    async def _get_book_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed book information."""

        work_id = parameters.get("work_id")
        if not work_id:
            raise ValueError("Missing 'work_id' parameter")

        url = f"{self.base_url}/works/{work_id}.json"

        self.logger.info(self.name, f"📚 Fetching book info: {work_id}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            # Description can be string or dict
            description = data.get("description", "")
            if isinstance(description, dict):
                description = description.get("value", "")

            book = {
                "title": data.get("title", ""),
                "description": description,
                "subjects": data.get("subjects", [])[:5],
                "work_id": work_id,
                "source": "Open Library",
                "extracted_by": self.pid
            }

            self.logger.info(self.name, f"✅ Retrieved book info")

            return book

        except Exception as e:
            self.logger.error(self.name, f"❌ Failed to fetch book: {e}")
            raise


if __name__ == "__main__":
    agent = OpenLibraryAgent()
    agent.run()
