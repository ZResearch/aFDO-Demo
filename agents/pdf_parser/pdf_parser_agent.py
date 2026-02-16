"""PDF Parser aFDO - Extracts text and metadata from PDF documents."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import base64
from typing import Dict, Any
from shared.afdo_base import aFDOBase
from agents.pdf_parser.pdf_utils import (
    extract_text,
    extract_basic_metadata,
    extract_tables,
    get_first_page_text
)


class PDFParserAgent(aFDOBase):
    """
    PDF Parser aFDO.

    Capabilities:
    - Extract text from PDFs
    - Extract basic metadata (title, author, pages)
    - Extract tables
    - Can call LLM services for advanced processing
    """

    def __init__(self):
        super().__init__(
            name="PDF Parser",
            fdo_type="21.T11148/type-document-processor-v1",
            operations=[
                "extract_text",
                "extract_metadata",
                "extract_tables",
                "extract_first_page"
            ],
            port=8004,
            cost=0.05,
            has_llm=False
        )

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Extracts text, metadata, and tables from PDF documents",
            "version": "2.0.0",
            "agent_role": "task_agent",
            "capabilities": {
                "extract_text": {
                    "description": "Extracts all text content from PDF document",
                    "input_schema": {
                        "pdf_data": "base64 encoded PDF content"
                    },
                    "output_schema": {
                        "text": "extracted text string",
                        "page_count": "integer",
                        "success": "boolean"
                    },
                    "estimated_duration": "2-5s",
                    "estimated_cost": "$0.05",
                    "requires_llm": False
                },
                "extract_metadata": {
                    "description": "Extracts title, author, and basic metadata from PDF",
                    "input_schema": {
                        "pdf_data": "base64 encoded PDF content"
                    },
                    "output_schema": {
                        "title": "string",
                        "author": "string",
                        "pages": "integer",
                        "creation_date": "string"
                    },
                    "estimated_duration": "1-2s",
                    "estimated_cost": "$0.05"
                },
                "extract_tables": {
                    "description": "Extracts tabular data from PDF",
                    "input_schema": {
                        "pdf_data": "base64 encoded PDF content"
                    },
                    "output_schema": {
                        "tables": "list of table data structures",
                        "table_count": "integer"
                    },
                    "estimated_duration": "3-8s",
                    "estimated_cost": "$0.05"
                },
                "extract_first_page": {
                    "description": "Extracts text from first page only (fast preview)",
                    "input_schema": {
                        "pdf_data": "base64 encoded PDF content"
                    },
                    "output_schema": {
                        "text": "first page text",
                        "success": "boolean"
                    },
                    "estimated_duration": "0.5-1s",
                    "estimated_cost": "$0.05"
                }
            },
            "dependencies": {
                "required_libraries": ["PyPDF2", "pdfplumber"],
                "python_version": ">=3.8"
            },
            "performance_characteristics": {
                "typical_latency": "2-5s for full extraction",
                "max_file_size": "50MB",
                "supported_pdf_versions": "1.0-1.7",
                "max_concurrent_requests": 20
            },
            "llm_capable": False
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""

        return {
            "agent_info": {
                "name": "PDF Parser Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Extracts text and metadata from PDF documents using PyPDF2 and pdfplumber"
            },

            "capabilities": {
                "extract_text": {
                    "operation_type": "data_extraction",

                    "input_schema": {
                        "type": "object",
                        "required": ["pdf_data"],
                        "properties": {
                            "pdf_data": {
                                "type": "string",
                                "format": "base64",
                                "contentEncoding": "base64"
                            },
                            "summarize": {
                                "type": "boolean",
                                "default": False
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["text", "char_count", "word_count"],
                        "properties": {
                            "text": {"type": "string"},
                            "char_count": {"type": "integer", "minimum": 0},
                            "word_count": {"type": "integer", "minimum": 0},
                            "summary": {"type": ["string", "null"]},
                            "processor": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 52428800,  # 50MB
                        "timeout_seconds": 30,
                        "rate_limit": 20
                    },

                    "examples": [
                        {
                            "input": {
                                "pdf_data": "JVBERi0xLjQKJeLjz9MK...",
                                "summarize": False
                            },
                            "output": {
                                "text": "This is a sample PDF document...",
                                "char_count": 5000,
                                "word_count": 800,
                                "summary": None,
                                "processor": "21.T11148/afdo-pdf-parser"
                            }
                        }
                    ]
                },

                "extract_metadata": {
                    "operation_type": "data_extraction",

                    "input_schema": {
                        "type": "object",
                        "required": ["pdf_data"],
                        "properties": {
                            "pdf_data": {
                                "type": "string",
                                "format": "base64",
                                "contentEncoding": "base64"
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "author": {"type": "string"},
                            "pages": {"type": "integer"},
                            "creation_date": {"type": "string"},
                            "extracted_by": {"type": "string"},
                            "extraction_method": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 52428800,
                        "timeout_seconds": 10,
                        "rate_limit": 50
                    },

                    "examples": []
                },

                "extract_tables": {
                    "operation_type": "data_extraction",

                    "input_schema": {
                        "type": "object",
                        "required": ["pdf_data"],
                        "properties": {
                            "pdf_data": {
                                "type": "string",
                                "format": "base64",
                                "contentEncoding": "base64"
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["tables", "table_count"],
                        "properties": {
                            "tables": {
                                "type": "array",
                                "items": {"type": "array"}
                            },
                            "table_count": {"type": "integer", "minimum": 0},
                            "extracted_by": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 52428800,
                        "timeout_seconds": 60,
                        "rate_limit": 10
                    },

                    "examples": []
                },

                "extract_first_page": {
                    "operation_type": "data_extraction",

                    "input_schema": {
                        "type": "object",
                        "required": ["pdf_data"],
                        "properties": {
                            "pdf_data": {
                                "type": "string",
                                "format": "base64",
                                "contentEncoding": "base64"
                            },
                            "max_chars": {
                                "type": "integer",
                                "default": 2000,
                                "minimum": 100,
                                "maximum": 10000
                            }
                        }
                    },

                    "output_schema": {
                        "type": "object",
                        "required": ["first_page_text", "char_count", "truncated"],
                        "properties": {
                            "first_page_text": {"type": "string"},
                            "char_count": {"type": "integer", "minimum": 0},
                            "truncated": {"type": "boolean"},
                            "extracted_by": {"type": "string"}
                        }
                    },

                    "constraints": {
                        "max_input_size": 52428800,
                        "timeout_seconds": 5,
                        "rate_limit": 100
                    },

                    "examples": []
                }
            },

            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [
                    "PyPDF2==3.0.1",
                    "pdfplumber==0.10.3"
                ],
                "resource_requirements": {
                    "memory_mb": 256,
                    "cpu_cores": 0.5
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
        """Handle PDF processing operations."""
        print(f"📄 Processing '{operation}' request from {caller_pid}")

        # Get PDF data (should be base64 encoded)
        pdf_base64 = parameters.get("pdf_data")
        if not pdf_base64:
            raise ValueError("Missing 'pdf_data' parameter (base64 encoded PDF)")

        # Decode PDF
        try:
            pdf_data = base64.b64decode(pdf_base64)
        except Exception as e:
            raise ValueError(f"Invalid base64 PDF data: {e}")

        # Route to appropriate handler
        if operation == "extract_text":
            return await self._extract_text(pdf_data, parameters)

        elif operation == "extract_metadata":
            return await self._extract_metadata(pdf_data, parameters)

        elif operation == "extract_tables":
            return await self._extract_tables(pdf_data, parameters)

        elif operation == "extract_first_page":
            return await self._extract_first_page(pdf_data, parameters)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _extract_text(
        self,
        pdf_data: bytes,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract all text from PDF."""
        text = extract_text(pdf_data)

        # Check if summarization requested
        summarize = parameters.get("summarize", False)
        summary = None

        if summarize:
            # TODO: Call LLM endpoint for summarization
            summary = "Summary not yet implemented (requires LLM endpoint)"

        return {
            "text": text,
            "char_count": len(text),
            "word_count": len(text.split()),
            "summary": summary,
            "processor": self.pid
        }

    async def _extract_metadata(
        self,
        pdf_data: bytes,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        metadata = extract_basic_metadata(pdf_data)

        # Add processor info
        metadata["extracted_by"] = self.pid
        metadata["extraction_method"] = "PyPDF2"

        return metadata

    async def _extract_tables(
        self,
        pdf_data: bytes,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract tables from PDF."""
        tables = extract_tables(pdf_data)

        return {
            "tables": tables,
            "table_count": len(tables),
            "extracted_by": self.pid
        }

    async def _extract_first_page(
        self,
        pdf_data: bytes,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract text from first page."""
        max_chars = parameters.get("max_chars", 2000)
        text = get_first_page_text(pdf_data, max_chars)

        return {
            "first_page_text": text,
            "char_count": len(text),
            "truncated": len(text) == max_chars,
            "extracted_by": self.pid
        }


if __name__ == "__main__":
    agent = PDFParserAgent()
    agent.run()
