# aFDO Autonomous Marketplace Guide

## Overview

The aFDO system has been transformed from a centralized orchestration model into a **true autonomous agent marketplace** where agents discover, negotiate, select, and coordinate services based on economic principles.

## Key Concepts

### 1. Autonomous Agents
Every aFDO is now:
- **Autonomous**: Makes its own decisions about service selection
- **Economic**: Has budget awareness and evaluates cost/quality trade-offs
- **Resilient**: Automatically finds alternatives when services fail
- **Policy-driven**: Can use hardcoded workflows OR autonomous selection
- **Market participant**: Can negotiate prices and build reputation
- **FDO Compliant**: Has persistent identifier (PID), self-describing metadata, DOIP protocol support

### 2. No Orchestrators - Composite Agents Only
- **Before**: NL Handler and Paper Analyzer were called "orchestrators"
- **After**: Terminology updated to "composite agents" - more accurate for P2P coordination
- **Composite agents**: Coordinate workflows by autonomously hiring services from marketplace
- **Key difference**: No centralized control - each agent makes own decisions
- **Registry Role**: Passive service directory only - provides information, never orchestrates

### 3. Economic Decision Making
Agents select services based on:
- **Cost**: Dynamic pricing based on queue load
- **Reputation**: Dual-path (objective metrics + caller ratings)
- **Availability**: Queue status and wait times
- **Policy**: Cheapest, fastest, best reputation, or balanced

### 4. FDO Compliance
All agents are **FAIR Digital Objects** with:
- **PIDs**: Handle-based persistent identifiers (e.g., `21.T11148/afdo-paper-analyzer`)
- **Self-Describing**: Comprehensive metadata with schemas and provenance
- **DOIP Protocol**: Digital Object Interface Protocol 2.0
- **Discoverable**: Registered in central registry with searchable metadata
- **Interoperable**: Standard communication protocols

📖 **See [FDO_COMPLIANCE.md](../FDO_COMPLIANCE.md) for detailed documentation**

## Architecture

### Agent Types

#### 1. Interface Agents
**Chat UI** (`port 8001`)
- Receives user queries with budget allocation
- Interprets queries using built-in LLM
- Plans workflows autonomously
- Estimates costs before execution
- Displays results with budget breakdown

#### 2. Composite Agents
**Paper Analyzer** (`port 8003`)
- Autonomous composite agent that coordinates multi-step workflows
- Budget-aware: tracks spending across workflow
- Uses `call_with_alternatives()` for automatic failover
- Returns detailed cost breakdown
- Selection policy: balanced (configurable)
- Operates via P2P marketplace - no centralized orchestration

**NL Handler** (`port 8002`)
- Scientific query interpretation composite agent
- Plans and executes workflows autonomously
- Built-in LLM for natural language understanding
- Discovers and hires services from marketplace

#### 3. Task Agents
**PDF Parser** (`port 8004`)
- Extracts text/metadata from PDFs
- Queue-based pricing
- Reports performance metrics

**FAIR Assessor** (`port 8005`)
- Assesses FAIR compliance
- Rule-based evaluation
- Low cost, high reliability

**LLM Endpoints** (`ports 8007, 8008`)
- GPT-4 and GPT-4-mini services
- Token-based pricing
- Quality vs cost trade-offs

#### 4. Infrastructure
**Registry** (`port 8000`)
- Passive service directory
- 15 marketplace endpoints
- Real-time status tracking
- Reputation management
- Failure reporting

## Marketplace Features

### 1. Dynamic Pricing

```python
# Base cost when idle
base_cost = 0.05

# Price increases with queue length
current_price = base_cost * (1 + (queue_length / max_queue_size) * surge_factor)

# Example: 5 requests in queue of max 10
# price = 0.05 * (1 + (5/10) * 2.0) = $0.10
```

### 2. Budget Management

```python
# User provides budget
budget = BudgetManager(total_budget=1.0)

# Agent reserves before calling service
reservation_id = budget.reserve(0.25, "extract_text", "pdf_parser_001")

# After successful call, commit actual cost
budget.commit(reservation_id, actual_cost=0.23)

# Budget breakdown always returned
print(budget.get_breakdown())
# {
#   "allocated": 1.0,
#   "spent": 0.23,
#   "remaining": 0.77,
#   "by_operation": {...}
# }
```

### 3. Reputation System

**Dual-Path Scoring:**
```
Reputation Score = (success_rate × 0.4) +
                   (response_time_accuracy × 0.2) +
                   (average_caller_rating × 0.3) +
                   (uptime × 0.1)
```

