"""Tests for PDF Parser aFDO."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

from agents.pdf_parser.pdf_utils import (
    extract_text,
    extract_basic_metadata,
    get_first_page_text
)


def create_test_pdf() -> bytes:
    """Create a simple test PDF."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Page 1
    c.drawString(100, 750, "Test Research Paper")
    c.drawString(100, 730, "Author: Test Author")
    c.drawString(100, 700, "Abstract: This is a test paper about testing.")
    c.showPage()

    # Page 2
    c.drawString(100, 750, "Introduction")
    c.drawString(100, 730, "This is the introduction section.")
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.read()


def test_extract_text():
    """Test text extraction."""
    pdf_data = create_test_pdf()
    text = extract_text(pdf_data)

    assert "Test Research Paper" in text
    assert "Test Author" in text
    assert "Introduction" in text


def test_extract_metadata():
    """Test metadata extraction."""
    pdf_data = create_test_pdf()
    metadata = extract_basic_metadata(pdf_data)

    assert "num_pages" in metadata
    assert metadata["num_pages"] == 2


def test_first_page():
    """Test first page extraction."""
    pdf_data = create_test_pdf()
    text = get_first_page_text(pdf_data)

    assert "Test Research Paper" in text
    assert "Introduction" not in text  # Should not include page 2


@pytest.mark.asyncio
async def test_pdf_parser_agent():
    """Test PDF Parser agent (requires registry running)."""
    from agents.pdf_parser.pdf_parser_agent import PDFParserAgent

    agent = PDFParserAgent()

    # Create test PDF
    pdf_data = create_test_pdf()
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

    # Test extract_text operation
    result = await agent.handle_operation(
        operation="extract_text",
        caller_pid="test-caller",
        parameters={"pdf_data": pdf_base64}
    )

    assert "text" in result
    assert "Test Research Paper" in result["text"]
    assert result["word_count"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
