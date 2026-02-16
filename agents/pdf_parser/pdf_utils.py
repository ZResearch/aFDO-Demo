"""Utilities for PDF processing."""

import io
from typing import Dict, Any, Optional, List
import PyPDF2
import pdfplumber


def extract_text_pypdf2(pdf_data: bytes) -> str:
    """
    Extract text using PyPDF2.

    Args:
        pdf_data: PDF file as bytes

    Returns:
        Extracted text
    """
    try:
        pdf_file = io.BytesIO(pdf_data)
        reader = PyPDF2.PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"PyPDF2 extraction failed: {e}")


def extract_text_pdfplumber(pdf_data: bytes) -> str:
    """
    Extract text using pdfplumber (fallback).

    Args:
        pdf_data: PDF file as bytes

    Returns:
        Extracted text
    """
    try:
        pdf_file = io.BytesIO(pdf_data)
        text_parts = []

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"pdfplumber extraction failed: {e}")


def extract_text(pdf_data: bytes) -> str:
    """
    Extract text from PDF (tries PyPDF2 first, pdfplumber as fallback).

    Args:
        pdf_data: PDF file as bytes

    Returns:
        Extracted text
    """
    try:
        return extract_text_pypdf2(pdf_data)
    except:
        # Fallback to pdfplumber
        return extract_text_pdfplumber(pdf_data)


def extract_basic_metadata(pdf_data: bytes) -> Dict[str, Any]:
    """
    Extract basic metadata from PDF.

    Args:
        pdf_data: PDF file as bytes

    Returns:
        Dictionary with metadata
    """
    try:
        pdf_file = io.BytesIO(pdf_data)
        reader = PyPDF2.PdfReader(pdf_file)

        metadata = reader.metadata or {}

        return {
            "title": metadata.get("/Title", "Unknown"),
            "author": metadata.get("/Author", "Unknown"),
            "subject": metadata.get("/Subject", ""),
            "creator": metadata.get("/Creator", ""),
            "producer": metadata.get("/Producer", ""),
            "num_pages": len(reader.pages)
        }
    except Exception as e:
        return {
            "title": "Unknown",
            "author": "Unknown",
            "error": str(e),
            "num_pages": 0
        }


def extract_tables(pdf_data: bytes) -> List[List[List[str]]]:
    """
    Extract tables from PDF using pdfplumber.

    Args:
        pdf_data: PDF file as bytes

    Returns:
        List of tables (each table is list of rows, each row is list of cells)
    """
    try:
        pdf_file = io.BytesIO(pdf_data)
        all_tables = []

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)

        return all_tables
    except Exception as e:
        return []


def get_first_page_text(pdf_data: bytes, max_chars: int = 2000) -> str:
    """
    Get text from first page (useful for getting abstract/intro).

    Args:
        pdf_data: PDF file as bytes
        max_chars: Maximum characters to return

    Returns:
        First page text (truncated)
    """
    try:
        pdf_file = io.BytesIO(pdf_data)
        reader = PyPDF2.PdfReader(pdf_file)

        if len(reader.pages) > 0:
            text = reader.pages[0].extract_text()
            return text[:max_chars]
        return ""
    except:
        return ""
