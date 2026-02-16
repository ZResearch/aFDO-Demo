# aFDO System Architecture - Technical Report

**Version:** 2.0.0
**Last Updated:** 2026-02-15
**Status:** Production specification with documented aspirational features

---

## Implementation Status

This document describes both **implemented features** and **aspirational architecture**. Key distinctions:

**✅ Fully Implemented:**
- Policy-driven agent behavior
- Semantic discovery with operation-based matching
- **Multi-level cascading delegation** (agents recursively delegate via policy decisions)
- **Automatic synthesis detection** (query_requires_synthesis condition in policies)
- Reputation tracking (formula and metrics)
- Execution trace capture and nesting
- Cost tracking throughout system

**⚠️ Partially Implemented:**
- Budget enforcement (tracked but not strictly enforced)

**📋 Designed But Not Used in Production:**
- Workflow generation (LLM Consultant can generate workflows via LLM, but not called)
- WorkflowEngine (complete implementation, never instantiated)
- Negotiation protocol (fully coded, agents use direct `call_other_afdo` instead)
- Dynamic pricing (base costs only, no reputation-based discounting)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Core Components](#core-components)
4. [Agent Types and Taxonomy](#agent-types-and-taxonomy)
5. [Semantic Discovery](#semantic-discovery)
6. [Cascading Delegation](#cascading-delegation)
7. [Reputation Tracking](#reputation-tracking)
8. [Policy Engine](#policy-engine)
9. [Trace Aggregation](#trace-aggregation)
10. [How to Add a New aFDO](#how-to-add-a-new-afdo)
11. [Fallback Chains](#fallback-chains)
12. [Data Flow Examples](#data-flow-examples)
13. [FDO Compliance](#fdo-compliance)

---

## System Overview

### High-Level Architecture

The aFDO system is a **multi-agent marketplace** for scientific research analysis built on FAIR Digital Object principles. The architecture combines:

- **Centralized Discovery** (Registry at port 8000)
- **Distributed Execution** (13 independent agents on ports 8001-8014)
- **Semantic Service Discovery** (Operation-based, not type-based)
- **Policy-Driven Autonomy** (JSON policies, not hardcoded logic)
- **Budget-Aware Workflows** (Cost tracking and optimization)
- **Provenance Tracking** (Complete execution traces)

```
┌─────────────────────────────────────────────────────────────┐
│                     User / Client                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Chat UI (8001) - Entry Point                   │
│  • Natural language interpretation                          │
│  • Workflow planning                                        │
│  • Budget management                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│          Registry (8000) - Service Discovery                │
│  • FDO record storage                                       │
│  • Agent discovery by operation                             │
│  • Marketplace coordination                                 │
│  • Reputation tracking                                      │
│  • Activity logging                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Agent Marketplace                         │
├─────────────────────┬───────────────────┬───────────────────┤
│   Task Agents       │ Composite Agents  │ External Sources  │
│                     │                   │                   │
│ • PDF Parser (8004) │ • Paper Analyzer  │ • Wikipedia (8010)│
│ • FAIR Assessor     │   (8003)          │ • ArXiv (8011)    │
│   (8005)            │ • NL Handler      │ • Open Library    │
│ • LLM GPT-4 (8007)  │   (8002)          │   (8012)          │
│ • LLM GPT-4-mini    │ • LLM Consultant  │                   │
│   (8008)            │   (8014)          │                   │
│ • Creator (8006)    │                   │                   │
└─────────────────────┴───────────────────┴───────────────────┘
```

### Key Characteristics

1. **Hybrid Architecture:** Centralized discovery + distributed execution
2. **Autonomous Agents:** Policy-driven decision making
3. **Dynamic Discovery:** Operation-based service location
4. **Budget-Aware:** Cost tracking throughout workflow
5. **Fault-Tolerant:** Automatic failover with alternatives
6. **Transparent:** Complete provenance and tracing

---

## Architecture Pattern

### Hybrid Design

The system uses a **hybrid architecture** that balances centralized coordination with distributed autonomy:

**Centralized Components:**
- **Registry (Port 8000):** FDO storage, discovery, coordination
- **Type System:** Shared type definitions
- **Activity Logging:** Centralized log aggregation

**Distributed Components:**
- **Agents (Ports 8001-8014):** Independent FastAPI services
- **Peer-to-Peer Communication:** Direct agent-to-agent calls after discovery
- **Local Decision Making:** Policy-based autonomous behavior

### Why Hybrid?

**Advantages:**
- **Discovery Efficiency:** Central registry for fast service location
- **Execution Performance:** Direct P2P calls avoid bottlenecks
- **Fault Tolerance:** Agents can discover alternatives
- **Scalability:** Add agents without registry changes
- **Transparency:** Central logging for audit trail

**Trade-offs:**
- **Not Fully Distributed:** Registry is single point of discovery
- **Not Fully Centralized:** No centralized data flow
- **Heartbeat Required:** Agents must actively register

---

## Core Components

### 1. FDO Registry (Port 8000)

**Location:** `registry/main.py`
**Storage:** `registry/file_storage.py` (JSON files)

**Responsibilities:**
1. **FDO Record Management**
   - Create, read, update, delete FDO records
   - Store agent metadata and capabilities
   - Track agent status (active/inactive)

2. **Service Discovery**
   - Operation-based search (`/market/agents/by_operation/{op}`)
   - Type-based search (`/doip/search/fdos`)
   - Filtered search with criteria

3. **Marketplace Coordination**
   - Agent registration and heartbeats
   - Queue depth tracking
   - Cost and reputation aggregation

4. **Activity Logging**
   - Aggregate activity logs from all agents
   - Provide per-agent activity history
   - Generate system-wide analytics

5. **Health Monitoring**
   - Heartbeat timeout detection (60s)
   - Automatic agent cleanup (24h inactive)
   - System health status

**Key Endpoints:**
```
GET  /                                    # Registry info
POST /doip/create/fdo                     # Register agent
GET  /doip/read/fdo/{pid}                 # Get agent details
GET  /doip/search/fdos                    # Search agents
GET  /market/agents/by_operation/{op}     # Find by operation
GET  /registry/fdos/{pid}/activity_log    # Agent activity
POST /status/update                       # Heartbeat
GET  /health                              # System health
```

**Storage Structure:**
```
registry/data/
├── fdos/           # Agent records (JSON)
├── metadata/       # Metadata records (JSON)
├── types/          # Type definitions
├── profiles/       # Profile definitions
└── operations/     # Operation registry
```

### 2. Shared Infrastructure

**Location:** `shared/` directory

**Core Modules:**

#### afdo_base.py (119KB, 3000+ lines)
Base class for all agents providing:
- Auto-registration with registry
- DOIP communication methods
- Discovery methods (`discover_by_operation`, `discover_by_type`)
- Budget management integration
- Policy engine integration
- Heartbeat mechanism
- Activity logging
- Execution tracing

**Key Methods:**
```python
async def register_self()              # Register with registry
async def discover_by_operation(op)    # Find agents by operation
async def call_other_afdo(pid, op)     # Direct P2P call
async def call_with_alternatives(op)   # Call with failover
def handle_operation_with_policy(op)   # Policy-based routing
```

#### budget_manager.py
- Budget allocation and tracking
- Reservation and commit pattern
- Transaction management
- Cost breakdown generation

#### reputation_manager.py
- Dual-path reputation system
- Objective metrics (success rate, accuracy)
- Subjective ratings (caller feedback)
- Reputation score calculation

#### selection_policy.py
- Policy-based agent selection
- Six policies: cheapest, fastest, balanced, best_reputation, value, availability
- Customizable weights

#### policy_engine.py
- JSON policy interpretation
- Rule-based decision making
- Priority-based rule matching
- Structured decisions with reasoning

#### execution_trace.py
- Complete execution trace capture
- Event logging with timestamps
- Agent interaction tracking
- Cost and duration tracking
- Human-readable trace formatting

#### queue_manager.py
- Request queuing
- Surge pricing based on load
- Queue depth tracking

#### negotiation.py
- Quote generation
- Price negotiation
- Cost estimation

---

## Agent Types and Taxonomy

### Agent Classification

Agents are classified by **autonomy level** rather than technical implementation:

#### 1. Task Agents
**Characteristics:**
- Execute specific, well-defined operations
- No internal workflow orchestration
- Do not call other agents (typically)
- Deterministic behavior

**Examples:**
- **PDF Parser (8004):** Extract text/metadata from PDFs
- **FAIR Assessor (8005):** Evaluate FAIR compliance
- **LLM GPT-4 (8007):** General-purpose LLM service
- **LLM GPT-4-mini (8008):** Cost-effective LLM service

**Operations:** Single-step, atomic operations

#### 2. Composite Agents
**Characteristics:**
- Coordinate multi-step workflows
- Discover and call other agents
- Budget-aware service selection
- Built-in LLMs for planning/synthesis

**Examples:**
- **Paper Analyzer (8003):** Orchestrates paper analysis workflow
- **NL Handler (8002):** Interprets queries and plans execution
- **LLM Consultant (8014):** Generates dynamic workflows

**Operations:** Multi-step workflows with delegation

#### 3. Interface Agents
**Characteristics:**
- User-facing entry points
- Natural language interpretation
- Workflow planning
- Route requests to appropriate agents

**Examples:**
- **Chat UI (8001):** Web interface with planning
- **NL Handler (8002):** Natural language query processor

**Operations:** User interaction, delegation, result synthesis

#### 4. Meta Agents
**Characteristics:**
- System-level operations
- Registry write privileges
- Agent lifecycle management

**Examples:**
- **Creator (8006):** Creates and registers new agents

**Operations:** System administration

#### 5. Data Source Agents
**Characteristics:**
- Connect to external APIs
- Fetch data from public sources
- No internal LLMs
- Policy-driven delegation

**Examples:**
- **Wikipedia Agent (8010):** Wikipedia articles
- **ArXiv Agent (8011):** Scientific papers
- **Open Library Agent (8012):** Book information

**Operations:** Data retrieval from external sources

### Agent Comparison

| Agent | Port | Category | LLM | Cost | Calls Others | Purpose |
|-------|------|----------|-----|------|--------------|---------|
| PDF Parser | 8004 | Task | No | $0.05 | No | Extract PDF content |
| FAIR Assessor | 8005 | Task | No | $0.02 | No | FAIR compliance |
| Creator | 8006 | Meta | No | $0.00 | No | Create agents |
| LLM GPT-4 | 8007 | Task | Yes | $0.03/1K | No | LLM service |
| LLM GPT-4-mini | 8008 | Task | Yes | $0.005/1K | No | Cheap LLM |
| Wikipedia | 8010 | Data Source | No | $0.01 | Yes (complex) | Wikipedia data |
| ArXiv | 8011 | Data Source | No | $0.02 | Yes (complex) | ArXiv papers |
| Open Library | 8012 | Data Source | No | $0.01 | Yes (complex) | Book data |
| NL Handler | 8002 | Interface/Composite | Yes | $0.05 | Yes | NL processing |
| Paper Analyzer | 8003 | Composite | Yes | $0.05 | Yes | Paper analysis |
| Chat UI | 8001 | Interface | Yes | $0.00 | Yes | Web interface |
| LLM Consultant | 8014 | Composite | Yes | $0.10 | No | Workflow generation |

---

## Semantic Discovery

### How It Works

The system uses **operation-based discovery** rather than type-based discovery:

**Traditional Approach (Type-Based):**
```
Client needs: "PDF processing"
→ Search for: type="PDF Processor"
→ Problem: What if new processor has different type?
```

**aFDO Approach (Operation-Based):**
```
Client needs: "extract_text" operation
→ Search for: operation="extract_text"
→ Finds: Any agent offering extract_text, regardless of type
→ Benefit: New agents automatically discovered
```

### Discovery Process

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Client Needs Operation                          │
│   "I need to extract text from a PDF"                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: Query Registry                                  │
│   GET /market/agents/by_operation/extract_text          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: Registry Returns Candidates                     │
│   [                                                      │
│     {pid: "pdf-parser-1", cost: 0.05, rep: 0.87},      │
│     {pid: "pdf-parser-2", cost: 0.03, rep: 0.82}       │
│   ]                                                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: Apply Selection Policy                          │
│   Policy: "balanced" (cost 40%, rep 30%, speed 30%)    │
│   Selected: pdf-parser-1 (higher reputation)            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: Direct P2P Call                                 │
│   POST http://localhost:8004/doip/call                  │
│   {operation: "extract_text", parameters: {...}}        │
└─────────────────────────────────────────────────────────┘
```

### Discovery API

**Find agents by operation:**
```python
# In agent code (using aFDOBase)
agents = await self.discover_by_operation("extract_text")
```

**Registry endpoint:**
```bash
curl http://localhost:8000/market/agents/by_operation/extract_text
```

**Response structure:**
```json
{
  "status": "success",
  "operation": "extract_text",
  "agents": [
    {
      "pid": "21.T11148/afdo-pdf-parser",
      "name": "PDF Parser",
      "current_cost": 0.05,
      "reputation": 0.87,
      "queue_depth": 0,
      "estimated_duration": 2.5,
      "status": "active",
      "operations": ["extract_text", "extract_metadata", "extract_tables"]
    }
  ],
  "count": 1
}
```

### Multi-Objective Scoring (Algorithm 1)

The registry implements **Algorithm 1: Capability-Based Semantic Discovery and Ranking** from the aFDO paper.

**Implementation:** `registry/main.py` lines 712-830

**Formula:**
```
score(a_i, o_{i,j}) = α·s_{i,j} + β·r_i - γ·(c_{i,j}/c_max)

where:
- s_{i,j} = max(s^op_{i,j}, s^agent_i)  # Paper's Algorithm 1, Line 8
- α = 0.6 (semantic similarity weight - most important)
- β = 0.3 (reputation weight - quality matters)
- γ = 0.1 (cost penalty weight - prefer cheaper)
- α + β + γ = 1 (normalized weights)
```

**Components:**

**1. Semantic Similarity (s_{i,j}):**
- Uses sentence transformers for embedding-based matching
- Compares query against both agent description AND individual operations
- Takes maximum: `max(best_operation_score, agent_score)`
- Example: "who is president of Algeria" → Wikipedia agent=0.427, best_op=0.303 → s_{i,j}=0.427

**2. Reputation (r_i):**
- Agent's historical performance score (0-1 scale)
- Based on success rate, duration accuracy, caller ratings, uptime
- Default for new agents: 0.5
- Example: Wikipedia agent → 0.500

**3. Cost Normalization (c_{i,j}/c_max):**
- c_max = maximum cost among all candidate agents
- Normalized cost: agent_cost / c_max
- Prevents expensive agents from dominating when costs vary widely
- Example: $0.01 / $0.05 = 0.200

**Scoring Example:**

```
Query: "who is the president of Algeria"

Wikipedia Agent:
  - Semantic: max(agent=0.427, best_op=0.303) = 0.427
  - Reputation: 0.500
  - Cost: $0.01, normalized = 0.200

  Final Score = 0.6(0.427) + 0.3(0.500) - 0.1(0.200)
              = 0.256 + 0.150 - 0.020
              = 0.386

Chat UI Agent:
  - Semantic: max(agent=0.256, best_op=0.243) = 0.256
  - Reputation: 0.500
  - Cost: $0.00, normalized = 0.000

  Final Score = 0.6(0.256) + 0.3(0.500) - 0.1(0.000)
              = 0.154 + 0.150 - 0.000
              = 0.304

Selection: Wikipedia Agent (0.386 > 0.304)
```

**Benefits:**

1. **Quality-Aware:** Prefers proven agents with good reputation
2. **Cost-Aware:** Slight preference for cheaper agents when similar
3. **Semantic-First:** Relevance (60%) matters most, not just cost
4. **Configurable:** Weights can be tuned based on priorities
5. **Production-Ready:** More robust than pure semantic or pure cost-based

**Tuning Weights:**

For different priorities, adjust α, β, γ (must sum to 1):

```python
# High Accuracy Priority (research tasks)
α = 0.8, β = 0.15, γ = 0.05  # Semantic match is critical

# High Reliability Priority (production tasks)
α = 0.5, β = 0.4, γ = 0.1    # Proven agents preferred

# Cost-Conscious Priority (batch processing)
α = 0.5, β = 0.2, γ = 0.3    # Strongly prefer cheaper
```

**Comparison with Simple Policies:**

The system also supports simpler client-side selection policies for specific use cases:

**1. Cheapest:**
```python
policy = CheapestPolicy()
selected = policy.select(agents)
# Minimizes: cost (ignores quality)
```

**2. Fastest:**
```python
policy = FastestPolicy()
selected = policy.select(agents)
# Minimizes: queue_time + execution_time
```

**3. Best Reputation:**
```python
policy = BestReputationPolicy()
selected = policy.select(agents)
# Maximizes: reputation (ignores cost)
```

**Note:** The multi-objective scoring is applied **at the registry level** during semantic discovery. Client-side policies are available but less sophisticated.

---

## Cascading Delegation

### How Cascading Works (Current Implementation)

**Multi-Level Delegation with Synthesis Detection:**

The system implements **true multi-level cascading** where agents can recursively delegate based on policy decisions. Agents automatically detect when queries require synthesis or analysis beyond their capabilities and delegate to appropriate helpers:

```
User Request: "Compare Algeria and Morocco"
    ↓
[Chat UI] Receives request
    ↓
Policy Engine evaluates:
  - Can I handle this alone?  → No
  - Decision: SEMANTIC_DISCOVERY
    ↓
[Chat UI] Discovers agents semantically:
  - Queries registry for operation matches
  - Finds: Wikipedia (best match for "Algeria")
    ↓
[Chat UI] → [Wikipedia] delegates with receive_query
    ↓
[Wikipedia] Receives: "Compare Algeria and Morocco"
    ↓
[Wikipedia] Policy Engine evaluates:
  - operation: receive_query ✓
  - query_requires_synthesis?
    → Detects "compare" keyword → TRUE ✓
  - Rule matches: rule_00_delegate_synthesis_queries
  - Decision: SEMANTIC_DISCOVERY
    ↓
[Wikipedia] Discovers agents:
  - Finds: LLM Consultant (best for synthesis)
    ↓
[Wikipedia] → [LLM Consultant] delegates
    ↓
[LLM Consultant] Synthesizes comparison
    ↓
Results cascade back:
[LLM] → [Wikipedia] → [Chat UI] → User
```

**With Fallback Chains:**

If Wikipedia fails or returns empty, Chat UI tries next candidate:
```
[Chat UI] → [Wikipedia] (fails)
          → [Open Library] (next candidate)
          → [LLM Consultant] (final fallback)
```

**Key Features:**
- ✅ True multi-level delegation (3+ levels possible)
- ✅ Automatic synthesis detection via policy
- ✅ Each agent makes autonomous delegation decisions
- ✅ Fallback chains at every level
- ✅ Complete trace of all delegation levels

### Example: Wikipedia Agent

**Scenario:** User asks complex question about quantum computing

**Policy File:** `agents/wikipedia_agent/policy.json`

```json
{
  "rules": [
    {
      "rule_id": "rule_01",
      "priority": 10,
      "conditions": {
        "operation": ["get_article_summary", "search_wikipedia"],
        "complexity": "simple"
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "Simple Wikipedia lookups are my core capability"
      }
    },
    {
      "rule_id": "rule_02",
      "priority": 8,
      "conditions": {
        "complexity": "complex"
      },
      "action": {
        "type": "query_registry_for_planner",
        "reasoning": "Complex queries need planning and synthesis",
        "parameters": {
          "registry_query": {
            "operations": ["plan_workflow", "interpret_natural_language"]
          }
        }
      }
    }
  ]
}
```

**Actual Execution Flow:**

1. **Chat UI receives user query:**
   ```python
   message = "Who is the president of Algeria?"
   ```

2. **Policy Engine evaluates:**
   ```python
   decision = await self.policy_engine.decide(
       operation="receive_user_input",
       parameters={"message": message}
   )
   # decision.decision = DecisionType.SEMANTIC_DISCOVERY
   # decision.reasoning = "Query requires external knowledge source"
   ```

3. **Chat UI discovers agents semantically:**
   ```python
   operation_results = await self.discover_by_operation_query(
       query=message,
       top_k=5,
       min_score=0.03
   )
   # Finds operations: get_article_summary, search_wikipedia, etc.
   # Collects all agents offering these operations
   # Builds fallback chain ranked by: active status, reputation, similarity, cost
   ```

4. **Chat UI delegates with fallback chain:**
   ```python
   for candidate in all_candidates:
       try:
           result = await self.call_other_afdo(
               target_pid=candidate["pid"],  # e.g., Wikipedia
               operation=candidate["operation"],
               data={"query": message}
           )
           if has_useful_content(result):
               return result  # Success!
       except Exception:
           continue  # Try next candidate
   ```

5. **Selected agent (e.g., Wikipedia) processes query:**
   - Fetches article summary
   - Returns structured response
   - No further delegation

6. **Results return to Chat UI, then to user**

**Note:** This is **single-level delegation**. The current system does NOT use multi-step workflow generation. LLM Consultant's `generate_workflow` operation exists but is not called in production flow.

### Delegation Types (Policy Decisions)

The policy engine supports multiple decision types. Here's their implementation status:

**✅ Actively Used:**

**1. SEMANTIC_DISCOVERY:**
- Most common pattern in production
- Discovers agents by semantic operation matching
- Builds fallback chains with automatic retry
- Example: Chat UI discovering Wikipedia for knowledge queries

**2. HANDLE_ALONE:**
- Agent processes request without delegation
- Example: Chat UI handling capability queries

**3. QUERY_REGISTRY_FOR_HELPER:**
- Agent discovers specific capability it lacks
- Example: Paper Analyzer finding PDF Parser

**📋 Defined But Rarely Used:**

**4. QUERY_REGISTRY_FOR_PLANNER:**
- Theoretical: Complex tasks needing workflow planning
- Example (not implemented): Agent delegating to LLM Consultant for workflow generation

**5. QUERY_REGISTRY_FOR_COORDINATOR:**
- Theoretical: Multiple agents needing coordination
- Note: System uses direct P2P calling instead

**6. DELEGATE_FULLY:**
- Pure pass-through delegation
- Limited use in current agents

**7. COLLABORATE:**
- Multi-agent orchestration
- Conceptual, not actively used

---

## Reputation Tracking

### Dual-Path Reputation System

The system tracks reputation using **both objective metrics and subjective ratings**:

**Formula:**
```
reputation_score =
    (success_rate * 0.4) +
    (duration_accuracy * 0.2) +
    (average_caller_rating * 0.3) +
    (uptime * 0.1)
```

### Objective Metrics (Path 1)

**1. Success Rate:**
```python
success_rate = successful_operations / total_operations
```

**2. Duration Accuracy:**
```python
# How close was estimated duration to actual?
accuracy = min(actual_duration / estimated_duration,
               estimated_duration / actual_duration)
avg_duration_accuracy = mean(all_accuracies)
```

**3. Cost Accuracy:**
```python
# How close was estimated cost to actual?
cost_accuracy = min(actual_cost / estimated_cost,
                    estimated_cost / actual_cost)
```

**4. Uptime:**
```python
uptime = (total_time - downtime) / total_time
```

### Subjective Ratings (Path 2)

Callers can rate agents after operations:

```python
rating = CallerRating(
    caller_pid="21.T11148/caller",
    overall=4.5,        # 1.0-5.0
    speed=5.0,          # Optional
    quality=4.0,        # Optional
    value=4.5,          # Optional
    reliability=4.5,    # Optional
    comment="Fast and accurate"
)
```

**Average rating calculation:**
```python
# Convert 1-5 scale to 0-1 scale
avg_5_scale = mean(all_ratings)
normalized = (avg_5_scale - 1.0) / 4.0
```

### Reputation Grades

| Score | Grade | Description |
|-------|-------|-------------|
| 0.95+ | A+ | Exceptional |
| 0.90-0.94 | A | Excellent |
| 0.85-0.89 | A- | Very Good |
| 0.80-0.84 | B+ | Good |
| 0.75-0.79 | B | Above Average |
| 0.70-0.74 | B- | Average |
| 0.65-0.69 | C+ | Below Average |
| 0.60-0.64 | C | Fair |
| 0.50-0.59 | C- | Poor |
| < 0.50 | F | Failing |

### Reputation in Discovery

When agents are discovered, their reputation is included:

```json
{
  "pid": "21.T11148/afdo-pdf-parser",
  "reputation": 0.87,
  "reputation_grade": "A-",
  "total_operations": 142,
  "success_rate": 0.94
}
```

Selection policies use reputation:
- **Best Reputation Policy:** Select highest reputation
- **Balanced Policy:** Weight reputation at 30%
- **Value Policy:** Maximize reputation per dollar

---

## Policy Engine

### Architecture

The policy engine provides **separation of concerns**: behavior is defined in JSON (data), interpreted by Python (code).

```
┌─────────────────────────────────────────────────┐
│  Agent Code (Python)                            │
│  ┌────────────────────────────────────────┐    │
│  │ handle_operation_with_policy()          │    │
│  │   ↓                                     │    │
│  │ Policy Engine evaluates rules           │    │
│  │   ↓                                     │    │
│  │ Returns decision + reasoning            │    │
│  │   ↓                                     │    │
│  │ Execute decision                        │    │
│  └────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────┘
                        │ loads
                        ↓
              ┌──────────────────┐
              │  policy.json      │
              │  (DATA)           │
              │  ├─ rules[]       │
              │  ├─ conditions    │
              │  └─ actions       │
              └──────────────────┘
```

### Policy File Format

**Location:** `agents/<agent_name>/policy.json` or `shared/policies/default_<type>_policy.json`

**Structure:**
```json
{
  "policy_id": "wikipedia_policy",
  "policy_version": "1.0.0",
  "description": "Policy for Wikipedia Agent",
  "default_action": "handle_alone",

  "rules": [
    {
      "rule_id": "rule_01",
      "description": "Handle simple Wikipedia lookups alone",
      "priority": 10,

      "conditions": {
        "operation": ["get_article_summary", "search_wikipedia"],
        "has_capability": true,
        "complexity": "simple"
      },

      "action": {
        "type": "handle_alone",
        "reasoning": "Simple lookups are my core capability"
      }
    },
    {
      "rule_id": "rule_02",
      "priority": 8,

      "conditions": {
        "complexity": "complex"
      },

      "action": {
        "type": "query_registry_for_planner",
        "reasoning": "Complex queries need planning",
        "parameters": {
          "registry_query": {
            "operations": ["plan_workflow"],
            "selection_criteria": "balanced"
          }
        }
      }
    }
  ]
}
```

### Decision Types

1. **handle_alone:** Execute operation directly
2. **query_registry_for_helper:** Find specific helper
3. **query_registry_for_planner:** Find planning agent
4. **query_registry_for_coordinator:** Find coordinator
5. **delegate_fully:** Full delegation (interface agents)
6. **collaborate:** Multi-agent collaboration
7. **escalate:** Escalate to higher authority
8. **custom:** Agent-specific custom handling

### Condition Types

- **operation:** Match operation name(s)
- **has_capability:** Check if agent can perform operation
- **complexity:** simple, moderate, complex, very_complex
- **parameter_count:** Number of parameters with operator (>, <, ==, etc.)
- **budget_threshold:** Minimum budget required
- **custom:** Agent-specific conditions

### Rule Evaluation

**Priority-based matching:**
1. Rules sorted by priority (highest first)
2. First matching rule wins
3. If no match, use default_action
4. Decision includes reasoning for transparency

**Example evaluation:**
```python
# Context
operation = "search_wikipedia"
complexity = "complex"
has_capability = True

# Rule matching
for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
    if matches_conditions(rule, context):
        return rule.action  # First match wins
```

### Benefits

1. **Flexibility:** Update behavior without code changes
2. **Transparency:** Clear reasoning for every decision
3. **Reusability:** Share policies between agents
4. **Evolution:** Policies can improve over time
5. **Testing:** Easy to A/B test different strategies

### Synthesis Detection (Multi-Level Cascading)

The policy engine automatically detects queries requiring synthesis or analysis beyond simple data lookup:

**Condition:** `query_requires_synthesis`

**Detection Logic:**
```python
def _query_requires_synthesis(parameters: Dict[str, Any]) -> bool:
    """Detect if query requires synthesis/comparison/reasoning."""
    query = parameters.get("query") or parameters.get("message", "")
    query_lower = query.lower()

    synthesis_keywords = [
        "compare", "versus", "vs", "difference between",
        "analyze", "analysis", "evaluate", "assessment",
        "explain", "why", "how does", "what makes",
        "synthesize", "summarize", "relate",
        "implications", "impact", "effect",
        "pros and cons", "advantages", "disadvantages",
        "better", "worse", "best", "optimal"
    ]

    return any(keyword in query_lower for keyword in synthesis_keywords)
```

**Usage in Policy:**
```json
{
  "rule_id": "rule_00_delegate_synthesis_queries",
  "priority": 11,
  "conditions": {
    "operation": ["receive_query"],
    "query_requires_synthesis": true
  },
  "action": {
    "type": "semantic_discovery",
    "reasoning": "Query requires synthesis beyond simple lookup"
  }
}
```

**Example Flow:**
1. Wikipedia receives: "Compare Algeria and Morocco"
2. Policy engine evaluates conditions
3. Detects "compare" keyword → `query_requires_synthesis = true`
4. Rule matches → triggers SEMANTIC_DISCOVERY
5. Wikipedia discovers and delegates to LLM Consultant
6. Multi-level cascading achieved: Chat UI → Wikipedia → LLM

---

## Trace Aggregation

### Execution Trace System

Every request generates a **complete execution trace** capturing all agent interactions:

**Structure:**
```python
@dataclass
class TraceEvent:
    event_id: str
    step_number: int
    timestamp: str
    agent_name: str
    agent_pid: str
    action_type: str       # "receive", "delegate", "execute", "return"
    operation: str
    input_data: Dict
    output_data: Dict
    duration_ms: int
    cost: float
    error: Optional[str]
    delegated_to: Optional[str]
    policy_rule: Optional[str]
    policy_reasoning: Optional[str]
```

### Trace Example

**Request:** "Analyze this research paper"

**Trace Output:**
```
[Step 1] Chat UI - RECEIVE
  Operation: receive_user_input
  Time: 2026-02-13T10:30:00.000Z
  Input: {message: "Analyze this paper", pdf_data: "..."}
  Policy Rule: rule_03
  Policy Reasoning: "Delegate to Paper Analyzer for complex analysis"

[Step 2] Chat UI - DELEGATE
  Operation: analyze_paper_budget
  Delegated To: Paper Analyzer (21.T11148/afdo-paper-analyzer)
  Cost: $0.00 (coordination)

[Step 3] Paper Analyzer - RECEIVE
  Operation: analyze_paper_budget
  Time: 2026-02-13T10:30:00.150Z
  Budget: $1.00

[Step 4] Paper Analyzer - DELEGATE
  Operation: extract_text
  Delegated To: PDF Parser (21.T11148/afdo-pdf-parser)
  Policy Rule: rule_02
  Policy Reasoning: "Need to extract PDF text first"

[Step 5] PDF Parser - EXECUTE
  Operation: extract_text
  Duration: 2300ms
  Cost: $0.05
  Output: {text: "...", word_count: 5000}

[Step 6] Paper Analyzer - EXECUTE
  Operation: analyze_content (built-in LLM)
  Duration: 8500ms
  Cost: $0.15 (included in coordination)

[Step 7] Paper Analyzer - DELEGATE
  Operation: assess_fairness
  Delegated To: FAIR Assessor (21.T11148/afdo-fair-assessor)

[Step 8] FAIR Assessor - EXECUTE
  Operation: assess_fairness
  Duration: 1200ms
  Cost: $0.02
  Output: {overall_score: 0.75, ...}

[Step 9] Paper Analyzer - RETURN
  Cost Total: $0.22
  Status: success

[Step 10] Chat UI - RETURN
  Total Duration: 12,500ms
  Total Cost: $0.22
  Agents Involved: Chat UI, Paper Analyzer, PDF Parser, FAIR Assessor
```

### Trace Storage

**Location:** `/tmp/afdo_traces/`

**Format:** JSON

**Example file:** `req_abc12345_20260213_103000.json`

```json
{
  "summary": {
    "request_id": "req_abc12345",
    "user_query": "Analyze this research paper",
    "start_time": "2026-02-13T10:30:00.000Z",
    "end_time": "2026-02-13T10:30:12.500Z",
    "total_duration_ms": 12500,
    "total_steps": 10,
    "agents_involved": ["Chat UI", "Paper Analyzer", "PDF Parser", "FAIR Assessor"],
    "total_cost": 0.22,
    "status": "success"
  },
  "events": [
    {
      "event_id": "req_abc12345_step_1",
      "step_number": 1,
      "timestamp": "2026-02-13T10:30:00.000Z",
      "agent_name": "Chat UI",
      "agent_pid": "21.T11148/afdo-chat-ui",
      "action_type": "receive",
      "operation": "receive_user_input",
      "input_data": {"message": "Analyze this paper"},
      "policy_rule": "rule_03",
      "policy_reasoning": "Delegate to Paper Analyzer"
    },
    ...
  ]
}
```

### Using Traces

**View trace in UI:**
```
http://localhost:8001/ui
→ Execute query
→ Click "View Trace" button
```

**Programmatic access:**
```python
tracer = ExecutionTracer(request_id="req_123", user_query="...")

# Log events
tracer.log_event(
    agent_name="PDF Parser",
    agent_pid="21.T11148/afdo-pdf-parser",
    action_type="execute",
    operation="extract_text",
    duration_ms=2300,
    cost=0.05
)

# Get summary
summary = tracer.get_summary()

# Save to file
filepath = tracer.save_to_file()

# Format readable
readable = tracer.format_readable()
print(readable)
```

---

## How to Add a New aFDO

### Requirements Checklist

Before creating a new aFDO, ensure you understand these requirements:

**✅ MANDATORY Requirements:**

1. **Inherit from aFDOBase** - All agents must extend `shared.afdo_base.aFDOBase`
2. **Implement handle_operation()** - Abstract method, must handle all declared operations
3. **Implement get_self_description()** - Abstract method, returns capability metadata
4. **Unique port number** - Must not conflict with existing agents (check ports 8000-8014)
5. **Valid FDO type** - Must use existing type or create new one (21.T11148/type-*-v1)
6. **Operation list** - Must declare all operations in `__init__` operations parameter
7. **Policy file** - Create `agents/<name>/policy.json` or use default policy
8. **Proper shutdown** - Must handle SIGTERM/SIGINT gracefully (inherited from aFDOBase)

**✅ STRONGLY RECOMMENDED:**

1. **Input validation** - Validate all parameters in handle_operation()
2. **Error handling** - Raise clear ValueError for user errors, RuntimeError for system errors
3. **Cost estimation** - Set realistic `cost` parameter in `__init__`
4. **Metadata content** - Implement get_metadata_content() with version, description
5. **Operation schemas** - Define input_schema and output_schema in get_self_description()
6. **Logging** - Use `self.logger` for all log messages
7. **Testing** - Create unit tests in tests/ directory
8. **Documentation** - Add agent to AGENTS.md with examples

**📋 OPTIONAL Enhancements:**

1. **Built-in LLM** - Set `has_llm=True` and initialize OpenAI client if needed
2. **Specialization** - Set `specialization` parameter for better discovery
3. **Custom policy engine** - Override policy behavior if default insufficient
4. **Budget awareness** - Use BudgetManager for multi-step workflows
5. **Execution tracing** - Use self.tracer for detailed logging
6. **Reputation tracking** - Automatic, but can customize via reputation_manager
7. **Queue management** - Automatic via QueueManager
8. **Dependencies** - Create requirements.txt for agent-specific packages

**⚠️ COMMON PITFALLS TO AVOID:**

1. ❌ **Hardcoding agent references** - Use semantic discovery, not direct PID references
2. ❌ **Forgetting async/await** - All operation handlers must be async
3. ❌ **Port conflicts** - Check with `lsof -i :PORT` before choosing
4. ❌ **Missing input validation** - Always validate before processing
5. ❌ **Blocking operations** - Use asyncio for I/O, avoid time.sleep()
6. ❌ **Not handling errors** - Always return structured error responses
7. ❌ **Skipping policy file** - Creates unpredictable delegation behavior
8. ❌ **Ignoring logging** - Makes debugging nearly impossible

---

### Step-by-Step Guide

#### Step 1: Choose Agent Type

Determine your agent's category:
- **Task Agent:** Single operation, no delegation
- **Composite Agent:** Multi-step workflow, delegates to others
- **Interface Agent:** User-facing, routes requests
- **Data Source Agent:** External API integration

#### Step 2: Create Agent Directory

```bash
mkdir -p agents/my_new_agent
cd agents/my_new_agent
```

#### Step 3: Create Agent Class

**File:** `my_new_agent_agent.py`

```python
"""My New Agent - Description"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
from shared.afdo_base import aFDOBase


class MyNewAgentAgent(aFDOBase):
    """My New Agent aFDO."""

    def __init__(self):
        super().__init__(
            name="My New Agent",
            fdo_type="21.T11148/type-YOUR-TYPE-v1",
            operations=[
                "operation_1",
                "operation_2"
            ],
            port=8015,  # Choose available port
            cost=0.10,  # Base cost per operation
            has_llm=False,  # Set True if agent has built-in LLM
            specialization="domain"  # Optional
        )

    def get_metadata_content(self) -> Dict[str, Any]:
        """Provide agent-specific metadata."""
        return {
            "description": "Brief description",
            "version": "1.0.0",
            "agent_role": "task_agent",
            "capabilities": {
                "operation_1": {
                    "description": "What this does",
                    "estimated_duration": "1-5s",
                    "estimated_cost": "$0.10"
                }
            }
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Return structured self-description."""
        return {
            "agent_info": {
                "name": "My New Agent",
                "version": "1.0.0",
                "agent_type": "task",
                "description": "Detailed description"
            },
            "capabilities": {
                "operation_1": {
                    "operation_type": "data_extraction",
                    "input_schema": {
                        "type": "object",
                        "required": ["param1"],
                        "properties": {
                            "param1": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["result"],
                        "properties": {
                            "result": {"type": "string"}
                        }
                    }
                }
            },
            "technical_spec": {
                "runtime": "Python 3.10",
                "dependencies": [],
                "resource_requirements": {
                    "memory_mb": 256,
                    "cpu_cores": 0.5
                }
            },
            "agent_attributes": {
                "has_llm": False,
                "autonomy_level": "task",
                "can_delegate": False
            }
        }

    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle operations."""
        if operation == "operation_1":
            return await self._operation_1(parameters)
        elif operation == "operation_2":
            return await self._operation_2(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _operation_1(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implement operation 1."""
        param1 = parameters.get("param1")
        if not param1:
            raise ValueError("Missing 'param1'")

        # Do the work
        result = f"Processed: {param1}"

        return {
            "result": result,
            "processor": self.pid
        }

    async def _operation_2(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implement operation 2."""
        # Implementation
        pass


if __name__ == "__main__":
    agent = MyNewAgentAgent()
    agent.run()
```

#### Step 4: Create Policy File

**File:** `policy.json`

```json
{
  "policy_id": "my_new_agent_policy",
  "policy_version": "1.0.0",
  "description": "Policy for My New Agent",
  "default_action": "handle_alone",

  "rules": [
    {
      "rule_id": "rule_01",
      "priority": 10,
      "conditions": {
        "operation": ["operation_1", "operation_2"],
        "has_capability": true
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "Core capabilities"
      }
    },
    {
      "rule_id": "rule_02",
      "priority": 5,
      "conditions": {
        "has_capability": false
      },
      "action": {
        "type": "query_registry_for_helper",
        "reasoning": "Need helper for unknown operations",
        "parameters": {
          "registry_query": {
            "selection_criteria": "balanced"
          }
        }
      }
    }
  ]
}
```

#### Step 5: Add to Startup Script

**File:** `start_system.sh`

Add after existing agents:

```bash
echo ""
echo "Starting my new agent (port 8015)..."
start_agent "my-new-agent" "agents/my_new_agent/my_new_agent_agent.py" "8015" || FAILED=$((FAILED+1))
```

#### Step 6: Test Agent

```bash
# Test standalone
python3 agents/my_new_agent/my_new_agent_agent.py

# Check registration
curl http://localhost:8000/doip/search/fdos | grep "My New Agent"

# Test operation
curl -X POST http://localhost:8015/doip/call \
  -H "Content-Type: application/json" \
  -d '{
    "target_pid": "21.T11148/afdo-my-new-agent",
    "operation": "operation_1",
    "caller_pid": "test",
    "parameters": {"param1": "test"}
  }'
```

#### Step 7: Add to System

```bash
# Stop system
./stop_system.sh

# Start with new agent
./start_system.sh

# Verify
./check_status.sh
```

### Common Patterns

**Task Agent Pattern:**
- No LLM
- No delegation
- Deterministic operations
- Simple policy (handle capable, delegate incapable)

**Composite Agent Pattern:**
- Has LLM for planning
- Delegates to helpers
- Complex policy with multiple rules
- Budget management

**Data Source Agent Pattern:**
- Connects to external API
- No LLM
- Policy delegates complex tasks to planners
- Error handling for API failures

---

## Fallback Chains

### How Fallback Works

When an agent call fails, the system automatically tries alternative providers:

```
Primary Agent Call
    ↓
  [FAILS]
    ↓
Discover Alternatives
    ↓
Try Second Agent
    ↓
  [FAILS]
    ↓
Try Third Agent
    ↓
[SUCCESS]
```

### Implementation

**In aFDOBase:**

```python
async def call_with_alternatives(
    self,
    operation: str,
    parameters: Dict,
    budget: BudgetManager,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Call operation with automatic failover.

    Args:
        operation: Operation to call
        parameters: Operation parameters
        budget: Budget manager
        max_retries: Maximum retry attempts

    Returns:
        Operation result

    Raises:
        ValueError: If all alternatives fail
    """

    # Discover all agents offering operation
    agents = await self.discover_by_operation(operation)

    if not agents:
        raise ValueError(f"No agents found for operation: {operation}")

    # Apply selection policy
    ranked_agents = self.selection_policy.select_multiple(agents)

    # Try each agent in order
    last_error = None
    for agent in ranked_agents[:max_retries + 1]:
        try:
            # Reserve budget
            reservation = budget.reserve(
                amount=agent["cost"],
                item=operation,
                provider_pid=agent["pid"]
            )

            # Call agent
            result = await self.call_other_afdo(
                target_pid=agent["pid"],
                operation=operation,
                data=parameters
            )

            # Commit budget
            budget.commit(reservation, agent["cost"])

            return result

        except Exception as e:
            last_error = e
            # Release budget reservation
            budget.release(reservation)
            # Log failure
            self.logger.warning(
                f"Failed to call {agent['pid']} for {operation}: {e}"
            )
            continue

    # All alternatives failed
    raise ValueError(
        f"All alternatives failed for {operation}: {last_error}"
    )
```

### Validation in Fallback Chains

Each agent in the chain validates its input:

```python
async def handle_operation(self, operation, caller_pid, parameters):
    # Validate input
    if operation == "extract_text":
        if "pdf_data" not in parameters:
            raise ValueError("Missing required parameter: pdf_data")

        if not isinstance(parameters["pdf_data"], str):
            raise ValueError("pdf_data must be base64 string")

    # Execute
    result = await self._extract_text(parameters)

    # Validate output
    if "text" not in result:
        raise ValueError("Output missing required field: text")

    return result
```

### Benefits

1. **Fault Tolerance:** System continues if one agent fails
2. **Load Balancing:** Distributes load across multiple providers
3. **Quality Assurance:** Validation at each step
4. **Cost Optimization:** Tries cheaper alternatives first
5. **Transparency:** Complete trace of attempts

---

## Data Flow Examples

### Example 1: Simple Paper Analysis

**User Request:** Analyze paper.pdf

```
[1] User → Chat UI
    POST /doip/call
    operation: receive_user_input
    parameters: {message: "Analyze", pdf_data: "..."}

[2] Chat UI → Policy Engine
    Evaluates: operation="receive_user_input", complexity="complex"
    Decision: delegate to Paper Analyzer

[3] Chat UI → Paper Analyzer
    POST /doip/call
    operation: analyze_paper_budget
    parameters: {pdf_data: "...", budget: 1.0}

[4] Paper Analyzer → Registry
    GET /market/agents/by_operation/extract_text
    Returns: [PDF Parser (0.05, 0.87)]

[5] Paper Analyzer → PDF Parser
    POST /doip/call
    operation: extract_text
    Result: {text: "...", char_count: 5000}
    Cost: $0.05

[6] Paper Analyzer → Built-in LLM
    Analyzes extracted text
    Cost: $0.15 (included in coordination)

[7] Paper Analyzer → Registry
    GET /market/agents/by_operation/assess_fairness
    Returns: [FAIR Assessor (0.02, 0.90)]

[8] Paper Analyzer → FAIR Assessor
    POST /doip/call
    operation: assess_fairness
    Result: {overall_score: 0.75, ...}
    Cost: $0.02

[9] Paper Analyzer → Chat UI
    Returns: {
      analysis: {...},
      fair_assessment: {...},
      cost_breakdown: {
        total: $0.22,
        services: [
          {name: "PDF Parser", cost: 0.05},
          {name: "Paper Analyzer", cost: 0.15},
          {name: "FAIR Assessor", cost: 0.02}
        ]
      }
    }

[10] Chat UI → User
    Displays results with cost breakdown
```

### Example 2: Complex Query with Cascading Delegation

**User Request:** "Explain quantum computing applications"

```
[1] User → Chat UI
    message: "Explain quantum computing applications"

[2] Chat UI → Wikipedia Agent (discovered)
    operation: get_article_summary
    topic: "quantum computing applications"

[3] Wikipedia Agent → Policy Engine
    Evaluates: complexity="complex"
    Decision: query_registry_for_planner

[4] Wikipedia Agent → Registry
    GET /market/agents/by_operation/generate_workflow
    Returns: [LLM Consultant (0.10, 0.92)]

[5] Wikipedia Agent → LLM Consultant
    operation: generate_workflow
    task: "Explain quantum computing applications"
    requester_capabilities: ["get_article_summary", "search_wikipedia"]

[6] LLM Consultant (generates workflow)
    Step 1: Search Wikipedia "quantum computing"
    Step 2: Search ArXiv for recent papers
    Step 3: Search Wikipedia "cryptography applications"
    Step 4: Synthesize comprehensive response

[7] LLM Consultant → Wikipedia Agent
    operation: search_wikipedia
    query: "quantum computing"

[8] LLM Consultant → ArXiv Agent
    operation: search_papers
    query: "quantum computing applications"

[9] LLM Consultant → Wikipedia Agent
    operation: search_wikipedia
    query: "quantum cryptography"

[10] LLM Consultant → Built-in LLM
    Synthesizes all results

[11] LLM Consultant → Wikipedia Agent
    Returns: comprehensive explanation

[12] Wikipedia Agent → Chat UI
    Returns: result with full trace

[13] Chat UI → User
    Displays: explanation + trace + cost
```

---

## FDO Compliance

### FDO Record Structure

**Standard:** Based on FDO specification v2.0

```python
class FDORecord(BaseModel):
    pid: str                        # Persistent Identifier
    fdo_type_pid: str              # Type reference
    fdo_profile_pid: str           # Profile reference
    metadata_pointer: str          # Metadata record PID
    operation_pids: List[str]      # Operations offered
    kernel_attributes: Dict        # Runtime info
    self_description: Dict         # Capability description
    status: str                    # active/inactive
    last_heartbeat: float         # Timestamp
    created_at: str               # ISO timestamp
    updated_at: str               # ISO timestamp
```

### PID Schema

**Format:** `21.T11148/{suffix}`

**Examples:**
- Agent: `21.T11148/afdo-pdf-parser`
- Metadata: `21.T11148/metadata-pdf-parser`
- Operation: `21.T11148/op-extract-text`
- Type: `21.T11148/type-document-processor-v1`

### Type System

**Implemented Types:**

1. **type-document-processor-v1**
   - Document processing agents
   - Expected: extract_text, extract_metadata

2. **type-quality-assessor-v1**
   - Quality assessment agents
   - Expected: assess_fairness, score_metadata

3. **type-workflow-coordinator-v1**
   - Workflow orchestration agents
   - Expected: analyze_paper, plan_workflow

4. **type-user-interface-v1**
   - User-facing interface agents
   - Expected: receive_user_input, display_message

5. **type-agent-creator-v1**
   - Agent creation meta-agents
   - Expected: create_afdo, fork_afdo

6. **type-llm-service-v1**
   - LLM service agents
   - Expected: generate_text, summarize

7. **type-data-source-v1**
   - External data source agents
   - Expected: search, get_data

### DOIP Protocol

**Implemented Operations:**

- `0.DOIP/Op.Create` → `POST /doip/create/{type}`
- `0.DOIP/Op.Read` → `GET /doip/read/{type}/{pid}`
- `0.DOIP/Op.Update` → `PATCH /registry/fdos/{pid}/field/{field}`
- `0.DOIP/Op.Delete` → `DELETE /doip/delete/{type}/{pid}`
- `0.DOIP/Op.Search` → `GET/POST /doip/search/{type}`

**Note:** Implementation uses HTTP/REST rather than binary DOIP v2.0 protocol.

---

## Summary

The aFDO system provides a comprehensive multi-agent architecture with:

- **Semantic Discovery:** Operation-based service location
- **Cascading Delegation:** Policy-driven autonomous behavior
- **Reputation Tracking:** Dual-path quality metrics
- **Trace Aggregation:** Complete provenance capture
- **Budget Management:** Cost-aware workflow execution
- **Fault Tolerance:** Automatic failover with validation
- **Extensibility:** Easy to add new agents
- **Transparency:** Full execution traces and reasoning

This architecture enables truly autonomous agents that can discover, collaborate, and adapt dynamically while maintaining transparency and quality assurance.

---

**Document Version:** 2.0.0
**Last Verified:** 2026-02-15
**Maintainer:** aFDO Architecture Team
