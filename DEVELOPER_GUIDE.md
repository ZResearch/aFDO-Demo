# aFDO System - Developer Guide

**Version:** 2.1.0
**Last Updated:** 2026-02-16
**Status:** For developers extending or modifying the system

---

## Implementation Status for Developers

When developing new agents or extending the system, be aware that some documented patterns are **aspirational** rather than production-ready:

**✅ Use These Patterns (Production-Ready):**
- Semantic discovery via `discover_by_operation_query()`
- **Multi-level delegation** via policy-driven SEMANTIC_DISCOVERY
- Delegation with `call_other_afdo()` (single or multi-level)
- Policy-driven decisions with `policy_engine.decide()`
- **Synthesis detection** with `query_requires_synthesis` condition
- Fallback chains with automatic retry
- Direct P2P calling between agents
- Execution trace logging

**📋 Available But Not Used (Aspirational):**
- Workflow generation via LLM Consultant (implemented, not called)
- WorkflowEngine for multi-step execution (coded, never instantiated)
- Negotiation protocol for pricing (complete, agents use direct calls)
- Multi-level recursive delegation (supported, not used)

**Developer Recommendation:** Follow the patterns in Chat UI, Wikipedia, and Paper Analyzer agents as reference implementations of production patterns.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Base Agent Framework](#base-agent-framework)
4. [Registry API Contract](#registry-api-contract) ⚠️ **CRITICAL**
5. [Creating New Agents](#creating-new-agents)
6. [Policy Configuration](#policy-configuration)
7. [Testing Procedures](#testing-procedures)
8. [Development Workflow](#development-workflow)
9. [Helper Scripts](#helper-scripts)
10. [Debugging](#debugging)
11. [Best Practices](#best-practices)
12. [Advanced Topics](#advanced-topics)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip and virtualenv
- Git (optional, for version control)
- IDE with Python support (VS Code, PyCharm recommended)
- OpenAI API key (for LLM-powered agents)

### Environment Setup

```bash
# 1. Navigate to project
cd IJCAI_DEMO

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# Or: venv\Scripts\activate  # On Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# 6. Set up API key
echo "OPENAI_API_KEY='your-key'" > .env

# 7. Verify setup
python3 -c "import fastapi, openai; print('✓ Setup complete')"
```

### IDE Configuration

**VS Code:**

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

**PyCharm:**
- File → Settings → Project → Python Interpreter
- Select the `venv/bin/python` interpreter
- Enable pytest as test runner

---

## Project Structure

### Directory Layout

```
IJCAI_DEMO/
├── agents/                         # All agent implementations
│   ├── __init__.py
│   ├── example_agent.py           # Template for new agents
│   │
│   ├── chat_ui/                   # Web interface agent
│   │   ├── chat_ui_agent.py
│   │   ├── static/                # HTML/CSS/JS
│   │   └── policy.json
│   │
│   ├── creator/                   # Agent creation meta-agent
│   │   ├── creator_agent.py
│   │   └── afdo_templates.py
│   │
│   ├── fair_assessor/             # FAIR compliance checker
│   │   ├── fair_assessor_agent.py
│   │   ├── fair_criteria.py
│   │   └── policy.json
│   │
│   ├── llm_endpoint_gpt4/         # GPT-4 service
│   │   ├── llm_endpoint_agent.py
│   │   └── requirements.txt
│   │
│   ├── llm_endpoint_gpt4_mini/    # GPT-4-mini service
│   │   └── llm_endpoint_agent.py
│   │
│   ├── llm_consultant/            # Workflow generator
│   │   └── llm_consultant_agent.py
│   │
│   ├── nl_handler_scientific/     # NL query processor
│   │   ├── nl_handler_agent.py
│   │   └── workflow_planner.py
│   │
│   ├── paper_analyzer/            # Composite analysis agent
│   │   ├── paper_analyzer_agent.py
│   │   ├── analysis_templates.py
│   │   └── policy.json
│   │
│   ├── pdf_parser/                # PDF processing
│   │   ├── pdf_parser_agent.py
│   │   ├── pdf_utils.py
│   │   ├── policy.json
│   │   └── requirements.txt
│   │
│   ├── wikipedia_agent/           # Wikipedia data source
│   │   ├── wikipedia_agent.py
│   │   └── policy.json
│   │
│   ├── arxiv_agent/               # ArXiv data source
│   │   ├── arxiv_agent.py
│   │   └── policy.json
│   │
│   └── openlibrary_agent/         # Open Library data source
│       ├── openlibrary_agent.py
│       └── policy.json
│
├── registry/                       # Central registry
│   ├── main.py                    # FastAPI registry server
│   ├── file_storage.py            # JSON storage backend
│   ├── models.py                  # Pydantic models
│   ├── event_broadcaster.py       # WebSocket events
│   ├── data/                      # Storage directory
│   │   ├── fdos/                  # FDO records
│   │   ├── metadata/              # Metadata records
│   │   ├── types/                 # Type definitions
│   │   ├── profiles/              # Profile definitions
│   │   └── operations/            # Operation registry
│   └── static/                    # Web dashboard
│
├── shared/                         # Shared infrastructure
│   ├── __init__.py
│   ├── afdo_base.py               # Base class (119KB, 3000+ lines)
│   ├── budget_manager.py          # Budget tracking
│   ├── doip_client.py             # Registry client
│   ├── execution_trace.py         # Execution tracing
│   ├── fdo_schemas.py             # FDO validation
│   ├── logging_config.py          # Centralized logging
│   ├── negotiation.py             # Quote/negotiation
│   ├── operation_types.py         # Operation enums
│   ├── policy_engine.py           # Policy interpreter
│   ├── queue_manager.py           # Request queuing
│   ├── reputation_manager.py      # Reputation tracking
│   ├── selection_policy.py        # Agent selection
│   ├── type_schemas.py            # Type schemas
│   ├── utils.py                   # Utilities
│   │
│   ├── policies/                  # Default policies
│   │   ├── default_task_policy.json
│   │   ├── default_composite_policy.json
│   │   └── default_interface_policy.json
│   │
│   └── protocols/                 # Protocol implementations
│       ├── __init__.py
│       ├── negotiation.py
│       ├── workflow.py
│       ├── negotiation_protocol.json
│       └── workflow_protocol.json
│
├── scripts/                        # Helper scripts
│   ├── __initialize_types.py      # Initialize type system
│   └── verify_agent_registration.py
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_policy_engine.py
│   ├── test_external_agents.py
│   └── test_dynamic_workflows.py
│
├── workflows/                      # Workflow examples
│   └── examples/
│       └── README.md
│
├── logs/                           # Log files (runtime)
│
├── requirements.txt                # Python dependencies
├── README.md                       # Project overview
├── ARCHITECTURE.md                 # Technical architecture
├── DEVELOPER_GUIDE.md              # This file
│
├── start_system.sh                 # System startup
├── stop_system.sh                  # System shutdown
└── check_status.sh                 # Status checker
```

### Key Files by Importance

**Most Critical (Understand These First):**
1. `shared/afdo_base.py` - Base class all agents inherit
2. `registry/main.py` - Registry API and marketplace
3. `shared/policy_engine.py` - Policy interpretation
4. `agents/example_agent.py` - Template for new agents

**Core Infrastructure:**
5. `shared/budget_manager.py` - Budget tracking
6. `shared/reputation_manager.py` - Reputation system
7. `shared/selection_policy.py` - Agent selection
8. `shared/execution_trace.py` - Execution tracing

**Agent Examples:**
9. `agents/pdf_parser/pdf_parser_agent.py` - Simple task agent
10. `agents/paper_analyzer/paper_analyzer_agent.py` - Complex composite agent
11. `agents/chat_ui/chat_ui_agent.py` - Interface agent

---

## Base Agent Framework

### aFDOBase Class

**Location:** `shared/afdo_base.py` (119KB, 3000+ lines)

All agents inherit from `aFDOBase`, which provides comprehensive infrastructure:

#### Core Features

**1. Auto-Registration**
```python
async def register_self(self) -> bool:
    """Register with registry on startup."""
    # Creates FDO record
    # Creates metadata record
    # Registers operations
    # Starts heartbeat task
```

**2. Discovery Methods**
```python
async def discover_by_operation(self, operation: str) -> List[Dict]:
    """Find agents offering specific operation."""

async def discover_by_type(self, fdo_type: str) -> List[Dict]:
    """Find agents of specific type."""
```

**3. Communication Methods**
```python
async def call_other_afdo(
    self,
    target_pid: str,
    operation: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Direct P2P call to another agent."""

async def call_with_alternatives(
    self,
    operation: str,
    parameters: Dict,
    budget: BudgetManager,
    max_retries: int = 2
) -> Dict[str, Any]:
    """Call with automatic failover."""
```

**4. Policy Integration**
```python
def _load_policy_engine(self):
    """Automatically load policy file."""
    # Checks agents/<name>/policy.json
    # Falls back to default policy

async def handle_operation_with_policy(
    self,
    operation: str,
    caller_pid: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Route operation through policy engine."""
```

**5. Budget Management**
```python
# Budget manager automatically available
self.budget_manager = BudgetManager(total_budget=1.0)

# Reserve, commit, release pattern
reservation = self.budget_manager.reserve(amount, item, provider_pid)
self.budget_manager.commit(reservation, actual_cost)
self.budget_manager.release(reservation)
```

**6. Activity Logging**
```python
# Automatic logging of all operations
self.logger.info(f"Processing {operation}")

# Centralized log: logs/afdo_YYYY-MM-DD.log
# Agent-specific log: logs/<agent-name>.log
```

**7. Execution Tracing**
```python
# Automatic trace generation
self.tracer = ExecutionTracer(request_id, user_query)
self.tracer.log_event(
    agent_name=self.name,
    action_type="execute",
    operation=operation,
    duration_ms=duration,
    cost=cost
)
```

### Abstract Methods (Must Implement)

Every agent must implement:

```python
@abstractmethod
async def handle_operation(
    self,
    operation: str,
    caller_pid: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle operation requests."""
    pass

@abstractmethod
def get_self_description(self) -> Dict[str, Any]:
    """Return structured capability description."""
    pass
```

### Optional Methods (Override as Needed)

```python
def get_metadata_content(self) -> Dict[str, Any]:
    """Provide agent-specific metadata."""
    return {}

def _infer_agent_type(self) -> str:
    """Infer agent category from FDO type."""
    # Automatically called, can override
```

---

## Registry API Contract

### ⚠️ CRITICAL: Semantic Discovery Response Format

**Problem:** Schema mismatch between agent code expectations and registry responses causes silent failures where agents cannot find operations even when they exist.

**Registry Discovery Endpoint:**
```
POST {registry_url}/doip/discover/by_operation_query
Request: {"query": "capability description", "top_k": 5, "min_score": 0.0}
```

**Registry Returns (Agent-Based Format):**
```json
{
  "status": "success",
  "data": [
    {
      "agent_pid": "21.T11148/afdo-fact-checker-agent",
      "agent_name": "Fact Checker Agent",
      "best_operation": "verify_fact",          ← NOT "operation"
      "operation_description": "Verify if...",
      "semantic_similarity": 0.712,             ← NOT "similarity_score"
      "agent_score": 0.520,
      "combined_score": 0.477,
      "num_matching_operations": 3,
      "cost": 0.05,
      "status": "active"
    }
  ]
}
```

### Correct Field Names (ALWAYS USE THESE)

| Purpose | ❌ WRONG (Old) | ✅ CORRECT (Current) | Notes |
|---------|---------------|---------------------|-------|
| Agent identifier | N/A | `agent_pid` | Required for calling |
| Agent name | N/A | `agent_name` | For logging |
| Operation to call | `operation` | `best_operation` | **Critical for routing** |
| Similarity score | `similarity_score` | `semantic_similarity` | For scoring |
| Provider list | `providers` | N/A | Not returned (use `agent_pid`) |

### Code Pattern (ALWAYS USE THIS)

```python
# ✅ CORRECT: Use registry response format
discovery_results = await self.discover_by_operation_query(query, top_k=5)

for result in discovery_results:
    # Get agent info
    agent_pid = result['agent_pid']                    # ✅ Always present
    agent_name = result.get('agent_name', agent_pid)   # ✅ Always present

    # Get operation to call - WITH FALLBACK for compatibility
    # CRITICAL: Use 'or' not nested .get() to handle None values!
    # .get() returns None if value IS None (only uses default if key missing)
    operation = result.get('best_operation') or \      # ✅ Current format
                result.get('operation') or \           # Fallback for old format
                'receive_query'                        # Final fallback

    # Get score - WITH FALLBACK for compatibility
    score = result.get('semantic_similarity') or \     # ✅ Current format
            result.get('similarity_score') or \        # Fallback for old format
            0.0                                         # Default

    # Call the agent
    await self.call_other_afdo(
        target_pid=agent_pid,
        operation=operation,  # Use the best_operation from registry
        data=parameters
    )
```

### ❌ Common Mistakes (DO NOT DO THIS)

```python
# ❌ WRONG: Hardcoding 'receive_query' without checking registry
operation = 'receive_query'  # Ignores what agent actually provides!

# ❌ WRONG: Using old field names without fallback
operation = result['operation']  # KeyError! Field doesn't exist!
score = result['similarity_score']  # KeyError! Field doesn't exist!

# ❌ WRONG: Assuming 'providers' field exists
for provider in result['providers']:  # KeyError! Field doesn't exist!
    pass

# ❌ WRONG: Using nested .get() - DOESN'T handle None values!
operation = result.get('best_operation', result.get('operation', 'receive_query'))
# Problem: If best_operation EXISTS but is None, returns None (not fallback)!
# .get(key, default) only uses default when KEY doesn't exist, not when VALUE is None

# Python gotcha demonstration:
d = {'key': None}
d.get('key', 'default')  # Returns None, NOT 'default'!
```

### ⚠️ Python Gotcha: .get() vs 'or' Chain

**The Problem:**
```python
# Registry might return: {"best_operation": None}
result.get('best_operation', 'fallback')  # Returns None, NOT 'fallback'!
```

**Why:** `.get(key, default)` only uses the default when the KEY doesn't exist. If the key exists but the VALUE is `None`, it returns `None`.

**The Solution:**
```python
# ✅ Use 'or' chain to handle None values
operation = result.get('best_operation') or 'fallback'

# ✅ Or with multiple fallbacks
operation = result.get('best_operation') or result.get('operation') or 'receive_query'
```

**Real Impact:** This caused "Operation 'None' not supported" errors when Chat UI Agent matched but had no good operation (registry returned `best_operation: None`).

### Testing Your Code

**Always test semantic discovery with real registry:**

```python
# Test that your code handles registry response correctly
results = await self.discover_by_operation_query(
    "verify factual claims",
    top_k=3
)

# Print what registry returns (for debugging)
print(f"Registry returned: {results[0].keys()}")

# Verify you're getting the right operation
assert 'best_operation' in results[0], "Registry format mismatch!"
assert 'agent_pid' in results[0], "Missing agent identifier!"
```

### Why This Matters

**Real incident (2026-02-16):**
- Fact Checker agent had excellent descriptions with keywords: "verify", "fact-check", "validate"
- Registry correctly returned Fact Checker with **0.712 similarity score** (very high!)
- But code expected `result['operation']` which didn't exist
- Defaulted to `'receive_query'`
- Called wrong operation on wrong agent → System failure
- User queries failed even though correct agent was available

**Impact:** Hours of debugging because schema mismatch made it appear like operations weren't registered, when they were perfectly registered but code couldn't read the response correctly.

### Registry Response Changelog

- **Before 2026-02:** Operation-based format with `operation` and `providers` fields
- **Current (2026-02+):** Agent-based format with `best_operation` and `agent_pid` fields
- **Compatibility:** Code must handle BOTH formats with fallbacks (see correct pattern above)

---

## Creating New Agents

### Prerequisites and Requirements

**Before you start, check these requirements:**

#### MANDATORY Components

| Component | Description | Location | Failure Impact |
|-----------|-------------|----------|----------------|
| **aFDOBase inheritance** | Your agent class must extend aFDOBase | `from shared.afdo_base import aFDOBase` | Won't run |
| **handle_operation()** | Async method to handle all operations | Abstract method | Won't run |
| **get_self_description()** | Returns capability metadata | Abstract method | Won't register |
| **Unique port** | Port not used by other agents | `__init__(port=XXXX)` | Port conflict |
| **FDO type** | Valid type PID | `fdo_type="21.T11148/type-*-v1"` | Registry error |
| **Operations list** | All operations your agent offers | `operations=["op1", "op2"]` | Won't discover |
| **Policy file** | Decision rules for delegation | `agents/<name>/policy.json` | Unpredictable |

#### RECOMMENDED Components

| Component | Why Important | How to Add |
|-----------|---------------|------------|
| **Input validation** | Prevents crashes, clear errors | Validate in handle_operation() |
| **Error handling** | Graceful failure, debugging | try/except with specific errors |
| **Cost estimation** | Budget tracking, selection | `cost=0.XX` in __init__ |
| **Metadata** | Better discovery, documentation | Implement get_metadata_content() |
| **Schemas** | Input/output validation, docs | Define in get_self_description() |
| **Logging** | Debugging, monitoring | Use self.logger.info/error |
| **Unit tests** | Confidence, regression prevention | tests/test_<agent>.py |

#### Available Ports

Check which ports are free:
```bash
# List used ports
./check_status.sh

# Check specific port
lsof -i :8015
```

**Currently used:** 8000 (Registry), 8001-8012 (Agents), 8014 (LLM Consultant)
**Available:** 8013, 8015+

#### FDO Types Available

```python
# Task agents (no delegation)
"21.T11148/type-document-processor-v1"    # Document processing
"21.T11148/type-quality-assessor-v1"      # Quality assessment
"21.T11148/type-llm-service-v1"           # LLM services

# Composite agents (orchestration)
"21.T11148/type-workflow-coordinator-v1"  # Multi-step workflows

# Interface agents (user-facing)
"21.T11148/type-user-interface-v1"        # User interfaces

# Data source agents (external APIs)
"21.T11148/type-data-source-v1"           # External data

# Meta agents (system operations)
"21.T11148/type-agent-creator-v1"         # Agent creation
```

To add new type, see [Advanced Topics → Adding New FDO Type](#adding-new-fdo-type)

#### Quick Validation Checklist

Before deploying your agent:

- [ ] Inherits from aFDOBase
- [ ] Implements handle_operation() with async
- [ ] Implements get_self_description()
- [ ] Has unique port number
- [ ] Has valid fdo_type
- [ ] Declares all operations in __init__
- [ ] Has policy.json file
- [ ] Validates all input parameters
- [ ] Returns structured responses
- [ ] Handles errors gracefully
- [ ] Uses self.logger for logging
- [ ] Has unit tests
- [ ] Added to start_system.sh
- [ ] Tested standalone
- [ ] Tested with full system

---

### Quick Start Template

```python
"""My New Agent - One-line description."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
from shared.afdo_base import aFDOBase


class MyNewAgentAgent(aFDOBase):
    """
    My New Agent aFDO.

    Capabilities:
    - operation_1: Description
    - operation_2: Description
    """

    def __init__(self):
        super().__init__(
            name="My New Agent",
            fdo_type="21.T11148/type-YOUR-TYPE-v1",
            operations=["operation_1", "operation_2"],
            port=8015,  # Choose available port
            cost=0.10,
            has_llm=False,
            specialization="domain"
        )

        # Initialize dependencies here
        # self.client = OpenAI(...) if has_llm=True

    def get_metadata_content(self) -> Dict[str, Any]:
        """Agent-specific metadata."""
        return {
            "description": "What this agent does",
            "version": "1.0.0",
            "agent_role": "task_agent",
            "capabilities": {
                "operation_1": {
                    "description": "What this operation does",
                    "estimated_duration": "1-5s",
                    "estimated_cost": "$0.10"
                }
            }
        }

    def get_self_description(self) -> Dict[str, Any]:
        """Structured self-description."""
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
                            "param1": {
                                "type": "string",
                                "description": "What this parameter is"
                            }
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["result"],
                        "properties": {
                            "result": {"type": "string"}
                        }
                    },
                    "constraints": {
                        "timeout_seconds": 30,
                        "rate_limit": 20
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
        print(f"Processing '{operation}' from {caller_pid}")

        if operation == "operation_1":
            return await self._operation_1(parameters)
        elif operation == "operation_2":
            return await self._operation_2(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _operation_1(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implement operation 1."""
        # Validate input
        param1 = parameters.get("param1")
        if not param1:
            raise ValueError("Missing required parameter: param1")

        # Do the work
        result = f"Processed: {param1}"

        # Return structured result
        return {
            "result": result,
            "processor": self.pid,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    async def _operation_2(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implement operation 2."""
        # Implementation here
        pass


if __name__ == "__main__":
    agent = MyNewAgentAgent()
    agent.run()
```

### Agent Types Guide

#### Task Agent

**Characteristics:**
- Single responsibility
- No delegation
- Deterministic
- No built-in LLM

**Example:** PDF Parser

**Template:**
```python
class TaskAgent(aFDOBase):
    def __init__(self):
        super().__init__(
            name="Task Agent",
            fdo_type="21.T11148/type-document-processor-v1",
            operations=["specific_operation"],
            port=8015,
            cost=0.05,
            has_llm=False
        )

    async def handle_operation(self, operation, caller_pid, parameters):
        # Direct implementation, no delegation
        return self._do_work(parameters)
```

#### Composite Agent

**Characteristics:**
- Multi-step workflows
- Discovers and calls helpers
- Has built-in LLM
- Budget-aware

**Example:** Paper Analyzer

**Template:**
```python
class CompositeAgent(aFDOBase):
    def __init__(self):
        super().__init__(
            name="Composite Agent",
            fdo_type="21.T11148/type-workflow-coordinator-v1",
            operations=["complex_workflow"],
            port=8015,
            cost=0.05,
            has_llm=True
        )
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def handle_operation(self, operation, caller_pid, parameters):
        budget = BudgetManager(total_budget=parameters["budget"])

        # Step 1: Call helper A
        result_a = await self.call_with_alternatives(
            operation="helper_operation",
            parameters=parameters,
            budget=budget
        )

        # Step 2: Use built-in LLM
        analysis = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": result_a["data"]}]
        )

        # Step 3: Call helper B
        result_b = await self.call_with_alternatives(
            operation="another_operation",
            parameters={"data": analysis},
            budget=budget
        )

        return {
            "result": result_b,
            "budget_summary": budget.get_breakdown()
        }
```

#### Data Source Agent

**Characteristics:**
- External API integration
- Policy-based delegation for complex tasks
- Error handling for API failures

**Example:** Wikipedia Agent

**Template:**
```python
class DataSourceAgent(aFDOBase):
    def __init__(self):
        super().__init__(
            name="Data Source Agent",
            fdo_type="21.T11148/type-data-source-v1",
            operations=["fetch_data"],
            port=8015,
            cost=0.01,
            has_llm=False
        )

    async def handle_operation(self, operation, caller_pid, parameters):
        try:
            # Call external API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.example.com/data",
                    params=parameters,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            return {
                "data": data,
                "source": "api.example.com"
            }

        except httpx.HTTPError as e:
            self.logger.error(f"API error: {e}")
            raise ValueError(f"Failed to fetch data: {e}")
```

### Adding Operations

To add new operations to existing agent:

```python
# 1. Add to operations list in __init__
operations=["existing_op", "new_operation"]

# 2. Add to self_description
"capabilities": {
    "new_operation": {
        "operation_type": "data_extraction",
        "input_schema": {...},
        "output_schema": {...}
    }
}

# 3. Add handler in handle_operation
elif operation == "new_operation":
    return await self._new_operation(parameters)

# 4. Implement method
async def _new_operation(self, parameters):
    # Implementation
    return {"result": "..."}

# 5. Restart agent to re-register
```

### External Data Source Agents

External data source agents fetch data from external public APIs and integrate seamlessly with the aFDO system through policy-driven autonomy and semantic discovery.

#### Key Features

**Autonomous Operation:**
- Each agent uses the **policy engine** for decision-making
- Agents decide when to handle tasks alone or delegate
- **NO hardcoded workflows** - agents discovered dynamically via semantic matching
- Pure registry-mediated collaboration

**Dynamic Discovery:**
- Agents discovered at **runtime via registry**
- No agent knows about other agents in advance
- Selection based on cost, reputation, availability
- Direct P2P calling pattern (no pre-negotiation in current implementation)

**Policy-Based Behavior:**
- Each agent has its own **policy.json** file
- Policies determine behavior patterns without code changes
- Rules evaluated by priority

#### Example External Agents

**1. Wikipedia Agent (Port 8010)**
- API: Wikipedia REST API (free, no auth)
- Operations: `get_article_summary`, `search_wikipedia`, `get_facts`
- Cost: $0.01 per operation
- Use case: General knowledge, historical facts

**2. ArXiv Agent (Port 8011)**
- API: ArXiv API (free, no auth)
- Operations: `search_papers`, `get_paper_abstract`, `find_research`
- Cost: $0.02 per operation
- Use case: Scientific research papers

**3. OpenLibrary Agent (Port 8012)**
- API: Open Library API (free, no auth)
- Operations: `search_books`, `get_book_info`, `find_references`
- Cost: $0.01 per operation
- Use case: Book references, literature search

#### How Dynamic Workflows Work

When a complex query arrives (e.g., "Explain history and science of coffee"):

```
Wikipedia Agent receives request
    ↓
Policy Engine evaluates:
    - "history" → I can handle ✓
    - "science" → Need scientific papers ✗
    - Complexity: COMPLEX
    - Decision: CONSULT_FOR_WORKFLOW
    ↓
Wikipedia queries registry: "Who can generate_workflow?"
    ↓
Registry returns: LLM Consultant (port 8014)
    ↓
Wikipedia calls LLM Consultant with task description
    ↓
LLM Consultant generates workflow:
    {
    }
    ↓
Chat UI discovers agents semantically
    ↓
Chat UI builds fallback chain:
    [Candidate 1] Wikipedia (similarity: 0.85, cost: $0.01)
    [Candidate 2] Open Library (similarity: 0.72, cost: $0.01)
    [Candidate 3] LLM Consultant (similarity: 0.65, cost: $0.03)
    ↓
Chat UI delegates to Wikipedia (first candidate)
    ↓
Wikipedia fetches article summary
    ↓
Result returned to Chat UI → User
```

**Actual Flow (Current Implementation):**
- ✅ Policy engine evaluates: "semantic_discovery"
- ✅ Semantic discovery finds matching operations
- ✅ Agents discovered at runtime via registry
- ✅ Single-level delegation with fallback chain
- ✅ **Pure autonomous behavior - NO hardcoding!**

**Note:** Multi-step workflow generation via LLM Consultant exists in code but is not used in production. The system uses direct semantic discovery and single-level delegation instead.

#### Creating External Data Source Agents

**Step-by-step guide:**

1. **Create Agent Class**

```python
from shared.afdo_base import aFDOBase
import httpx

class MyDataAgent(aFDOBase):
    def __init__(self):
        super().__init__(
            name="My Data Agent",
            fdo_type="21.T11148/type-data-source-v1",
            operations=["search_data", "get_info"],
            port=8015,
            cost=0.03,
            has_llm=False,
            specialization="my_domain"
        )
        self.api_url = "https://api.example.com"

    def get_metadata_content(self) -> Dict[str, Any]:
        return {
            "description": "Fetches data from Example API",
            "version": "1.0.0",
            "agent_role": "data_source",
            "api_endpoint": self.api_url
        }

    def get_self_description(self) -> Dict[str, Any]:
        return {
            "agent_info": {
                "name": "My Data Agent",
                "version": "1.0.0",
                "agent_type": "data_source",
                "description": "Fetches data from external API"
            },
            "capabilities": {
                "search_data": {
                    "operation_type": "data_retrieval",
                    "input_schema": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 10}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["results"],
                        "properties": {
                            "results": {"type": "array"},
                            "count": {"type": "integer"}
                        }
                    }
                }
            }
        }

    async def handle_operation(self, operation, caller_pid, parameters):
        if operation == "search_data":
            return await self._search_data(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _search_data(self, parameters):
        query = parameters.get("query")
        limit = parameters.get("limit", 10)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/search",
                    params={"q": query, "limit": limit},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            return {
                "results": data.get("results", []),
                "count": len(data.get("results", [])),
                "source": self.api_url,
                "processor": self.pid
            }

        except httpx.HTTPError as e:
            self.logger.error(f"API error: {e}")
            raise ValueError(f"Failed to fetch data: {e}")
```

2. **Create Policy File** (`agents/my_data_agent/policy.json`)

```json
{
  "policy_id": "my_data_agent_policy",
  "default_action": "handle_alone",
  "rules": [
    {
      "rule_id": "rule_01_handle_data_lookup",
      "priority": 10,
      "conditions": {
        "operation": ["search_data", "get_info"],
        "has_capability": true
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "Data lookups are my core capability"
      }
    },
    {
      "rule_id": "rule_02_complex_need_workflow",
      "priority": 9,
      "conditions": {
        "complexity": "complex"
      },
      "action": {
        "type": "consult_for_workflow",
        "reasoning": "Task too complex - need consultant to generate workflow",
        "parameters": {
          "consultant_query": {
            "operations": ["generate_workflow", "plan_task"]
          }
        }
      }
    },
    {
      "rule_id": "rule_03_unknown_operation",
      "priority": 5,
      "conditions": {
        "has_capability": false
      },
      "action": {
        "type": "query_registry_for_helper",
        "reasoning": "I don't have this capability, need helper"
      }
    }
  ]
}
```

3. **Update Startup Script** (add to `start_system.sh`)

```bash
echo "Starting My Data Agent (port 8015)..."
start_agent "my-data-agent" \
  "agents/my_data_agent/my_data_agent.py" \
  "8015" || FAILED=$((FAILED+1))
```

4. **Test Agent**

```bash
# Start agent
python3 agents/my_data_agent/my_data_agent.py

# Test operation
curl -X POST http://localhost:8015/doip/extend/search_data \
  -H "Content-Type: application/json" \
  -d '{
    "authentication": {"caller_pid": "test"},
    "parameters": {"query": "test", "limit": 5}
  }'
```

5. **Verify Registration**

```bash
python3 scripts/verify_agent_registration.py
# Should show: ✅ My Data Agent    Type: 21.T11148/type-data-source-v1    Port: 8015
```

#### Best Practices for Data Source Agents

**1. Keep Agents Simple**
- One agent = One API/data source
- Clear, focused responsibility
- Easy to understand and maintain

**2. Use Policies, Not Code**
- Behavior defined in JSON
- Update without redeployment
- Version-controlled separately

**3. Enable Discovery**
- Register all operations clearly
- Use descriptive operation names
- Provide good metadata

**4. Provide Cost Information**
- Define base cost in agent initialization
- Cost is tracked but not negotiated in current implementation
- Budget constraints are monitored but not strictly enforced

**5. Handle Failures Gracefully**
- Return meaningful error messages
- Support fallback strategies
- Don't crash on API errors
- Implement retry with backoff

**6. Document Thoroughly**
- Clear operation schemas
- Input/output examples
- Rate limits and constraints
- API dependencies

#### Troubleshooting External Agents

**Agent Not Discovered**

Symptoms: Agent not appearing in registry queries

Solutions:
1. Check agent is running: `./check_status.sh`
2. Verify registration succeeded: Check agent startup logs
3. Confirm operation names match: Use `verify_agent_registration.py`
4. Check port conflicts: `lsof -i :8015`

**Operations Fail**

Symptoms: API calls returning errors

Solutions:
1. Check API connectivity: Test API directly with curl
2. Verify API rate limits: Review API documentation
3. Check timeout settings: Increase if needed for slow APIs
4. Review error logs: `tail -f logs/my-data-agent.log`

**Cost Escalation**

Symptoms: Budget exceeded errors

Solutions:
1. Check cost estimates: Review negotiation logs
2. Verify budget allocation: Check parameters
3. Review workflow complexity: May need more budget
4. Check for loops: Verify workflow structure

**Policy Not Working**

Symptoms: Agent behavior unexpected

Solutions:
1. Validate JSON: `python3 -c "import json; json.load(open('policy.json'))"`
2. Check rule priorities: Higher priority = evaluated first
3. Review conditions: Must match for rule to fire
4. Test policy decision: Add debug logging in policy_engine.py

#### Architecture Principles

**No Hardcoding:**
- ✅ Agents discovered at runtime via semantic discovery
- ✅ No compile-time dependencies between agents
- ✅ Policy-driven routing decisions
- ❌ No hardcoded agent references
- ⚠️ Note: Workflow generation capability exists but not used in production

**Pure Autonomy:**
- ✅ Policy-driven decisions
- ✅ Runtime discovery via registry
- ✅ Fallback chains with automatic retry
- ✅ Graceful degradation
- ⚠️ Note: LLM workflow generation is aspirational, not production

**Protocol-Driven:**
- ✅ DOIP protocol for all agent calls
- ✅ Direct P2P calling pattern
- 📋 Note: Negotiation protocol exists but agents use direct `call_other_afdo()` in practice
- 📋 Note: WorkflowEngine exists but not instantiated in production
- ✅ Registry for discovery
- ✅ DOIP for communication

This architecture enables the system to handle **any query** by dynamically generating optimal workflows and discovering the right agents at runtime - **no predefined paths, pure autonomous intelligence.**

---

## Policy Configuration

### Policy File Structure

**Location:** `agents/<agent_name>/policy.json`

**Complete Example:**

```json
{
  "policy_id": "agent_policy_v1",
  "policy_version": "1.0.0",
  "description": "Policy for My Agent",
  "default_action": "handle_alone",

  "rules": [
    {
      "rule_id": "rule_01_core_capability",
      "description": "Handle operations within core capabilities",
      "priority": 10,

      "conditions": {
        "operation": ["op1", "op2"],
        "has_capability": true,
        "complexity": "simple"
      },

      "action": {
        "type": "handle_alone",
        "reasoning": "These are my core operations",
        "parameters": {}
      }
    },

    {
      "rule_id": "rule_02_complex_task",
      "description": "Delegate complex tasks to planners",
      "priority": 8,

      "conditions": {
        "complexity": "complex"
      },

      "action": {
        "type": "query_registry_for_planner",
        "reasoning": "Complex tasks need planning and coordination",
        "parameters": {
          "registry_query": {
            "operations": ["plan_workflow", "generate_workflow"],
            "fallback_operations": ["interpret_natural_language"],
            "selection_criteria": "balanced"
          }
        },
        "fallback": {
          "type": "handle_alone",
          "parameters": {
            "warning": "Handling without planner"
          }
        }
      }
    },

    {
      "rule_id": "rule_03_unknown_operation",
      "description": "Find helpers for unknown operations",
      "priority": 5,

      "conditions": {
        "has_capability": false
      },

      "action": {
        "type": "query_registry_for_helper",
        "reasoning": "I don't have this capability, need helper",
        "parameters": {
          "registry_query": {
            "selection_criteria": "balanced"
          }
        }
      }
    },

    {
      "rule_id": "rule_04_budget_constrained",
      "description": "Use cheap services when budget is low",
      "priority": 7,

      "conditions": {
        "budget_threshold": 0.10,
        "complexity": "moderate"
      },

      "action": {
        "type": "query_registry_for_helper",
        "reasoning": "Low budget, prioritize cheap services",
        "parameters": {
          "registry_query": {
            "selection_criteria": "cheapest"
          }
        }
      }
    }
  ]
}
```

### Enabling Multi-Level Cascading

To enable your agent to participate in multi-level cascading (recursively delegate to other agents), add a synthesis detection rule to your policy:

**Pattern (for data source agents):**

```json
{
  "rules": [
    {
      "rule_id": "rule_00_delegate_synthesis_queries",
      "description": "Delegate synthesis/comparison queries to LLM",
      "priority": 11,
      "conditions": {
        "operation": ["receive_query"],
        "query_requires_synthesis": true
      },
      "action": {
        "type": "semantic_discovery",
        "reasoning": "Query requires synthesis beyond simple lookup",
        "parameters": {
          "discovery_query": {
            "use_semantic_matching": true,
            "min_similarity": 0.3,
            "selection_criteria": "balanced"
          }
        }
      }
    },

    {
      "rule_id": "rule_01_handle_simple_queries",
      "description": "Handle simple queries directly",
      "priority": 10,
      "conditions": {
        "operation": ["receive_query", "get_article_summary"],
        "has_capability": true
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "Simple lookup within my capability"
      }
    }
  ]
}
```

**How It Works:**

1. **Agent receives query** via `receive_query` operation
2. **Policy engine evaluates** `query_requires_synthesis` condition
3. **Synthesis keywords detected:**
   - compare, versus, analyze, evaluate
   - explain, why, how does
   - pros and cons, advantages, disadvantages
   - better, worse, best, optimal
4. **If synthesis needed:** Rule 00 matches → SEMANTIC_DISCOVERY
5. **Agent discovers LLM** and delegates for synthesis
6. **Multi-level cascade achieved:** User → Your Agent → LLM → Result

**Example Flow:**

```
User: "Compare Algeria and Morocco"
  ↓
Chat UI → Wikipedia (your agent)
  ↓
Wikipedia policy detects "compare" → query_requires_synthesis = TRUE
  ↓
Wikipedia → LLM Consultant (semantic discovery)
  ↓
LLM synthesizes comparison
  ↓
Results: LLM → Wikipedia → Chat UI → User
```

**Benefits:**

- ✅ Your agent automatically knows when it needs help
- ✅ No hardcoded delegation logic
- ✅ Works with any LLM agent in the system
- ✅ Graceful fallback if LLM unavailable
- ✅ Complete trace of multi-level delegation

### Condition Types

**operation:** Match specific operations
```json
"conditions": {
  "operation": ["extract_text", "extract_metadata"]
}
```

**has_capability:** Check if agent can perform operation
```json
"conditions": {
  "has_capability": true
}
```

**complexity:** Task complexity assessment
```json
"conditions": {
  "complexity": "simple"  // simple|moderate|complex|very_complex
}
```

**parameter_count:** Number of parameters
```json
"conditions": {
  "parameter_count": {"operator": "<=", "value": 2}
}
```

**budget_threshold:** Minimum budget required
```json
"conditions": {
  "budget_threshold": 0.50
}
```

**query_requires_synthesis:** Detects synthesis/comparison queries (enables multi-level cascading)
```json
"conditions": {
  "operation": ["receive_query"],
  "query_requires_synthesis": true
}
```

Synthesis keywords detected:
- compare, versus, difference between, analyze, evaluate
- explain, why, how does, what makes
- pros and cons, advantages, disadvantages
- better, worse, best, optimal

### Action Types

**handle_alone:** Execute directly
```json
"action": {
  "type": "handle_alone",
  "reasoning": "Core capability"
}
```

**query_registry_for_helper:** Find specific helper
```json
"action": {
  "type": "query_registry_for_helper",
  "reasoning": "Need specialized service",
  "parameters": {
    "registry_query": {
      "operations": ["specific_operation"],
      "selection_criteria": "balanced"
    }
  }
}
```

**query_registry_for_planner:** Find workflow planner
```json
"action": {
  "type": "query_registry_for_planner",
  "reasoning": "Need planning",
  "parameters": {
    "registry_query": {
      "operations": ["plan_workflow", "generate_workflow"]
    }
  }
}
```

**semantic_discovery:** Discover agents via semantic matching (enables multi-level cascading)
```json
"action": {
  "type": "semantic_discovery",
  "reasoning": "Query requires synthesis beyond my capability",
  "parameters": {
    "discovery_query": {
      "use_semantic_matching": true,
      "min_similarity": 0.3,
      "selection_criteria": "balanced"
    }
  }
}
```

Use this for multi-level delegation where your agent needs to find the best helper dynamically based on query semantics.

**collaborate:** Multi-agent collaboration
```json
"action": {
  "type": "collaborate",
  "reasoning": "Need multiple services",
  "parameters": {
    "required_operations": ["op1", "op2"],
    "strategy": "parallel"
  }
}
```

### Policy Loading

Policies load automatically with fallback chain:

1. **Agent-specific:** `agents/<name>/policy.json`
2. **Type-based default:** `shared/policies/default_<type>_policy.json`
3. **No policy:** Agent works without policy

**Check policy loading:**
```bash
# Start agent and check logs
tail -f logs/<agent-name>.log | grep -i policy

# Should see:
# [INFO] Policy loaded from agents/my_agent/policy.json
# Or:
# [INFO] Policy loaded from shared/policies/default_task_policy.json
```

### Understanding Multi-Objective Agent Scoring

When your agent uses `semantic_discovery`, the registry automatically applies **multi-objective scoring** to rank candidates intelligently.

**Implementation:** `registry/main.py` lines 712-830

#### How It Benefits Your Agent

**Before (pure semantic matching):**
```python
# Agent A: similarity=0.90, reputation=0.50, cost=$0.10
# Agent B: similarity=0.85, reputation=0.95, cost=$0.01
# Selection: Agent A (higher similarity, but unreliable and expensive)
```

**After (multi-objective scoring):**
```python
# Agent A: score = 0.6(0.90) + 0.3(0.50) - 0.1(1.0) = 0.540 + 0.150 - 0.100 = 0.590
# Agent B: score = 0.6(0.85) + 0.3(0.95) - 0.1(0.1) = 0.510 + 0.285 - 0.010 = 0.785
# Selection: Agent B (better overall quality and value) ✓
```

#### The Scoring Formula

```
score(a_i, o_{i,j}) = α·s_{i,j} + β·r_i - γ·(c_{i,j}/c_max)

where:
- s_{i,j} = max(s^op_{i,j}, s^agent_i)  # Best semantic match
- α = 0.6  # Semantic similarity weight (most important)
- β = 0.3  # Reputation weight (quality matters)
- γ = 0.1  # Cost penalty weight (prefer cheaper)
- α + β + γ = 1  # Normalized weights
```

#### What Your Agent Gets

When your agent calls:
```python
# In your agent's policy
{
  "action": {
    "type": "semantic_discovery",
    "reasoning": "Need best agent for this query"
  }
}
```

The registry automatically:
1. **Embeds the query** using sentence transformers
2. **Compares against all agents** (descriptions AND operations)
3. **Calculates semantic similarity** for each candidate
4. **Applies multi-objective scoring** with reputation and cost
5. **Returns ranked results** sorted by composite score

**Your agent receives:**
```python
[
  {
    "agent_pid": "21.T11148/afdo-wikipedia-agent",
    "agent_name": "Wikipedia Agent",
    "semantic_similarity": 0.427,
    "combined_score": 0.386,  # Multi-objective score
    "cost": 0.01,
    "reputation": 0.500,
    "scoring_weights": {"alpha": 0.6, "beta": 0.3, "gamma": 0.1}
  },
  # ... more candidates sorted by combined_score
]
```

#### When to Use Semantic Discovery

**Use `semantic_discovery` when:**
- Query is natural language (not a specific operation name)
- Multiple agents might handle the task
- You want the best match considering quality AND cost
- You need intelligent agent selection

**Example policy:**
```json
{
  "rule_id": "rule_natural_language_query",
  "priority": 10,
  "conditions": {
    "operation": ["receive_query", "handle_request"],
    "query_type": "natural_language"
  },
  "action": {
    "type": "semantic_discovery",
    "reasoning": "Use multi-objective scoring for best agent match",
    "parameters": {
      "discovery_query": {
        "use_semantic_matching": true,
        "min_similarity": 0.3,
        "top_k": 5
      }
    }
  }
}
```

#### Tuning Priorities (Future)

Currently weights are fixed at α=0.6, β=0.3, γ=0.1, but the system is designed for future configurability:

**For accuracy-critical tasks:**
```python
# Future: α=0.8, β=0.15, γ=0.05
# Prioritizes semantic match, less concern for cost
```

**For production reliability:**
```python
# Future: α=0.5, β=0.4, γ=0.1
# Prioritizes proven agents, balanced semantic match
```

**For cost-conscious batch processing:**
```python
# Future: α=0.5, β=0.2, γ=0.3
# Strong preference for cheaper agents
```

#### Developer Benefits

1. **Less Code:** No need to implement ranking logic in your agent
2. **Better Results:** Balanced selection considering multiple factors
3. **Production-Ready:** Proven agents preferred over untested ones
4. **Cost-Aware:** Automatic preference for value
5. **Transparent:** Full scoring breakdown in results

#### Testing Multi-Objective Scoring

**Test your agent's semantic discovery:**

```bash
# 1. Start system
./start_system.sh

# 2. Send natural language query
curl -X POST http://localhost:8001/doip/extend/receive_user_input \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "message": "who is the president of Algeria"
    }
  }'

# 3. Check logs for scoring details
tail -100 logs/system.log | grep "📊"

# You should see:
# [Registry] 📊 Wikipedia Agent:
#     sem=0.427 (max(agent=0.427, best_op=0.303))
#     rep=0.500
#     cost=$0.01
#     final=0.386
```

**Debug scoring:**
```bash
# Enable detailed scoring logs
export LOG_LEVEL=DEBUG

# Restart registry to see scoring calculations
./stop_system.sh
./start_system.sh

# Watch scoring in real-time
tail -f logs/system.log | grep -E "(📊|semantic|score)"
```

---

## Testing Procedures

### Manual Testing

**Test Agent Standalone:**

```bash
# 1. Start registry
python3 registry/main.py &

# 2. Wait for registry
sleep 3

# 3. Start your agent
python3 agents/my_new_agent/my_new_agent_agent.py

# 4. Check registration
curl http://localhost:8000/doip/search/fdos | grep "My New Agent"

# 5. Test operation
curl -X POST http://localhost:8015/doip/call \
  -H "Content-Type: application/json" \
  -d '{
    "target_pid": "21.T11148/afdo-my-new-agent",
    "operation": "operation_1",
    "caller_pid": "test",
    "parameters": {"param1": "test value"}
  }'

# 6. Check logs
tail -f logs/my-new-agent.log
```

### Automated Testing

**Test Structure:**

```python
# tests/test_my_agent.py

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.my_new_agent.my_new_agent_agent import MyNewAgentAgent


@pytest.fixture
def agent():
    """Create agent instance for testing."""
    return MyNewAgentAgent()


@pytest.mark.asyncio
async def test_operation_1(agent):
    """Test operation_1 with valid input."""
    result = await agent.handle_operation(
        operation="operation_1",
        caller_pid="test",
        parameters={"param1": "test"}
    )

    assert result["result"] == "Processed: test"
    assert "processor" in result


@pytest.mark.asyncio
async def test_operation_1_missing_param(agent):
    """Test operation_1 with missing parameter."""
    with pytest.raises(ValueError, match="Missing required parameter"):
        await agent.handle_operation(
            operation="operation_1",
            caller_pid="test",
            parameters={}
        )


@pytest.mark.asyncio
async def test_unknown_operation(agent):
    """Test unknown operation."""
    with pytest.raises(ValueError, match="Unknown operation"):
        await agent.handle_operation(
            operation="unknown_op",
            caller_pid="test",
            parameters={}
        )


def test_self_description(agent):
    """Test self-description structure."""
    desc = agent.get_self_description()

    assert "agent_info" in desc
    assert "capabilities" in desc
    assert "operation_1" in desc["capabilities"]
    assert "input_schema" in desc["capabilities"]["operation_1"]
    assert "output_schema" in desc["capabilities"]["operation_1"]


def test_metadata_content(agent):
    """Test metadata content."""
    metadata = agent.get_metadata_content()

    assert "description" in metadata
    assert "version" in metadata
    assert "capabilities" in metadata
```

**Run Tests:**

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_my_agent.py

# Run with coverage
pytest --cov=agents tests/

# Run with verbose output
pytest -v tests/

# Run specific test
pytest tests/test_my_agent.py::test_operation_1
```

### Integration Testing

**Test with Full System:**

```bash
# 1. Start full system
./start_system.sh

# 2. Wait for startup
sleep 5

# 3. Test via API
curl -X POST http://localhost:8001/doip/call \
  -H "Content-Type: application/json" \
  -d '{
    "target_pid": "21.T11148/afdo-chat-ui",
    "operation": "receive_user_input",
    "caller_pid": "test",
    "parameters": {
      "message": "Test my new agent",
      "budget": 1.0
    }
  }'

# 4. Check trace
curl http://localhost:8000/registry/fdos/21.T11148/afdo-my-new-agent/activity_log

# 5. Check logs
grep -i "my new agent" logs/afdo_$(date +%Y-%m-%d).log
```

### Policy Testing

**Test Policy Decisions:**

```python
# tests/test_my_agent_policy.py

import pytest
from shared.policy_engine import PolicyEngine


def test_policy_simple_operation():
    """Test policy for simple operation."""
    engine = PolicyEngine(
        agent_pid="test",
        agent_capabilities=["operation_1"],
        policy_file="agents/my_new_agent/policy.json"
    )

    decision = engine.decide(
        operation="operation_1",
        parameters={"param1": "test"},
        context={"complexity": "simple"}
    )

    assert decision.decision == "handle_alone"
    assert decision.rule_id == "rule_01"


def test_policy_complex_operation():
    """Test policy for complex operation."""
    engine = PolicyEngine(
        agent_pid="test",
        agent_capabilities=["operation_1"],
        policy_file="agents/my_new_agent/policy.json"
    )

    decision = engine.decide(
        operation="operation_1",
        parameters={"param1": "complex task"},
        context={"complexity": "complex"}
    )

    assert decision.decision == "query_registry_for_planner"
    assert decision.rule_id == "rule_02"
```

---

## Development Workflow

### Typical Development Cycle

```
1. Design
   └─ Define agent purpose, operations, inputs/outputs

2. Implement
   └─ Create agent class, implement operations

3. Create Policy
   └─ Define decision rules in policy.json

4. Test Locally
   └─ Test agent standalone with test inputs

5. Test Discovery
   └─ Verify agent can be discovered by operation

6. Test Integration
   └─ Test with full system, check interactions

7. Add to Startup
   └─ Include in start_system.sh

8. Document
   └─ Update DEVELOPER_GUIDE.md agent reference section

9. Commit
   └─ Version control changes
```

### Feature Development

**Adding New Operation to Existing Agent:**

```bash
# 1. Create feature branch (if using git)
git checkout -b feature/add-new-operation

# 2. Edit agent file
# - Add operation to operations list
# - Add to self_description
# - Add handler in handle_operation
# - Implement method

# 3. Update policy if needed
# - Add rule for new operation

# 4. Test
pytest tests/test_agent.py
python3 agents/agent/agent.py  # Test standalone

# 5. Test integration
./stop_system.sh
./start_system.sh
# Test via UI or API

# 6. Document
# Update AGENTS.md

# 7. Commit (if using git)
git add agents/agent/agent.py
git commit -m "Add new_operation to Agent"
git push origin feature/add-new-operation
```

### Bug Fixing

**Workflow:**

```bash
# 1. Reproduce bug
# - Write test that fails
# - Run agent with debug logging

# 2. Debug
export LOG_LEVEL=DEBUG
python3 agents/agent/agent.py
tail -f logs/agent.log

# 3. Fix
# - Modify code
# - Verify test passes

# 4. Test regression
pytest tests/  # Run all tests

# 5. Deploy
./stop_system.sh
./start_system.sh

# 6. Verify fix
# - Test in production scenario
# - Check logs
```

---

## Helper Scripts

### initialize_types.py

**Purpose:** Initialize or reset FDO type system

**Usage:**
```bash
# Make sure registry is running
python3 scripts/initialize_types.py
```

**What it does:**
- Connects to registry
- Creates/updates all type definitions
- Creates default profile
- Validates schemas

**When to use:**
- First time setup
- After adding new types
- After corrupting type data
- After registry data reset

### Startup Scripts

#### start_system.sh

**Purpose:** Start all agents in correct order

**Customization:**

```bash
# Add new agent
echo ""
echo "Starting my new agent (port 8015)..."
start_agent "my-new-agent" \
  "agents/my_new_agent/my_new_agent_agent.py" \
  "8015" || FAILED=$((FAILED+1))
```

**Functions available:**
- `start_agent <name> <path> <port>` - Start agent with monitoring
- `check_port <port>` - Check if port is available
- `wait_for_registry` - Wait for registry to be ready

#### stop_system.sh

**Purpose:** Gracefully stop all agents

**Features:**
- Reverse order shutdown
- PID file-based termination
- Force kill if needed
- Cleanup

#### check_status.sh

**Purpose:** Check system status

**Output:**
- Which agents are running
- Port status
- PID information
- Summary

---

## Debugging

### Enable Debug Logging

**System-wide:**
```bash
export LOG_LEVEL=DEBUG
./stop_system.sh
./start_system.sh
```

**Single agent:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Debugging Scenarios

#### Agent Won't Register

**Check:**
```bash
# 1. Is registry running?
curl http://localhost:8000/

# 2. Is port available?
lsof -i :8015

# 3. Check agent logs
tail -f logs/my-agent.log

# 4. Check API key (if LLM agent)
echo $OPENAI_API_KEY
```

#### Agent Not Discovered

**Check:**
```bash
# 1. Is agent registered?
curl http://localhost:8000/doip/search/fdos | grep "My Agent"

# 2. Check operations
curl http://localhost:8000/market/agents/by_operation/my_operation

# 3. Check agent status
curl http://localhost:8000/doip/read/fdo/21.T11148/afdo-my-agent
```

#### Policy Not Loading

**Check:**
```bash
# 1. Check file exists
ls -la agents/my_agent/policy.json

# 2. Validate JSON
python3 -m json.tool agents/my_agent/policy.json

# 3. Check agent logs
tail -f logs/my-agent.log | grep -i policy
```

#### Budget Errors

**Check:**
```bash
# 1. Check budget in parameters
# Budget must be > 0

# 2. Check cost estimates
curl http://localhost:8000/market/agents/by_operation/operation
# Compare costs to budget

# 3. Check budget logs
tail -f logs/paper-analyzer.log | grep -i budget
```

### Debugging Tools

**Python Debugger (pdb):**
```python
# In agent code
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

**VS Code Debugger:**

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Agent",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/agents/my_agent/my_agent_agent.py",
      "console": "integratedTerminal",
      "env": {
        "OPENAI_API_KEY": "your-key"
      }
    }
  ]
}
```

**HTTP Debugging:**
```bash
# Use httpie for better output
pip install httpie

http POST http://localhost:8015/doip/call \
  target_pid="21.T11148/afdo-my-agent" \
  operation="operation_1" \
  caller_pid="test" \
  parameters:='{"param1": "test"}'
```

---

## Best Practices

### Code Style

**Follow PEP 8:**
```bash
# Format code
black agents/my_agent/

# Check style
flake8 agents/my_agent/

# Type checking
mypy agents/my_agent/
```

**Naming Conventions:**
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Agent Design

**1. Single Responsibility**
- One agent, one clear purpose
- Don't create "Swiss Army knife" agents

**2. Clear Interfaces**
- Well-defined input/output schemas
- Comprehensive error messages
- Validation at boundaries

**3. Idempotency**
- Same input = same output
- No side effects (unless documented)
- Stateless when possible

**4. Error Handling**
```python
async def handle_operation(self, operation, caller_pid, parameters):
    try:
        # Validate inputs
        self._validate_parameters(operation, parameters)

        # Execute
        result = await self._execute(operation, parameters)

        # Validate outputs
        self._validate_result(operation, result)

        return result

    except ValueError as e:
        # User error
        self.logger.warning(f"Validation error: {e}")
        raise

    except Exception as e:
        # System error
        self.logger.error(f"Execution error: {e}", exc_info=True)
        raise RuntimeError(f"Operation failed: {e}")
```

**5. Logging Best Practices**
```python
# Info: Normal operations
self.logger.info(f"Processing {operation}")

# Warning: Recoverable issues
self.logger.warning(f"Retrying after failure: {e}")

# Error: Failures
self.logger.error(f"Operation failed: {e}", exc_info=True)

# Debug: Detailed information
self.logger.debug(f"Parameters: {parameters}")
```

### Policy Design

**1. Clear Priorities**
- Specific rules: High priority (10+)
- General rules: Medium priority (5-9)
- Fallbacks: Low priority (1-4)

**2. Meaningful Reasoning**
- Explain why decision was made
- Help debugging
- Enable transparency

**3. Comprehensive Coverage**
- Handle all expected scenarios
- Provide fallback for unexpected
- Default action for safety

### Testing Strategy

**Unit Tests:**
- Test each operation independently
- Mock external dependencies
- Test error cases

**Integration Tests:**
- Test with real registry
- Test discovery
- Test delegation chains

**End-to-End Tests:**
- Test complete workflows
- Test with real data
- Test cost tracking

---

## Advanced Topics

### Adding New FDO Type

**1. Define type in `scripts/initialize_types.py`:**

```python
new_type = {
    "pid": "21.T11148/type-my-new-type-v1",
    "name": "my_new_type",
    "category": "task_agent",
    "description": "Description of type",
    "expected_capabilities": ["required_op"],
    "optional_capabilities": ["optional_op"],
    "version": "1.0.0"
}

# Add to type creation loop
await create_type(new_type)
```

**2. Run type initialization:**
```bash
python3 scripts/initialize_types.py
```

**3. Create default policy:**
```bash
# Create shared/policies/default_my_new_type_policy.json
```

### Custom Selection Policy

**Create custom policy:**

```python
# shared/custom_policies.py

from shared.selection_policy import SelectionPolicy

class CostPerQualityPolicy(SelectionPolicy):
    """Select based on cost per quality point."""

    def select(self, quotes, reputations, criteria):
        candidates = self._filter_quotes(quotes, reputations, criteria)

        def cost_per_quality(quote):
            rep = reputations.get(quote.agent_pid, 0.85)
            cost = quote.estimated_cost if quote.estimated_cost > 0 else 0.01
            return cost / rep  # Lower is better

        return min(candidates, key=cost_per_quality)
```

**Use custom policy:**

```python
from shared.custom_policies import CostPerQualityPolicy

class MyAgent(aFDOBase):
    def __init__(self):
        super().__init__(...)
        self.selection_policy = CostPerQualityPolicy()
```

### Dynamic Workflow Generation

**📋 Note: This feature is implemented but not used in production. The code below shows how it *could* be used.**

**Use LLM Consultant to generate workflows (aspirational):**

```python
# In composite agent (NOT CURRENTLY USED IN PRODUCTION)
async def handle_complex_task(self, parameters):
    # Generate workflow dynamically
    workflow_result = await self.call_other_afdo(
        target_pid="21.T11148/llm-consultant",
        operation="generate_workflow",
        data={
            "task_description": parameters["task"],
            "requester_capabilities": self.operations,
            "context": {
                "budget": parameters["budget"],
                "quality_preference": "balanced"
            }
        }
    )

    workflow = workflow_result["data"]["workflow"]

    # Execute generated workflow (requires WorkflowEngine instantiation)
    # Note: WorkflowEngine exists but is not instantiated in current agents
    results = await self._execute_workflow(workflow, parameters)

    return results
```

**Current Production Pattern (Semantic Discovery):**

Instead of workflow generation, agents use semantic discovery:

```python
# What actually happens in production
async def handle_complex_task(self, parameters):
    # Use semantic discovery to find best agent
    result = await self._semantic_discovery_and_cascade(
        decision, "receive_query", parameters
    )
    return result
```

### Custom Activity Logging

**Add custom log aggregation:**

```python
class MyAgent(aFDOBase):
    async def call_other_afdo(self, target_pid, operation, data):
        # Call parent implementation
        result = await super().call_other_afdo(target_pid, operation, data)

        # Custom logging
        await self._log_custom_metric(
            operation=operation,
            target=target_pid,
            duration=result.get("duration"),
            custom_field="custom_value"
        )

        return result
```

---

## Agent Operations Reference

This section provides detailed operation schemas, input/output specifications, constraints, and implementation details for all agents in the system. For comprehensive agent information, refer to this reference when implementing new operations or understanding existing ones.

### Complete Agent Reference

For the complete reference of all agents with detailed operation schemas, input/output specifications, constraints, and implementation details with line numbers, see the dedicated agent documentation:

**Available Agents:**
1. **PDF Parser Agent** (Port 8004) - Document text/metadata extraction
2. **FAIR Assessor Agent** (Port 8005) - FAIR compliance evaluation
3. **Paper Analyzer Agent** (Port 8003) - Autonomous composite analysis
4. **Chat UI Agent** (Port 8001) - Web interface with query interpretation
5. **Creator Agent** (Port 8006) - Meta-agent for creating new aFDOs
6. **LLM Endpoint GPT-4 Agent** (Port 8007) - General-purpose LLM service
7. **LLM Endpoint GPT-4-mini Agent** (Port 8008) - Cost-effective LLM service
8. **Scientific NL Handler Agent** (Port 8002) - Scientific query processor
9. **Wikipedia Agent** (Port 8010) - Wikipedia data source
10. **ArXiv Agent** (Port 8011) - Scientific papers from ArXiv
11. **OpenLibrary Agent** (Port 8012) - Book information
12. **LLM Consultant Agent** (Port 8014) - Dynamic workflow generation

### Key Operation Patterns

**Common Input Schema Pattern:**
```json
{
  "type": "object",
  "required": ["required_param"],
  "properties": {
    "required_param": {
      "type": "string",
      "description": "Clear description"
    },
    "optional_param": {
      "type": "string",
      "default": "value"
    }
  }
}
```

**Common Output Schema Pattern:**
```json
{
  "type": "object",
  "required": ["result", "processor"],
  "properties": {
    "result": {"type": "object"},
    "processor": {"type": "string"},
    "cost": {"type": "number"},
    "duration_ms": {"type": "number"}
  }
}
```

**Common Constraints:**
- `timeout_seconds`: Operation timeout
- `rate_limit`: Requests per minute
- `max_input_size`: Maximum input in bytes
- `max_retries`: Automatic retry attempts

### Operation Discovery

To discover which agents support specific operations:

```bash
# Query by operation
curl http://localhost:8000/market/agents/by_operation/extract_text

# Query by type
curl http://localhost:8000/market/agents/by_type/21.T11148/type-document-processor-v1
```

---

## Resources

- **FDO Specification:** https://fairdo.org/
- **DOIP Protocol:** https://www.dona.net/doipv2
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pydantic Docs:** https://docs.pydantic.dev/
- **OpenAI API:** https://platform.openai.com/docs/

---

**Document Version:** 2.0.0
**Last Verified:** 2026-02-15
**Maintainer:** aFDO Development Team
