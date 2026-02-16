# Audit Findings

## 1. Architecture: Orchestrator or P2P?

**Claim:** "No central orchestrators, pure P2P coordination"

**Reality:** The Paper Analyzer agent (`agents/paper_analyzer/paper_analyzer_agent.py`) IS a central orchestrator. It explicitly:
- Defines a multi-step workflow (lines 232-238: "1. Extract text from PDF, 2. Analyze content with LLM, 3. Assess FAIR compliance, 4. Synthesize results")
- Controls execution sequence (lines 254-357 in `_analyze_paper` method)
- Discovers and calls other services (PDF Parser, FAIR Assessor)
- Manages data flow between services
- Synthesizes final results from all steps

The documentation attempts to distinguish "composite agents" from "orchestrators" by claiming they use "peer-to-peer service discovery" instead of "centralized control" (ARCHITECTURE.md:96). However, this is a semantic distinction. Dynamic service discovery doesn't change the fact that Paper Analyzer centrally controls a multi-step workflow.

**Verdict:** ❌ **MISLEADING**

**Evidence:**
- agents/paper_analyzer/paper_analyzer_agent.py:232-238 (workflow definition)
- agents/paper_analyzer/paper_analyzer_agent.py:254-357 (orchestration implementation)
- Line 33 comment: "Changed from orchestrator" - explicitly renamed to avoid the term

---

## 2. FDO Self-Description

**Claim:** "Self-describing FDO records with complete metadata"

**Reality:**
- self_description field: ❌ **NO** - Main FDO records contain only a `metadata_pointer` (registry/data/fdos/21.T11148-afdo-pdf-parser.json:11)
- Capability schemas: ⚠️ **EXTERNAL** - Schemas exist but are stored in separate metadata files, not in the FDO record itself
- Examples: ❌ **NO** - No example inputs/outputs in schemas

The FDO records are **NOT** self-describing. They use indirection through metadata pointers. The actual metadata with capability schemas is stored in `registry/data/metadata/` as separate JSON files.

**Verdict:** ⚠️ **MISLEADING / PARTIAL**

**Evidence:**
- registry/data/fdos/21.T11148-afdo-pdf-parser.json:11 - Only has `metadata_pointer`
- registry/data/metadata/21.T11148-afdo-metadata-pdf-parser.json - Actual schemas stored externally

---

## 3. Activity Logs

**Claim:** "Activity logs track all interactions" (README.md:94)

**Reality:**
- activity_log field: ✅ **YES** - Field exists in FDO records (registry/data/fdos/21.T11148-afdo-pdf-parser.json:12)
- Calls logged automatically: ❌ **NO** - Activity log is empty: `"activity_log": []`
- Documentation reveals this is **PLANNED** for Week 2, not implemented (FDO_COMPLIANCE.md:545, CHANGELOG.md:190)

The documentation states "Activity logs maintained in-memory, never persisted. Lost on restart" and describes persistence as "PLANNED" (FDO_COMPLIANCE.md:427).

**Verdict:** ❌ **FALSE** (Feature claimed but not implemented)

**Evidence:**
- registry/data/fdos/21.T11148-afdo-pdf-parser.json:12 - Empty array
- FDO_COMPLIANCE.md:545 - "Week 2 Changes (PLANNED): Activity Log Persistence"
- CHANGELOG.md:391 - "Pending: Activity logs only in-memory"

---

## 4. Type System

**Claim:** "Types are first-class FDOs with PIDs"

**Reality:**
- Types directory exists: ✅ **YES** - `registry/data/types/` exists
- Types directory is: **EMPTY** - No type FDO records found
- fdo_type_pid is: **STRING** - Not a PID format (e.g., `"document_processor"` instead of `"21.T11148/type-document-processor"`)

Types are referenced as plain strings rather than being first-class FDO objects with PIDs. The types directory exists but contains no actual type definitions.

**Verdict:** ❌ **FALSE**

**Evidence:**
- `ls -la registry/data/types/` - Directory is empty (only `.` and `..`)
- registry/data/fdos/21.T11148-afdo-pdf-parser.json:3 - `"fdo_type_pid": "document_processor"` (string, not PID)

---

## SUMMARY

**Critical Issues Found: 4**

1. **Architecture Misrepresentation** - Claims "no orchestrators" but Paper Analyzer clearly orchestrates multi-step workflows. Renamed from "orchestrator" to "composite agent" without changing functionality.

2. **Non-Self-Describing FDOs** - Records use external metadata pointers instead of being self-describing. Core FDO principle violated through indirection.

3. **Missing Activity Logs** - Claimed as implemented feature but actually empty and marked as "PLANNED" in technical docs. Major provenance tracking gap.

4. **Types Not Implemented as FDOs** - Types are strings, not first-class FDO objects with PIDs. Empty types directory contradicts documentation claims.

---

## RECOMMENDATION

**Pick ONE to fix first:** **Activity Logs (#3)**

**Rationale:** This is the most critical for demo credibility because:
- It's claimed as a current feature (not "upcoming") in user-facing docs (README.md, FDO_COMPLIANCE.md)
- Empty activity logs are immediately visible when inspecting FDO records
- It's an FDO compliance requirement, not just an architectural choice
- The gap between claim ("Complete provenance tracking") and reality (empty arrays) is most damaging to trust

The other issues are problematic but involve architectural decisions or semantic debates. Empty activity logs are unambiguous: the feature is claimed but not working.