**Rating Submission:**
```python
# After successful operation, caller rates provider
await registry.submit_rating({
    "agent_pid": "pdf_parser_001",
    "caller_pid": "paper_analyzer_001",
    "overall": 4.5,  # 1-5 scale
    "speed": 5.0,
    "quality": 4.0,
    "value": 5.0
})
```

### 4. Negotiation

```python
# Request quote
quote = await agent.get_quote(
    operation="extract_text",
    parameters={...},
    priority="normal"
)

# Negotiate if too expensive
negotiation_result = await agent.negotiate(
    QuoteRequest(
        operation="extract_text",
        max_budget=0.03,  # Lower than quote
        reason="budget_constraint"
    )
)

if negotiation_result.accepted:
    # Proceed at negotiated price
    final_cost = negotiation_result.final_cost
else:
    # Try alternative provider
    pass
```

### 5. Failure Recovery

```python
# Automatic alternatives on failure
result = await agent.call_with_alternatives(
    operation="extract_text",
    parameters={...},
    budget=budget_manager,
    max_retries=2
)

# Workflow:
# 1. Attempt with Provider A → FAILS
# 2. Report failure to registry
# 3. Find alternatives excluding A
# 4. Attempt with Provider B → SUCCESS
# 5. Return result with cost metadata
```

### 6. Selection Policies

```python
# Configure agent's selection policy
agent = PaperAnalyzerAgent()
agent.selection_policy = "balanced"  # Default

# Available policies:
# - "cheapest": Minimize cost
# - "fastest": Minimize wait time
# - "best_reputation": Maximize reliability
# - "balanced": 40% cost + 30% reputation + 30% speed
# - "value": Best reputation/cost ratio
# - "availability": Shortest queue
```

## Usage Examples

### Example 1: Simple Query with Budget

```python
# User submits query via Chat UI
result = await chat_ui.handle_operation(
    operation="receive_user_input",
    caller_pid="user",
    parameters={
        "message": "Analyze this research paper",
        "pdf_data": base64_pdf,
        "budget": 0.50,
        "policy": "balanced"
    }
)

# Chat UI:
# 1. Interprets query → "analyze_paper"
# 2. Plans workflow → [Paper Analyzer]
# 3. Estimates cost → $0.35
# 4. Executes with budget tracking
# 5. Returns result + budget breakdown

print(result["budget_summary"])
# {
#   "allocated": 0.50,
#   "spent": 0.33,
#   "remaining": 0.17,
#   "breakdown": {
#     "pdf_extraction": 0.05,
#     "fair_assessment": 0.02,
#     "llm_analysis": 0.21,
#     "coordination": 0.05
#   }
# }
```

### Example 2: Budget-Constrained Workflow

```python
# User has limited budget
result = await chat_ui.handle_operation(
    operation="receive_user_input",
    parameters={
        "message": "Analyze paper",
        "pdf_data": pdf,
        "budget": 0.10,  # Very limited
        "policy": "cheapest"  # Cost optimization
    }
)

# System behavior:
# - Uses "cheapest" policy for all selections
# - Skips optional steps if budget insufficient
# - Returns partial results with explanation
# - Shows what was completed vs skipped
```

### Example 3: High-Priority, Time-Sensitive

```python
result = await chat_ui.handle_operation(
    operation="receive_user_input",
    parameters={
        "message": "Quick FAIR check",
        "metadata": metadata,
        "budget": 1.0,  # Generous budget
        "policy": "fastest"  # Speed priority
    }
)

# System behavior:
# - Selects agents with shortest queues
# - Willing to pay surge pricing
# - Completes in minimal time
```

## Registry Marketplace Endpoints

### Market Intelligence
```
GET /market/agents/by_operation/{operation}?sort_by=reputation
```
Returns agents sorted by reputation, cost, or load.

### Reputation
```
POST /reputation/update
POST /reputation/rate
GET /reputation/{agent_pid}
```

### Live Status
```
GET /status/agents
GET /status/agent/{agent_pid}
POST /status/update  # Heartbeat
```

### Failure Recovery
```
POST /failures/report
GET /failures/{agent_pid}
GET /alternatives/{agent_pid}/{operation}
```

### Analytics
```
GET /analytics/market
```
Returns marketplace health, average costs, agent counts.

## Data Flow Example

**Budget-Aware Paper Analysis:**

