# Fact Checker Agent

**Port:** 8013
**Type:** `21.T11148/type-fact-checker-v1`
**Category:** Composite Agent (Multi-Source Verification)

## Overview

The Fact Checker Agent verifies factual claims through **policy-driven multi-source validation**. All delegation behavior is defined in `policy.json` - the agent code contains NO hardcoded logic.

## Key Features

✅ **Multi-Source Validation** - Gathers evidence from multiple independent sources
✅ **Policy-Driven Behavior** - All delegation logic in policy, not code
✅ **Parallel Execution** - Calls multiple agents simultaneously
✅ **Resilient** - Continues if some sources fail (requires minimum 2)
✅ **LLM Synthesis** - Aggregates evidence and calculates confidence
✅ **Transparent** - Complete trace of all sources consulted

## Operations

### 1. `verify_fact`
**Purpose:** Verify a factual claim with confidence scoring

**Input:**
```json
{
  "claim": "Algeria's capital is Algiers",
  "confidence_threshold": 0.7,
  "max_sources": 5
}
```

**Output:**
```json
{
  "claim": "Algeria's capital is Algiers",
  "verified": true,
  "confidence": 0.95,
  "evidence": [
    {
      "source": "Wikipedia Agent",
      "source_pid": "21.T11148/afdo-wikipedia-agent",
      "data": {...},
      "supports_claim": true
    },
    {
      "source": "ArXiv Agent",
      "source_pid": "21.T11148/afdo-arxiv-agent",
      "data": {...},
      "supports_claim": true
    }
  ],
  "synthesis": "All sources confirm that Algiers is the capital of Algeria...",
  "sources_consulted": 3
}
```

### 2. `cross_validate`
**Purpose:** Cross-validate information across multiple sources

**Input:**
```json
{
  "claim": "Statement to validate",
  "sources": ["Wikipedia", "ArXiv", "OpenLibrary"]
}
```

**Output:**
```json
{
  "claim": "Statement to validate",
  "validated": true,
  "consistency_score": 0.88,
  "source_results": [...]
}
```

### 3. `check_claim`
**Purpose:** Quick claim verification (fewer sources, faster)

**Input:**
```json
{
  "claim": "Quick fact to check"
}
```

**Output:**
```json
{
  "claim": "Quick fact to check",
  "likely_true": true,
  "confidence": 0.82
}
```

## How It Works (Policy-Driven)

### Architecture

```
User Query
    ↓
Fact Checker Agent
    ↓
Policy Engine evaluates: verify_fact operation
    ↓
Policy Rule: rule_01_verify_fact_multi_source
    ↓
SEQUENCE with 2 steps:
    ├─ Step 1: SEMANTIC_DISCOVERY (multi-delegate)
    │   ├─ Query: "find and retrieve information about: {claim}"
    │   ├─ top_k: 5 agents
    │   ├─ Parallel execution: YES
    │   ├─ Collect all results: YES
    │   ├─ Min successful: 2
    │   └─ Calls: Wikipedia, ArXiv, OpenLibrary, etc.
    │
    └─ Step 2: SEMANTIC_DISCOVERY (synthesis)
        ├─ Query: "analyze consistency and verify claim..."
        ├─ Filter: has_llm = true
        ├─ Input: Aggregated evidence from Step 1
        └─ Calls: LLM Consultant
            └─ Returns: {verified, confidence, synthesis}
```

### Policy-Driven Multi-Delegation

**Key Policy Parameters (from policy.json):**

```json
{
  "step": 1,
  "action": "semantic_discovery",
  "discovery_query": "find and retrieve information about: {claim}",
  "parameters": {
    "top_k": 5,                    // Use top 5 agents
    "min_similarity": 0.3,          // Minimum score threshold
    "parallel_execution": true,     // Call all simultaneously
    "collect_all_results": true,    // Aggregate ALL results
    "min_successful": 2,            // Need at least 2 sources
    "operation_to_call": "auto_detect"  // Let registry decide operation
  }
}
```

