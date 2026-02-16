"""FAIR compliance assessment criteria and scoring."""

from typing import Dict, Any, List, Tuple


class FAIRCriteria:
    """FAIR principles assessment criteria."""

    @staticmethod
    def assess_findable(metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Assess Findable principles (F1-F4).

        Args:
            metadata: Metadata to assess

        Returns:
            (score, suggestions) tuple
        """
        score = 0.0
        suggestions = []
        max_score = 4.0

        # F1: Globally unique and persistent identifier
        if metadata.get("pid") or metadata.get("doi") or metadata.get("identifier"):
            score += 1.0
        else:
            suggestions.append("F1: Add globally unique identifier (PID, DOI, etc.)")

        # F2: Data described with rich metadata
        required_fields = ["title", "description", "keywords", "author"]
        present_fields = sum(1 for field in required_fields if metadata.get(field))
        f2_score = present_fields / len(required_fields)
        score += f2_score
        if f2_score < 1.0:
            missing = [f for f in required_fields if not metadata.get(f)]
            suggestions.append(f"F2: Add metadata fields: {', '.join(missing)}")

        # F3: Metadata clearly includes identifier
        if metadata.get("pid") and "pid" in str(metadata.get("description", "")).lower():
            score += 1.0
        else:
            suggestions.append("F3: Reference identifier in description/metadata")

        # F4: Indexed in searchable resource
        if metadata.get("indexed_in") or metadata.get("repository"):
            score += 1.0
        else:
            suggestions.append("F4: Register in searchable repository/index")

        return score / max_score, suggestions

    @staticmethod
    def assess_accessible(metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Assess Accessible principles (A1-A2).

        Args:
            metadata: Metadata to assess

        Returns:
            (score, suggestions) tuple
        """
        score = 0.0
        suggestions = []
        max_score = 2.0

        # A1: Retrievable by identifier using standard protocol
        if metadata.get("access_url") or metadata.get("endpoint"):
            score += 1.0
        else:
            suggestions.append("A1: Provide access URL or retrieval endpoint")

        # A2: Metadata accessible even when data unavailable
        if metadata.get("metadata_preserved") or metadata.get("persistent_metadata"):
            score += 1.0
        else:
            suggestions.append("A2: Ensure metadata persists independently of data")

        return score / max_score, suggestions

    @staticmethod
    def assess_interoperable(metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Assess Interoperable principles (I1-I3).

        Args:
            metadata: Metadata to assess

        Returns:
            (score, suggestions) tuple
        """
        score = 0.0
        suggestions = []
        max_score = 3.0

        # I1: Formal, accessible, shared knowledge representation
        if metadata.get("format") or metadata.get("schema"):
            score += 1.0
        else:
            suggestions.append("I1: Specify data format and schema")

        # I2: Uses FAIR-compliant vocabularies
        if metadata.get("vocabulary") or metadata.get("ontology"):
            score += 1.0
        else:
            suggestions.append("I2: Use standardized vocabularies/ontologies")

        # I3: Includes qualified references to other data
        if metadata.get("references") or metadata.get("related_data"):
            score += 1.0
        else:
            suggestions.append("I3: Add references to related datasets")

        return score / max_score, suggestions

    @staticmethod
    def assess_reusable(metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Assess Reusable principles (R1-R4).

        Args:
            metadata: Metadata to assess

        Returns:
            (score, suggestions) tuple
        """
        score = 0.0
        suggestions = []
        max_score = 4.0

        # R1: Rich attributes for data and metadata
        detailed_fields = ["methodology", "provenance", "creation_date", "version"]
        present = sum(1 for field in detailed_fields if metadata.get(field))
        r1_score = present / len(detailed_fields)
        score += r1_score
        if r1_score < 1.0:
            missing = [f for f in detailed_fields if not metadata.get(f)]
            suggestions.append(f"R1: Add detailed attributes: {', '.join(missing)}")

        # R2: Clear and accessible usage license
        if metadata.get("license") or metadata.get("usage_rights"):
            score += 1.0
        else:
            suggestions.append("R2: Specify clear usage license")

        # R3: Detailed provenance
        if metadata.get("provenance") or metadata.get("lineage"):
            score += 1.0
        else:
            suggestions.append("R3: Document data provenance and lineage")

        # R4: Meets domain-relevant community standards
        if metadata.get("standards_compliance") or metadata.get("community_standard"):
            score += 1.0
        else:
            suggestions.append("R4: Document compliance with domain standards")

        return score / max_score, suggestions

    @staticmethod
    def assess_overall(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform complete FAIR assessment.

        Args:
            metadata: Metadata to assess

        Returns:
            Complete assessment results
        """
        # Assess each principle
        f_score, f_suggestions = FAIRCriteria.assess_findable(metadata)
        a_score, a_suggestions = FAIRCriteria.assess_accessible(metadata)
        i_score, i_suggestions = FAIRCriteria.assess_interoperable(metadata)
        r_score, r_suggestions = FAIRCriteria.assess_reusable(metadata)

        # Calculate overall score
        overall_score = (f_score + a_score + i_score + r_score) / 4.0

        # Determine compliance level
        if overall_score >= 0.8:
            compliance_level = "Excellent"
        elif overall_score >= 0.6:
            compliance_level = "Good"
        elif overall_score >= 0.4:
            compliance_level = "Fair"
        else:
            compliance_level = "Needs Improvement"

        return {
            "overall_score": round(overall_score, 2),
            "compliance_level": compliance_level,
            "principle_scores": {
                "findable": round(f_score, 2),
                "accessible": round(a_score, 2),
                "interoperable": round(i_score, 2),
                "reusable": round(r_score, 2)
            },
            "suggestions": {
                "findable": f_suggestions,
                "accessible": a_suggestions,
                "interoperable": i_suggestions,
                "reusable": r_suggestions
            },
            "total_suggestions": len(f_suggestions) + len(a_suggestions) +
                               len(i_suggestions) + len(r_suggestions)
        }