```
User → Chat UI: "Analyze this paper" + PDF + Budget=$1.00
  ↓
Chat UI interprets → "analyze_paper"
Chat UI plans → [Paper Analyzer]
Chat UI estimates → $0.45
Chat UI creates BudgetManager($1.00)
  ↓
Chat UI → Registry: Get agents for "analyze_paper_budget"
Registry → Chat UI: [Paper Analyzer (rep=0.92, cost=$0.05)]
  ↓
Chat UI → Paper Analyzer: analyze_paper_budget + budget=$1.00
  ↓
Paper Analyzer reserves $0.05 coordination fee
Paper Analyzer → Registry: Get agents for "extract_text"
Registry → Paper Analyzer: [Parser A ($0.05), Parser B ($0.03)]
Paper Analyzer selects B (cheapest with balanced policy)
  ↓
Paper Analyzer → PDF Parser B: extract_text
PDF Parser B → Paper Analyzer: {text, cost=$0.03, duration=2.1s}
  ↓
Paper Analyzer commits $0.03, remaining=$0.92
Paper Analyzer → Registry: Get agents for "summarize"
Registry → Paper Analyzer: [LLM A ($0.30), LLM B ($0.20)]
  ↓
Paper Analyzer → LLM B: summarize
LLM B → Paper Analyzer: {summary, cost=$0.18}
  ↓
Paper Analyzer commits $0.18, remaining=$0.74
Paper Analyzer commits coordination $0.05
Total spent: $0.26
  ↓
Paper Analyzer → Chat UI: {results, budget_summary}
Chat UI → User: Results + "Cost: $0.26 of $1.00"
```

**Key**: Domain agents autonomously discover and select services from marketplace.

## Testing

Run marketplace tests:
```bash
# Foundation components
pytest tests/test_marketplace_foundation.py -v

# End-to-end workflows
pytest tests/test_autonomous_workflows.py -v

# Registry endpoints
pytest tests/test_registry_marketplace.py -v
```

## Success Metrics

✅ **Marketplace-based discovery** in call traces
✅ **Dynamic pricing** adjusts with load
✅ **Budget tracked** accurately (no over-spending)
✅ **Negotiation** working (accept/reject/counter-offer)
✅ **Reputation** updates in real-time
✅ **Automatic alternatives** on failure
✅ **Policy-based selection** working
✅ **Registry passive** (no orchestration)

## Migration from Legacy System

### Before (Old Terminology: "Orchestrator" Pattern)

**Note**: This was the terminology used before Week 1 FDO compliance updates. "Orchestrator" has been replaced with "composite agent" to accurately reflect P2P coordination.
```python
# Paper Analyzer directly calls specific agents
pdf_parsers = await self.discover_by_operation("extract_text")
result = await self.call_other_afdo(pdf_parsers[0]["pid"], "extract_text", data)
```

### After (Marketplace Pattern)
```python
# Paper Analyzer uses marketplace with automatic alternatives
result = await self.call_with_alternatives(
    operation="extract_text",
    parameters=data,
    budget=budget_manager,
    max_retries=2
)
```

## Advanced Features

### Custom Selection Policy
```python
from shared.selection_policy import CustomPolicy

def my_scoring(quote, reputation):
    # Custom logic
    return (reputation * 0.5) + (1.0 / quote.estimated_cost * 0.5)

agent.selection_policy = CustomPolicy(scoring_function=my_scoring)
```

### Bulk Operations
```python
# Request bulk discount
quote_request = QuoteRequest(
    operation="analyze_papers",
    quantity=10,  # Bulk request
    max_budget=4.0
)

# Provider may offer package pricing
result = await agent.negotiate(quote_request)
if result.accepted:
    # Bulk discount applied
    per_paper_cost = result.final_cost / 10
```

## Troubleshooting

### Issue: Budget exhaustion mid-workflow
**Solution**: Increase budget or use "cheapest" policy

### Issue: All alternatives failing
**Solution**: Check registry for agent availability, restart failed agents

### Issue: Reputation not updating
**Solution**: Ensure heartbeat active, check `/status/agents` endpoint

### Issue: High costs
**Solution**: Use "cheapest" policy, negotiate, or wait for lower queue times

## Future Enhancements

- **Market-driven pricing**: Supply/demand economics
- **Agent specialization bonuses**: Higher reputation for specialized work
- **Predictive cost estimation**: ML-based cost prediction
- **Quality-of-service tiers**: Premium vs standard service levels
- **Cross-registry federation**: Multi-marketplace support
