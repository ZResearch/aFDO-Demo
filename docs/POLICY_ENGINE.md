# Policy Engine Framework

## Overview

The Policy Engine framework provides a clean separation between **policy (configuration/data)** and **engine (code)** for aFDO agent decision-making.

### Key Principle

```
Policy = Configuration (JSON) ← DATA
Engine = Interpreter (Python) ← CODE
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  aFDO Agent                                             │
│  ┌────────────────┐         ┌─────────────────────┐    │
│  │ Agent Code     │         │ Policy Engine       │    │
│  │                │────────>│ (Interpreter/       │    │
│  │ - Operations   │  reads  │  Executor)          │    │
│  │ - Capabilities │<────────│                     │    │
│  └────────────────┘ executes└─────────────────────┘    │
│         │                             │                 │
│         │                             │ loads           │
│         │                             ↓                 │
│         │                    ┌─────────────────┐        │
│         │                    │ Policy.json     │        │
│         │                    │ (DATA)          │        │
│         │                    │ - Rules         │        │
│         │                    │ - Conditions    │        │
│         │                    │ - Actions       │        │
│         │                    └─────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Policy Files (JSON)

Machine-readable configuration files that define agent behavior.

**Location:**
- Agent-specific: `agents/<agent_name>/policy.json`
- Default policies: `shared/policies/default_<type>_policy.json`

**Schema:** `shared/policy_schema.json`

### 2. Policy Engine (Python)

Interpreter that reads and executes policies.

**File:** `shared/policy_engine.py`

**Classes:**
- `PolicyEngine` - Main interpreter
- `PolicyDecision` - Result of policy evaluation
- `DecisionType` - Enum of possible decisions

### 3. Integration in aFDOBase

The policy engine is automatically loaded and used by all agents inheriting from `aFDOBase`.

**Methods:**
- `_load_policy_engine()` - Loads policy file
- `handle_operation_with_policy()` - Uses policy for decisions
- `_execute_policy_decision()` - Executes policy decisions

## Policy File Format

```json
{
  "policy_id": "unique_policy_id",
  "policy_version": "1.0.0",
  "description": "Human-readable description",
  "default_action": "handle_alone",

  "rules": [
    {
      "rule_id": "rule_01",
      "description": "Rule description",
      "priority": 10,
      "conditions": {
        "operation": ["op1", "op2"],
        "has_capability": true,
        "complexity": "simple",
        "parameter_count": {"operator": "<=", "value": 2},
        "budget_threshold": 0.5
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "Why this action",
        "parameters": {
          "registry_query": {
            "operations": ["helper_op"],
            "fallback_operations": ["fallback_op"]
          },
          "selection_criteria": "balanced"
        },
        "fallback": {
          "type": "handle_alone",
          "parameters": {}
        }
      }
    }
  ]
}
```

## Decision Types

1. **handle_alone** - Execute operation directly
2. **query_registry_for_helper** - Find and delegate to helper agent
3. **query_registry_for_planner** - Find and delegate to planning agent
4. **query_registry_for_coordinator** - Find and delegate to coordinator
5. **delegate_fully** - Full delegation (interface agents)
6. **collaborate** - Multi-agent collaboration (composite agents)
7. **escalate** - Escalate to higher authority
8. **custom** - Agent-specific custom action

## Condition Matching

Policies evaluate conditions to determine which rule applies:

- **operation** - Match operation name(s)
- **has_capability** - Whether agent can perform operation
- **complexity** - Task complexity (simple, moderate, complex, very_complex)
- **parameter_count** - Number of parameters with operator
- **budget_threshold** - Minimum budget required
- **custom** - Agent-specific conditions

## Agent Types and Default Policies

### Task Agents
Simple agents with specific capabilities.

**Default:** `default_task_policy.json`
- Handle operations within capabilities
- Delegate operations outside capabilities

**Examples:** PDF Parser, FAIR Assessor

### Composite Agents
Complex agents that coordinate multiple services.

**Default:** `default_composite_policy.json`
- Handle simple tasks alone
- Collaborate for moderate/complex tasks
- Use full marketplace for complex operations

**Examples:** Paper Analyzer, Research Coordinator

### Interface Agents
User-facing agents that route requests.

**Default:** `default_interface_policy.json`
- Handle greetings/simple UI operations
- Delegate user requests to appropriate agents

**Examples:** Chat UI

## Creating Custom Policies

### Step 1: Create Policy File

Create `agents/your_agent/policy.json`:

```json
{
  "policy_id": "your_agent_policy",
  "policy_version": "1.0.0",
  "description": "Policy for Your Agent",
  "default_action": "handle_alone",
  "rules": [
    {
      "rule_id": "rule_01",
      "priority": 10,
      "conditions": {
        "operation": ["your_operation"],
        "has_capability": true
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "Core capability"
      }
    }
  ]
}
```

### Step 2: Policy Engine Auto-Loads

The policy engine automatically:
1. Looks for `agents/your_agent/policy.json`
2. Falls back to default policy for agent type
3. Logs policy loading status

### Step 3: Test

```python
# Policy is automatically used when operations are called
result = await agent.handle_operation(
    operation="your_operation",
    caller_pid="test",
    parameters={"param": "value"}
)
```

## Benefits

### ✅ Separation of Concerns
- Policies are data (JSON)
- Engine is code (Python)
- Agents don't hardcode decision logic

### ✅ Flexibility
- Update policies without code changes
- Different agents can have different policies
- Easy to test different strategies

### ✅ Inspectability
- Policies are human-readable
- Clear reasoning for decisions
- Audit trail of decision-making

### ✅ Reusability
- Share policies between agents
- Version control policies separately
- Store policies in registry

### ✅ Dynamic Updates
- Policies can be updated at runtime
- Agents can evolve their behavior
- A/B testing different policies

## Example Policies

### Simple Task Agent (PDF Parser)

```json
{
  "policy_id": "pdf_parser_policy",
  "default_action": "handle_alone",
  "rules": [
    {
      "rule_id": "core_operations",
      "priority": 10,
      "conditions": {
        "operation": ["parse_pdf", "extract_text"],
        "has_capability": true
      },
      "action": {
        "type": "handle_alone",
        "reasoning": "PDF operations are my core capability"
      }
    }
  ]
}
```

### Complex Composite Agent (Paper Analyzer)

```json
{
  "policy_id": "paper_analyzer_policy",
  "default_action": "collaborate",
  "rules": [
    {
      "rule_id": "full_analysis",
      "priority": 9,
      "conditions": {
        "operation": ["analyze_paper"],
        "complexity": "complex"
      },
      "action": {
        "type": "collaborate",
        "reasoning": "Full analysis requires multiple services",
        "parameters": {
          "discovery_strategy": "comprehensive",
          "planning_mode": "adaptive",
          "required_services": ["pdf_parser", "fair_assessor"]
        }
      }
    }
  ]
}
```

## Testing

### Validate Policy Schema

```python
import json
import jsonschema

