# aFDO Protocol Implementation

This directory contains the core protocol implementations for the aFDO system.

## Overview

The protocol system enables:
1. **Cost Negotiation Protocol** - Recursive cost estimation and budget approval between aFDOs
2. **Workflow Engine** - Data-driven workflow execution with no hardcoded logic

## Files

### Schemas (JSON)
- `negotiation_protocol.json` - Complete protocol specification for cost negotiation
- `workflow_protocol.json` - Complete protocol specification for workflow execution

### Implementations (Python)
- `negotiation.py` - NegotiationProtocol implementation
- `workflow.py` - WorkflowEngine implementation

## Usage

### 1. Cost Negotiation Protocol

The negotiation protocol enables recursive cost estimation with budget approval:

```python
from shared.protocols import NegotiationProtocol

# In your aFDO agent
class MyAgent(aFDOBase):
    def __init__(self, ...):
        super().__init__(...)
        self.negotiation = NegotiationProtocol(self)

    async def request_service_with_negotiation(self, target_pid, operation, params):
        # Phase 1: Request estimate
        estimate = await self.negotiation.request_estimate(
            target_pid=target_pid,
            operation=operation,
            parameters=params,
            budget_limit=1.0,
            quality_preference="balanced"
        )

        print(f"Estimated cost: ${estimate.estimated_cost:.3f}")
        print(f"Confidence: {estimate.confidence:.0%}")
        print(f"Breakdown: {len(estimate.breakdown)} components")

        # Phase 2: Approve estimate
        session_id = list(self.negotiation.active_sessions.keys())[0]
        execution_id = await self.negotiation.approve_estimate(
            session_id=session_id,
            approved=True,
            allocated_budget=estimate.estimated_cost
        )

        # Phase 3: Execute with budget
        result = await self.negotiation.execute_with_budget(
            session_id=session_id,
            operation=operation,
            parameters=params
        )

        print(f"Actual cost: ${result.actual_cost:.3f}")
        return result.result
```

#### Server-Side (Providing Estimates)

```python
async def handle_estimate_request(self, caller_pid, operation, parameters):
    """Called when another agent requests estimate."""
    estimate = await self.negotiation.provide_estimate(
        caller_pid=caller_pid,
        operation=operation,
        parameters=parameters,
        budget_limit=None
    )
    return estimate.to_dict()
```

### 2. Workflow Engine

The workflow engine executes data-driven workflows:

```python
from shared.protocols import WorkflowEngine, Workflow

# In your aFDO agent
class MyAgent(aFDOBase):
    def __init__(self, ...):
        super().__init__(...)
        self.workflow_engine = WorkflowEngine(self)

    async def execute_research_workflow(self, query):
        # Create workflow definition (data-driven, no hardcoded logic)
        workflow = self.workflow_engine.create_workflow(
            name="Research Paper Workflow",
            description="Find and analyze papers on a topic",
            steps=[
                {
                    "step_id": "search",
                    "name": "Search Papers",
                    "operation": "search_papers",
                    "executor": "discover",
                    "discovery_query": {
                        "operation": "search_papers",
                        "selection_criteria": "cheapest"
                    },
                    "depends_on": [],
                    "input_mapping": {
                        "query": "workflow.input.query",
                        "limit": "workflow.input.limit"
                    },
                    "on_failure": "abort"
                },
                {
                    "step_id": "analyze",
                    "name": "Analyze Papers",
                    "operation": "analyze_paper",
                    "executor": "discover",
                    "discovery_query": {
                        "operation": "analyze_paper",
                        "selection_criteria": "best_reputation"
                    },
                    "depends_on": ["search"],
                    "input_mapping": {
                        "papers": "search.result.results"
                    },
                    "on_failure": "retry",
                    "max_retries": 2
                },
                {
                    "step_id": "summarize",
                    "name": "Summarize Results",
                    "operation": "summarize",
                    "executor": "self",
                    "depends_on": ["analyze"],
                    "input_mapping": {
                        "analyses": "analyze.result"
                    },
                    "on_failure": "abort"
                }
            ],
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                }
            }
        )

        # Execute workflow
        result = await self.workflow_engine.execute_workflow(
            workflow=workflow,
            workflow_input={"query": query, "limit": 5},
            total_budget=2.0
        )

        print(f"Workflow completed with cost: ${result['cost']:.3f}")
        return result
```

## Key Features

### Negotiation Protocol

1. **Recursive Estimation** - Agents can request estimates from helpers, creating a cost breakdown tree
2. **Budget Approval** - Explicit approval step before execution
3. **Cost Escalation** - Handle budget overruns during execution
4. **State Machine** - Clear state transitions (idle → estimating → awaiting_approval → approved → executing → completed)
5. **Session Tracking** - Complete message history for each negotiation

### Workflow Engine

1. **Data-Driven** - Workflows defined as data structures, not code
2. **Dependency Management** - Steps execute in correct order based on dependencies
3. **Executor Discovery** - Dynamically discover agents to execute steps
4. **Error Handling** - Configurable failure policies (abort/continue/retry/fallback)
5. **Budget Tracking** - Track costs across workflow execution
6. **Context Management** - Share data between steps using path notation

## Integration with aFDOBase

To integrate these protocols into an aFDO agent:

```python
from shared.afdo_base import aFDOBase
from shared.protocols import NegotiationProtocol, WorkflowEngine

class MyAgent(aFDOBase):
    def __init__(self, pid, name, ...):
        super().__init__(pid, name, ...)

        # Add protocols
        self.negotiation = NegotiationProtocol(self)
        self.workflow_engine = WorkflowEngine(self)

    async def handle_operation(self, operation, data):
        # Handle special protocol operations
        if operation.startswith("__estimate_"):
            # Extract actual operation
            actual_op = operation[11:]  # Remove "__estimate_" prefix
            return await self._handle_estimate_request(actual_op, data)

        elif operation == "__approval_decision":
            return await self._handle_approval(data)

        # Handle normal operations
        return await super().handle_operation(operation, data)

    async def _handle_estimate_request(self, operation, data):
        estimate = await self.negotiation.provide_estimate(
            caller_pid=data["caller_pid"],
            operation=operation,
            parameters=data["parameters"],
            budget_limit=data.get("budget_limit")
        )
        return estimate.to_dict()

    async def _handle_approval(self, data):
        # Store approval for tracking
        return {"status": "acknowledged"}
```

## Protocol Schemas

The JSON schema files provide machine-readable specifications:

- **Message Types** - All message formats for the protocol
- **State Machines** - Valid state transitions
- **Field Specifications** - Required/optional fields with types

These schemas can be used for:
- Validation
- Code generation
- Documentation
- Interoperability with other systems

## Examples

See the integration tests in `tests/test_protocols.py` for complete examples.

## Future Enhancements

Potential improvements:
1. Workflow estimation phase (estimate before execution)
2. Parallel step execution
3. Conditional branching in workflows
4. Sub-workflow support
5. Workflow templates and composition
6. Advanced negotiation strategies
7. Budget forecasting and optimization