**What This Does:**
1. Registry semantic discovery finds top 5 capable agents
2. All 5 agents called **in parallel** (not sequentially)
3. Results from ALL agents aggregated
4. If any fail, continue if ≥2 succeed
5. Pass aggregated evidence to synthesis step

## Example Execution Flow

### Request:
```bash
curl -X POST http://localhost:8013/doip/extend/verify_fact \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "claim": "Algeria gained independence in 1962"
    }
  }'
```

### Execution Trace:

```
[Step 1] Fact Checker receives verify_fact
[Step 2] Policy Engine matches rule_01_verify_fact_multi_source
[Step 3] Execute SEQUENCE Step 1: Evidence Gathering
    ├─ Registry semantic discovery for: "find and retrieve information about: Algeria gained independence in 1962"
    ├─ Registry returns top 5: Wikipedia (0.82), ArXiv (0.65), OpenLibrary (0.58), ...
    ├─ Parallel delegation to all 5 agents:
    │   ├─ Wikipedia → get_article_summary(Algeria) → ✓ Success
    │   ├─ ArXiv → search_papers(Algeria independence) → ✓ Success
    │   ├─ OpenLibrary → search_books(Algeria history) → ✗ Failed (timeout)
    │   ├─ Chat UI → receive_query → ✓ Success (delegated to LLM)
    │   └─ LLM Consultant → analyze_query_intent → ✓ Success
    ├─ Aggregate results: 4/5 successful (min_successful=2 ✓ met)
    └─ Evidence collected from 4 sources

[Step 4] Execute SEQUENCE Step 2: Synthesis
    ├─ Registry semantic discovery for: "analyze consistency and verify claim..."
    ├─ Filter: has_llm = true
    ├─ Registry returns: LLM Consultant (best match)
    ├─ Delegate to LLM Consultant with:
    │   {
    │     "task": "verify_consistency",
    │     "claim": "Algeria gained independence in 1962",
    │     "evidence": [4 source results],
    │     "instructions": "Analyze consistency, calculate confidence..."
    │   }
    └─ LLM Consultant returns:
        {
          "verified": true,
          "confidence": 0.95,
          "synthesis": "All 4 sources confirm independence in 1962...",
          "supporting_sources": 4,
          "conflicting_sources": 0
        }

[Step 5] Fact Checker returns final result
```

## Cascading Behavior

The Fact Checker creates **4-5 level cascades**:

```
Level 1: User → Chat UI
Level 2: Chat UI → Fact Checker (semantic discovery)
Level 3: Fact Checker → [Wikipedia, ArXiv, OpenLibrary] (parallel)
Level 4: Wikipedia → LLM (if synthesis needed)
Level 5: Fact Checker → LLM Consultant (final synthesis)
```

**Example with deeper cascade:**
```
User: "Is this claim true: X"
  ↓
Chat UI (semantic discovery: "verify")
  ↓
Fact Checker (policy: SEQUENCE)
  ↓ (parallel)
  ├─→ Wikipedia → get_article("X")
  ├─→ ArXiv → search_papers("X")
  │     └─→ Paper Analyzer → PDF Parser (if paper found)
  └─→ OpenLibrary → search_books("X")
  ↓
Fact Checker (aggregate evidence)
  ↓
LLM Consultant (synthesize verification)
  ↓
Fact Checker → Chat UI → User

Cascade Depth: 5-6 levels
Parallel Branches: 3
```

## Policy Configuration

### Rule Priority

1. **Priority 10:** `rule_01_verify_fact_multi_source` - Full verification with synthesis
2. **Priority 9:** `rule_02_cross_validate_multi_source` - Cross-validation across sources
3. **Priority 8:** `rule_03_quick_claim_check` - Quick check (3 sources, faster)
4. **Priority 5:** `rule_04_unknown_operation` - Delegate unknown operations