with open('shared/policy_schema.json') as f:
    schema = json.load(f)

with open('agents/my_agent/policy.json') as f:
    policy = json.load(f)

jsonschema.validate(policy, schema)
```

### Test Policy Engine

```python
from shared.policy_engine import PolicyEngine, DecisionType

engine = PolicyEngine(
    agent_pid="test-agent",
    agent_capabilities=["operation1", "operation2"],
    policy_file="agents/my_agent/policy.json"
)

decision = await engine.decide(
    operation="operation1",
    parameters={"param": "value"},
    context={"budget": 1.0}
)

print(f"Decision: {decision.decision}")
print(f"Reasoning: {decision.reasoning}")
print(f"Rule: {decision.rule_id}")
```

## Future Enhancements

- **Policy Storage in Registry** - Store policies as FDOs
- **Policy Versioning** - Track policy changes over time
- **Policy Analytics** - Monitor which rules are used
- **Policy Learning** - Automatically improve policies based on outcomes
- **Policy Sharing** - Marketplace for proven policies
- **Policy Composition** - Combine multiple policies

## Troubleshooting

### Policy Not Loading

Check:
1. Policy file exists at correct location
2. JSON is valid
3. Policy matches schema
4. Agent logs show policy loading status

### Rules Not Matching

Check:
1. Condition operators are correct
2. Operation names match exactly
3. Priority order is correct
4. Complexity assessment is accurate

### Decision Not Executing

Check:
1. Decision type is valid
2. Required parameters are present
3. Fallback is defined for failures
4. Agent implements required methods

## References

- Policy Schema: `shared/policy_schema.json`
- Policy Engine: `shared/policy_engine.py`
- aFDOBase Integration: `shared/afdo_base.py`
- Default Policies: `shared/policies/`
- Example Policies: `agents/*/policy.json`
