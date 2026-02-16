"""
Workflow Protocol Implementation

Data-driven workflow execution for aFDOs with no hardcoded logic.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class WorkflowStatus(Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    ESTIMATED = "estimated"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Individual step execution status."""
    PENDING = "pending"
    READY = "ready"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Single step in workflow."""
    step_id: str
    name: str
    operation: str
    executor: str  # self|discover|specific
    input_mapping: Dict[str, str]

    description: str = ""
    executor_pid: Optional[str] = None
    discovery_query: Optional[Dict[str, Any]] = None
    depends_on: List[str] = field(default_factory=list)
    output_mapping: Optional[Dict[str, str]] = None
    on_failure: str = "abort"  # abort|continue|retry|fallback
    fallback_step: Optional[str] = None
    max_retries: int = 0
    timeout: Optional[int] = None
    cost_limit: Optional[float] = None

    # Runtime state
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    cost: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retries: int = 0


@dataclass
class Workflow:
    """Complete workflow definition."""
    workflow_id: str
    name: str
    created_by: str
    steps: List[WorkflowStep]

    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: WorkflowStatus = WorkflowStatus.DRAFT
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    cost_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "status": self.status.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "steps": [
                {
                    "step_id": s.step_id,
                    "name": s.name,
                    "description": s.description,
                    "operation": s.operation,
                    "executor": s.executor,
                    "executor_pid": s.executor_pid,
                    "discovery_query": s.discovery_query,
                    "depends_on": s.depends_on,
                    "input_mapping": s.input_mapping,
                    "output_mapping": s.output_mapping,
                    "on_failure": s.on_failure,
                    "fallback_step": s.fallback_step,
                    "max_retries": s.max_retries,
                    "timeout": s.timeout,
                    "cost_limit": s.cost_limit,
                    "status": s.status.value if hasattr(s.status, 'value') else s.status,
                    "result": s.result,
                    "error": s.error,
                    "cost": s.cost
                }
                for s in self.steps
            ],
            "execution_log": self.execution_log,
            "cost_summary": self.cost_summary
        }


class ExecutionContext:
    """Runtime context during workflow execution."""

    def __init__(self, workflow_id: str, workflow_input: Dict[str, Any], total_budget: float):
        self.workflow_id = workflow_id
        self.workflow_input = workflow_input
        self.step_results: Dict[str, Any] = {}  # step_id -> result
        self.budget = {
            "total": total_budget,
            "spent": 0.0,
            "remaining": total_budget
        }

    def get_value(self, path: str) -> Any:
        """
        Get value from context using path notation.

        Examples:
            'workflow.input.query' -> self.workflow_input['query']
            'step_01.result.data' -> self.step_results['step_01']['result']['data']
        """
        parts = path.split('.')

        if parts[0] == 'workflow' and parts[1] == 'input':
            # Navigate workflow input
            value = self.workflow_input
            for part in parts[2:]:
                value = value.get(part) if isinstance(value, dict) else getattr(value, part, None)
            return value

        elif parts[0] in self.step_results:
            # Navigate step results
            step_id = parts[0]
            value = self.step_results[step_id]
            for part in parts[1:]:
                value = value.get(part) if isinstance(value, dict) else getattr(value, part, None)
            return value

        else:
            raise ValueError(f"Invalid context path: {path}")

    def set_step_result(self, step_id: str, result: Any, cost: float, duration: float):
        """Store step result in context."""
        self.step_results[step_id] = {
            "result": result,
            "cost": cost,
            "duration": duration
        }

        # Update budget
        self.budget["spent"] += cost
        self.budget["remaining"] = self.budget["total"] - self.budget["spent"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow": {
                "id": self.workflow_id,
                "input": self.workflow_input
            },
            "steps": self.step_results,
            "budget": self.budget
        }


class WorkflowEngine:
    """
    Data-driven workflow execution engine.

    Executes workflows defined as data structures with no hardcoded logic.
    """

    def __init__(self, agent):
        """
        Initialize workflow engine for an agent.

        Args:
            agent: The aFDOBase instance using this engine
        """
        self.agent = agent
        self.logger = logging.getLogger(f"Workflow[{agent.pid}]")

        # Active workflows
        self.active_workflows: Dict[str, Workflow] = {}

        # Completed workflows (keep last 50)
        self.completed_workflows: List[Workflow] = []
        self.max_completed = 50

    async def execute_workflow(
        self,
        workflow: Workflow,
        workflow_input: Dict[str, Any],
        total_budget: float
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow: Workflow definition
            workflow_input: Input data for workflow
            total_budget: Total budget allocated

        Returns:
            Workflow output
        """
        self.logger.info(f"🚀 Starting workflow: {workflow.name} ({workflow.workflow_id})")

        # Initialize execution context
        context = ExecutionContext(workflow.workflow_id, workflow_input, total_budget)

        # Mark workflow as executing
        workflow.status = WorkflowStatus.EXECUTING
        self.active_workflows[workflow.workflow_id] = workflow

        try:
            # Execute steps in dependency order
            completed_steps = set()

            while len(completed_steps) < len(workflow.steps):
                # Find steps that are ready to execute
                ready_steps = self._find_ready_steps(workflow.steps, completed_steps)

                if not ready_steps:
                    # Check if we're stuck
                    pending_steps = [s for s in workflow.steps if s.step_id not in completed_steps]
                    if pending_steps:
                        raise RuntimeError(
                            f"Workflow stuck: {len(pending_steps)} steps pending but none ready. "
                            f"Possible circular dependency."
                        )
                    break

                # Execute ready steps (could be parallelized)
                for step in ready_steps:
                    try:
                        await self._execute_step(step, workflow, context)
                        completed_steps.add(step.step_id)

                    except Exception as step_error:
                        # Handle step failure according to on_failure policy
                        handled = await self._handle_step_failure(
                            step, step_error, workflow, context
                        )

                        if handled:
                            completed_steps.add(step.step_id)
                        else:
                            # Workflow failed
                            raise

            # Workflow completed successfully
            workflow.status = WorkflowStatus.COMPLETED

            # Calculate cost summary
            workflow.cost_summary = {
                "estimated": 0.0,  # Could track this during estimation phase
                "actual": context.budget["spent"],
                "breakdown": [
                    {
                        "step_id": step.step_id,
                        "step_name": step.name,
                        "cost": step.cost
                    }
                    for step in workflow.steps
                ]
            }

            self.logger.info(f"✅ Workflow completed: {workflow.name}")
            self.logger.info(f"   Total cost: ${context.budget['spent']:.3f}")

            # Extract output (could be based on output_schema)
            output = {
                "status": "success",
                "workflow_id": workflow.workflow_id,
                "steps": context.step_results,
                "cost": context.budget["spent"]
            }

            self._archive_workflow(workflow.workflow_id)

            return output

        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {workflow.name} - {e}")
            workflow.status = WorkflowStatus.FAILED

            self._archive_workflow(workflow.workflow_id)

            raise

    def _find_ready_steps(
        self,
        steps: List[WorkflowStep],
        completed_steps: set
    ) -> List[WorkflowStep]:
        """Find steps that are ready to execute."""
        ready = []

        for step in steps:
            # Skip if already completed
            if step.step_id in completed_steps:
                continue

            # Skip if already executing or failed
            if step.status in [StepStatus.EXECUTING, StepStatus.SUCCESS, StepStatus.FAILED]:
                continue

            # Check if all dependencies are completed
            dependencies_met = all(dep_id in completed_steps for dep_id in step.depends_on)

            if dependencies_met:
                ready.append(step)

        return ready

    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        context: ExecutionContext
    ):
        """Execute a single workflow step."""
        self.logger.info(f"  ▶️ Executing step: {step.name} ({step.step_id})")

        step.status = StepStatus.EXECUTING
        step.started_at = time.time()

        # 1. Resolve input parameters using input_mapping
        step_input = self._resolve_input_mapping(step.input_mapping, context)

        # 2. Determine executor
        executor_pid = await self._resolve_executor(step)

        # 3. Check budget
        if step.cost_limit and context.budget["remaining"] < step.cost_limit:
            raise RuntimeError(f"Insufficient budget for step {step.step_id}")

        # 4. Execute operation
        try:
            if executor_pid == self.agent.pid:
                # Execute locally
                result = await self._execute_local_operation(step.operation, step_input)
                cost = self.agent.cost
            else:
                # Execute remotely via aFDO call
                result = await self.agent.call_other_afdo(
                    target_pid=executor_pid,
                    operation=step.operation,
                    data=step_input
                )

                # Extract cost from result if available
                cost = result.get("_cost", self.agent.cost)
                result = result.get("result", result)

            # 5. Store result in context
            step.completed_at = time.time()
            duration = step.completed_at - step.started_at
            step.cost = cost
            step.result = result
            step.status = StepStatus.SUCCESS

            context.set_step_result(step.step_id, result, cost, duration)

            # 6. Log execution
            workflow.execution_log.append({
                "step_id": step.step_id,
                "executor_pid": executor_pid,
                "started_at": datetime.fromtimestamp(step.started_at).isoformat(),
                "completed_at": datetime.fromtimestamp(step.completed_at).isoformat(),
                "status": "success",
                "cost": cost,
                "result": result
            })

            self.logger.info(f"  ✅ Step completed: {step.name} (${cost:.3f})")

        except Exception as e:
            step.error = str(e)
            raise

    async def _handle_step_failure(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow: Workflow,
        context: ExecutionContext
    ) -> bool:
        """
        Handle step failure according to on_failure policy.

        Returns:
            True if handled (workflow continues), False if should fail
        """
        self.logger.warning(f"  ⚠️ Step failed: {step.name} - {error}")

        if step.on_failure == "retry" and step.retries < step.max_retries:
            # Retry
            step.retries += 1
            step.status = StepStatus.PENDING
            self.logger.info(f"  🔄 Retrying step {step.name} ({step.retries}/{step.max_retries})")
            await self._execute_step(step, workflow, context)
            return True

        elif step.on_failure == "continue":
            # Mark as skipped and continue
            step.status = StepStatus.SKIPPED
            self.logger.info(f"  ⏭️ Skipping step {step.name}")
            return True

        elif step.on_failure == "fallback" and step.fallback_step:
            # Execute fallback step
            fallback = next((s for s in workflow.steps if s.step_id == step.fallback_step), None)
            if fallback:
                self.logger.info(f"  🔀 Executing fallback: {fallback.name}")
                await self._execute_step(fallback, workflow, context)
                step.status = StepStatus.SKIPPED
                return True

        # Default: abort workflow
        step.status = StepStatus.FAILED
        return False

    def _resolve_input_mapping(
        self,
        input_mapping: Dict[str, str],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Resolve input parameters from context paths."""
        resolved = {}

        for param_name, context_path in input_mapping.items():
            try:
                resolved[param_name] = context.get_value(context_path)
            except Exception as e:
                raise ValueError(f"Failed to resolve input mapping '{param_name}': {context_path} - {e}")

        return resolved

    async def _resolve_executor(self, step: WorkflowStep) -> str:
        """Determine which aFDO should execute this step."""
        if step.executor == "self":
            return self.agent.pid

        elif step.executor == "specific":
            if not step.executor_pid:
                raise ValueError(f"Step {step.step_id} requires executor_pid")
            return step.executor_pid

        elif step.executor == "discover":
            if not step.discovery_query:
                raise ValueError(f"Step {step.step_id} requires discovery_query")

            # Discover suitable executor
            operation = step.discovery_query.get("operation")
            criteria = step.discovery_query.get("selection_criteria", "balanced")

            helpers = await self.agent.discover_by_operation(operation)

            if not helpers:
                raise RuntimeError(f"No helpers found for operation: {operation}")

            # Select based on criteria
            if criteria == "cheapest":
                selected = min(helpers, key=lambda h: h.get("cost", float('inf')))
            elif criteria == "fastest":
                selected = min(helpers, key=lambda h: h.get("queue_size", float('inf')))
            elif criteria == "best_reputation":
                selected = max(helpers, key=lambda h: h.get("reputation", 0))
            else:  # balanced
                selected = helpers[0]

            return selected["pid"]

        else:
            raise ValueError(f"Unknown executor type: {step.executor}")

    async def _execute_local_operation(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute operation locally on this agent."""
        if operation not in self.agent.operations:
            raise ValueError(f"Operation not supported: {operation}")

        # Call the operation handler
        handler = self.agent.operations[operation]
        return await handler(parameters)

    def _archive_workflow(self, workflow_id: str):
        """Archive completed workflow."""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows.pop(workflow_id)
            self.completed_workflows.append(workflow)

            # Keep only last N workflows
            if len(self.completed_workflows) > self.max_completed:
                self.completed_workflows = self.completed_workflows[-self.max_completed:]

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]

        for workflow in self.completed_workflows:
            if workflow.workflow_id == workflow_id:
                return workflow

        return None

    def create_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> Workflow:
        """
        Create a new workflow from definition.

        Args:
            name: Workflow name
            steps: List of step definitions
            input_schema: Input schema
            output_schema: Output schema
            description: Workflow description

        Returns:
            Created workflow
        """
        workflow_id = str(uuid.uuid4())[:8]

        # Parse steps
        workflow_steps = []
        for step_def in steps:
            step = WorkflowStep(
                step_id=step_def["step_id"],
                name=step_def["name"],
                operation=step_def["operation"],
                executor=step_def["executor"],
                input_mapping=step_def["input_mapping"],
                description=step_def.get("description", ""),
                executor_pid=step_def.get("executor_pid"),
                discovery_query=step_def.get("discovery_query"),
                depends_on=step_def.get("depends_on", []),
                output_mapping=step_def.get("output_mapping"),
                on_failure=step_def.get("on_failure", "abort"),
                fallback_step=step_def.get("fallback_step"),
                max_retries=step_def.get("max_retries", 0),
                timeout=step_def.get("timeout"),
                cost_limit=step_def.get("cost_limit")
            )
            workflow_steps.append(step)

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            created_by=self.agent.pid,
            steps=workflow_steps,
            input_schema=input_schema or {},
            output_schema=output_schema or {}
        )

        self.logger.info(f"📋 Created workflow: {name} ({workflow_id}) with {len(steps)} steps")

        return workflow
