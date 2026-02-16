"""Analysis templates and prompts for paper analysis."""

from typing import Dict, Any

class AnalysisTemplates:
    """Templates for different types of paper analysis."""

    @staticmethod
    def get_comprehensive_analysis_prompt(paper_text: str) -> str:
        """Get prompt for comprehensive paper analysis."""
        return f"""Analyze this research paper comprehensively. Provide:

1. **Main Contribution**: What is the key contribution?
2. **Methodology**: What methods/approaches are used?
3. **Key Findings**: What are the main results?
4. **Strengths**: What are the paper's strengths?
5. **Limitations**: What limitations exist?
6. **Reproducibility**: Can the work be reproduced?

Paper text (first 3000 chars):
{paper_text[:3000]}

Provide a structured analysis."""

    @staticmethod
    def get_methodology_prompt(paper_text: str) -> str:
        """Get prompt for methodology assessment."""
        return f"""Assess the methodology in this research paper:

1. What methods/techniques are used?
2. Are the methods appropriate for the research questions?
3. Are there any methodological concerns?
4. Is the experimental setup clearly described?

Paper text:
{paper_text[:2000]}"""

    @staticmethod
    def get_findings_prompt(paper_text: str) -> str:
        """Get prompt for key findings extraction."""
        return f"""Extract the key findings from this research paper:

1. What are the main results?
2. What evidence supports these findings?
3. Are the findings clearly stated?
4. What is the significance of these findings?

Paper text:
{paper_text[:2000]}"""

    @staticmethod
    def get_reproducibility_prompt(paper_text: str) -> str:
        """Get prompt for reproducibility assessment."""
        return f"""Assess the reproducibility of this research:

1. Is the data availability clearly stated?
2. Is the code/implementation available?
3. Are the experimental parameters specified?
4. Can someone replicate this work?

Paper text:
{paper_text[:2000]}"""