### Customization

To adjust behavior, edit `policy.json`:

**More sources (higher confidence):**
```json
"top_k": 10,              // Use top 10 agents
"min_successful": 5       // Require 5 successful sources
```

**Faster verification (lower confidence):**
```json
"top_k": 3,               // Only top 3 agents
"min_successful": 1,      // Accept 1 source
"parallel_execution": false  // Sequential (stop early if confident)
```

**Stricter filtering:**
```json
"min_similarity": 0.5     // Higher threshold (more relevant agents only)
```

## Testing

### Test Standalone
```bash
# Start agent
python3 agents/fact_checker/fact_checker_agent.py

# Test verify_fact
curl -X POST http://localhost:8013/doip/extend/verify_fact \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "claim": "The capital of Algeria is Algiers",
      "confidence_threshold": 0.7
    }
  }'
```

### Test with System
```bash
# Start full system
./start_system.sh

# Test via Chat UI
curl -X POST http://localhost:8001/doip/extend/receive_user_input \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "message": "Verify this: Algeria gained independence in 1962"
    }
  }'

# Check trace
ls -lt /tmp/afdo_traces/ | head -1
cat /tmp/afdo_traces/req_XXXXX_*.json | jq .
```

### View Multi-Source Delegation
```bash
# Check system logs for evidence gathering
tail -f logs/system.log | grep -E "(📊|Step 1|Step 2|evidence|synthesis)"

# Should see:
# [Fact Checker] Executing Step 1: Evidence gathering
# [Fact Checker] Delegating to Wikipedia Agent
# [Fact Checker] Delegating to ArXiv Agent
# [Fact Checker] Delegating to OpenLibrary Agent
# [Fact Checker] Aggregated 3 results
# [Fact Checker] Executing Step 2: Synthesis
# [Fact Checker] Delegating to LLM Consultant
```

## No Hardcoded Behavior

**Agent Code (`fact_checker_agent.py`):**
- ✅ Generic `handle_operation()` - routes to policy
- ✅ Input validation only
- ✅ No delegation logic
- ✅ No hardcoded agent references
- ✅ All behavior driven by `policy.json`

**Policy File (`policy.json`):**
- ✅ Defines SEQUENCE steps
- ✅ Specifies multi-source gathering
- ✅ Defines synthesis step
- ✅ Configures parallel execution
- ✅ Sets thresholds and filters

**Result:** Change policy → change behavior. No code changes needed!

## Cost Estimation

| Operation | Sources | Typical Cost |
|-----------|---------|-------------|
| verify_fact | 3-5 sources + LLM | $0.05-0.15 |
| cross_validate | 3-5 sources + LLM | $0.05-0.15 |
| check_claim | 2-3 sources + LLM | $0.03-0.10 |

**Breakdown:**
- Fact Checker coordination: $0.05
- Each data source: $0.01-0.02
- LLM synthesis: $0.03-0.05
- **Total:** Depends on sources consulted

## Troubleshooting

**Issue:** "Not enough successful sources"
- **Cause:** Less than `min_successful` agents responded
- **Solution:** Lower `min_successful` in policy or increase `top_k`

**Issue:** "No LLM agent found for synthesis"
- **Cause:** LLM Consultant not running or not registered
- **Solution:** Check `./check_status.sh` and restart if needed

**Issue:** "High latency"
- **Cause:** Sequential execution or too many sources
- **Solution:** Ensure `parallel_execution: true` in policy, reduce `top_k`

## Future Enhancements

Possible policy additions:
- Source credibility scoring
- Temporal verification (check publication dates)
- Contradiction detection and resolution
- Evidence quality assessment
- Budget-aware source selection
- Adaptive confidence thresholds

---

**Version:** 1.0.0
**Created:** 2026-02-15
**Type:** `21.T11148/type-fact-checker-v1`
**Port:** 8013
