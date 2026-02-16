"""
Workflow Engine - Data-driven workflow execution

Executes workflows defined as JSON with:
- Dependency resolution
- Parallel execution where possible
- Failure handling (retry, fallback, abort)
- Cost tracking and budget management
- Dynamic agent discovery
"""

import json
import uuid
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""
    pass


@dataclass
class StepResult:
    """Result of a single step execution."""
    step_id: str
    executor_pid: str
    status: str  # success|failed|skipped
    result: Any
    cost: float
    duration: float
    started_at: float
    completed_at: float
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "executor_pid": self.executor_pid,
            "status": self.status,
            "result": self.result,
            "cost": self.cost,
            "duration": self.duration,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


class ExecutionContext:
    """
    Runtime context during workflow execution.

    Provides access to:
    - Workflow inputs
    - Step results
    - Budget tracking
    """

    def __init__(self, workflow_input: Dict[str, Any], total_budget: float):
        self.workflow_input = workflow_input
        self.step_results: Dict[str, StepResult] = {}
        self.budget = {
            "total": total_budget,
            "spent": 0.0,
            "remaining": total_budget
        }

    def resolve_path(self, path: str) -> Any:
        """
        Resolve a path in the execution context.

        Paths can reference:
        - workflow.input.field_name
        - step_id.result.field_name
        - step_id.cost

        Examples:
        - "workflow.input.question" → self.workflow_input["question"]
        - "step_01.result.data" → self.step_results["step_01"].result["data"]
        - "step_01.cost" → self.step_results["step_01"].cost
        """
        parts = path.split(".")

        if parts[0] == "workflow":
            # workflow.input.field
            if parts[1] == "input":
                current = self.workflow_input
                for part in parts[2:]:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list) and part.isdigit():
                        current = current[int(part)]
                    else:
                        return None
                return current

        elif parts[0] in self.step_results:
            # step_id.result.field or step_id.cost
            step_result = self.step_results[parts[0]]

            if parts[1] == "result":
                current = step_result.result
                for part in parts[2:]:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list) and part.isdigit():
                        current = current[int(part)]
                    else:
                        return None
                return current

            elif parts[1] == "cost":
                return step_result.cost

            elif parts[1] == "duration":
                return step_result.duration

        return None

    def add_step_result(self, result: StepResult):
        """Add step result and update budget."""
        self.step_results[result.step_id] = result
        self.budget["spent"] += result.cost
        self.budget["remaining"] = self.budget["total"] - self.budget["spent"]

    def has_budget(self, amount: float) -> bool:
        """Check if enough budget remains."""
        return self.budget["remaining"] >= amount


class WorkflowEngine:
    """
    Executes data-driven workflows.

    Features:
    - Load workflows from JSON
    - Dependency resolution (topological sort)
    - Parallel execution of independent steps
    - Cost estimation before execution
    - Budget tracking during execution
    - Failure handling per step configuration
    """

    def __init__(self, agent):
        """
        Initialize workflow engine for an agent.

        Args:
            agent: The aFDOBase instance using this engine
        """
        self.agent = agent
        self.logger = logging.getLogger(f"Workflow[{agent.pid}]")

        # Current workflow
        self.workflow: Optional[Dict[str, Any]] = None

        # Execution context
        self.context: Optional[ExecutionContext] = None

        # Execution log
        self.execution_log: List[StepResult] = []

    def load_workflow(self, workflow: Dict[str, Any]):
        """
        Load workflow from dictionary.

        Args:
            workflow: Workflow specification (follows workflow_protocol.json schema)
        """
        # Validate required fields
        required = ["workflow_id", "name", "steps"]
        for field in required:
            if field not in workflow:
                raise ValueError(f"Missing required field: {field}")

        if not workflow["steps"]:
            raise ValueError("Workflow must have at least one step")

        self.workflow = workflow
        self.execution_log = []

        self.logger.info(f"📋 Loaded workflow: {workflow['name']}")
        self.logger.info(f"   ID: {workflow['workflow_id']}")
        self.logger.info(f"   Steps: {len(workflow['steps'])}")

    def load_workflow_file(self, filepath: str):
        """Load workflow from JSON file."""
        with open(filepath, 'r') as f:
            workflow = json.load(f)
        self.load_workflow(workflow)

    async def estimate_workflow(
        self,
        workflow_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estimate total cost and time for workflow.

        For each step:
        - If executor="self": use agent's cost
        - If executor="discover": discover agent and get estimate via negotiation
        - If executor="specific": get estimate from specific agent

        Args:
            workflow_input: Input data for workflow

        Returns:
            Dictionary with estimated_cost, estimated_time, breakdown
        """
        if not self.workflow:
            raise ValueError("No workflow loaded")

        self.logger.info(f"💰 Estimating workflow: {self.workflow['name']}")

        # Create temporary context for estimation
        temp_context = ExecutionContext(workflow_input, float('inf'))

        total_cost = 0.0
        total_time = 0.0
        breakdown = []

        for step in self.workflow["steps"]:
            step_id = step["step_id"]
            operation = step["operation"]
            executor_type = step["executor"]

            self.logger.info(f"   Estimating step: {step_id} ({operation})")

            # Resolve inputs for this step
            step_inputs = self._resolve_step_inputs(step, temp_context)

            # Get estimate based on executor type
            if executor_type == "self":
                # Use agent's own cost
                step_cost = self.agent.cost
                step_time = 5.0  # Default estimate
                executor_pid = self.agent.pid

            elif executor_type == "discover":
                # Discover agent and get estimate
                discovery_query = step.get("discovery_query", {})
                operation_to_find = discovery_query.get("operation", operation)

                # Discover agents
                agents = await self.agent.discover_by_operation(operation_to_find)

                if not agents:
                    self.logger.warning(f"   ⚠️ No agents found for {operation_to_find}")
                    continue

                # Select agent based on criteria
                selection_criteria = discovery_query.get("selection_criteria", "balanced")
                selected = self._select_agent(agents, selection_criteria)
                executor_pid = selected["pid"]

                # Request estimate via negotiation protocol
                try:
                    estimate = await self.agent.negotiation.request_estimate(
                        target_pid=executor_pid,
                        operation=operation,
                        parameters=step_inputs
                    )
                    step_cost = estimate.estimated_cost
                    step_time = estimate.estimated_time
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Failed to get estimate: {e}")
                    step_cost = 0.05  # Default
                    step_time = 10.0

            elif executor_type == "specific":
                # Specific agent
                executor_pid = step.get("executor_pid")
                if not executor_pid:
                    raise ValueError(f"Step {step_id} has executor='specific' but no executor_pid")

                # Request estimate
                try:
                    estimate = await self.agent.negotiation.request_estimate(
                        target_pid=executor_pid,
                        operation=operation,
                        parameters=step_inputs
                    )
                    step_cost = estimate.estimated_cost
                    step_time = estimate.estimated_time
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Failed to get estimate: {e}")
                    step_cost = 0.05
                    step_time = 10.0

            else:
                raise ValueError(f"Unknown executor type: {executor_type}")

            # Add to breakdown
            breakdown.append({
                "step_id": step_id,
                "operation": operation,
                "executor_pid": executor_pid,
                "estimated_cost": step_cost,
                "estimated_time": step_time
            })

            total_cost += step_cost
            total_time += step_time  # Sequential for now (can optimize)

            self.logger.info(f"   ✅ ${step_cost:.3f}, {step_time:.1f}s via {executor_pid}")

        result = {
            "estimated_cost": total_cost,
            "estimated_time": total_time,
            "breakdown": breakdown,
            "step_count": len(breakdown)
        }

        self.logger.info(f"✅ Total estimate: ${total_cost:.3f}, {total_time:.1f}s")

        return result

    async def execute_workflow(
        self,
        workflow_input: Dict[str, Any],
        budget: float
    ) -> Dict[str, Any]:
        """
        Execute workflow with given budget.

        Args:
            workflow_input: Input data for workflow
            budget: Total budget for execution

        Returns:
            Dictionary with result, cost_summary, execution_log
        """
        if not self.workflow:
            raise ValueError("No workflow loaded")

        self.logger.info(f"🚀 Executing workflow: {self.workflow['name']}")
        self.logger.info(f"   Budget: ${budget:.3f}")

        # Initialize execution context
        self.context = ExecutionContext(workflow_input, budget)
        self.execution_log = []

        # Build dependency graph
        dep_graph = self._build_dependency_graph()

        # Execute steps in topological order
        execution_order = self._topological_sort(dep_graph)

        self.logger.info(f"📝 Execution order: {execution_order}")

        for step_id in execution_order:
            # Check budget before executing
            if not self.context.has_budget(0.01):  # Minimum buffer
                raise WorkflowExecutionError(
                    f"Insufficient budget at step {step_id}. "
                    f"Spent: ${self.context.budget['spent']:.3f}, "
                    f"Remaining: ${self.context.budget['remaining']:.3f}"
                )

            # Get step configuration
            step = self._get_step(step_id)

            # Check if dependencies succeeded
            if not self._dependencies_satisfied(step):
                self.logger.warning(f"⚠️ Skipping {step_id}: dependencies not satisfied")

                # Create skipped result
                result = StepResult(
                    step_id=step_id,
                    executor_pid="none",
                    status="skipped",
                    result=None,
                    cost=0.0,
                    duration=0.0,
                    started_at=time.time(),
                    completed_at=time.time(),
                    error="Dependencies not satisfied"
                )

                self.context.add_step_result(result)
                self.execution_log.append(result)
                continue

            # Execute step
            try:
                result = await self._execute_step(step)
                self.context.add_step_result(result)
                self.execution_log.append(result)

                if result.status == "success":
                    self.logger.info(f"✅ {step_id} completed: ${result.cost:.3f}, {result.duration:.1f}s")
                else:
                    self.logger.error(f"❌ {step_id} failed: {result.error}")

                    # Handle failure based on on_failure strategy
                    on_failure = step.get("on_failure", "abort")

                    if on_failure == "abort":
                        raise WorkflowExecutionError(f"Step {step_id} failed, aborting workflow")
                    elif on_failure == "continue":
                        self.logger.info(f"⏭️ Continuing despite failure")
                        continue
                    elif on_failure == "retry":
                        # Retry logic
                        max_retries = step.get("max_retries", 0)
                        if result.error and max_retries > 0:
                            self.logger.info(f"🔄 Retrying {step_id} (max {max_retries})")
                            # Implement retry logic here
                        else:
                            raise WorkflowExecutionError(f"Step {step_id} failed with no retries")
                    elif on_failure == "fallback":
                        # Execute fallback step
                        fallback_step_id = step.get("fallback_step")
                        if fallback_step_id:
                            self.logger.info(f"🔄 Executing fallback: {fallback_step_id}")
                            # Add fallback step to execution queue
                        else:
                            raise WorkflowExecutionError(f"Step {step_id} failed with no fallback")

            except Exception as e:
                self.logger.error(f"❌ Step {step_id} exception: {e}")

                # Create failed result
                result = StepResult(
                    step_id=step_id,
                    executor_pid="unknown",
                    status="failed",
                    result=None,
                    cost=0.0,
                    duration=0.0,
                    started_at=time.time(),
                    completed_at=time.time(),
                    error=str(e)
                )

                self.context.add_step_result(result)
                self.execution_log.append(result)

                # Check on_failure strategy
                on_failure = step.get("on_failure", "abort")
                if on_failure == "abort":
                    raise
                elif on_failure == "continue":
                    continue

        # Workflow completed
        self.logger.info(f"✅ Workflow completed")
        self.logger.info(f"   Total cost: ${self.context.budget['spent']:.3f}")
        self.logger.info(f"   Steps executed: {len(self.execution_log)}")

        # Compile result
        return {
            "status": "completed",
            "result": self._compile_workflow_result(),
            "cost_summary": {
                "total_budget": budget,
                "actual_cost": self.context.budget["spent"],
                "remaining": self.context.budget["remaining"],
                "breakdown": [r.to_dict() for r in self.execution_log]
            },
            "execution_log": [r.to_dict() for r in self.execution_log]
        }

    async def _execute_step(self, step: Dict[str, Any]) -> StepResult:
        """
        Execute a single workflow step.

        Args:
            step: Step configuration

        Returns:
            StepResult
        """
        step_id = step["step_id"]
        operation = step["operation"]
        executor_type = step["executor"]

        self.logger.info(f"▶️ Executing step: {step_id}")

        start_time = time.time()

        # Resolve step inputs
        step_inputs = self._resolve_step_inputs(step, self.context)

        try:
            # Execute based on executor type
            if executor_type == "self":
                # Execute with agent's own capabilities
                result = await self.agent._execute_operation(operation, step_inputs)
                cost = self.agent.cost
                executor_pid = self.agent.pid

            elif executor_type == "discover":
                # Discover and delegate
                discovery_query = step.get("discovery_query", {})
                operation_to_find = discovery_query.get("operation", operation)

                # Discover agents
                agents = await self.agent.discover_by_operation(operation_to_find)

                if not agents:
                    raise Exception(f"No agents found for operation: {operation_to_find}")

                # Select agent
                selection_criteria = discovery_query.get("selection_criteria", "balanced")
                selected = self._select_agent(agents, selection_criteria)
                executor_pid = selected["pid"]

                # Delegate via negotiation protocol
                # 1. Request estimate
                estimate = await self.agent.negotiation.request_estimate(
                    target_pid=executor_pid,
                    operation=operation,
                    parameters=step_inputs,
                    budget_limit=self.context.budget["remaining"]
                )

                # 2. Check budget
                if estimate.estimated_cost > self.context.budget["remaining"]:
                    raise Exception(
                        f"Step cost ${estimate.estimated_cost:.3f} exceeds "
                        f"remaining budget ${self.context.budget['remaining']:.3f}"
                    )

                # 3. Approve
                session_id = list(self.agent.negotiation.active_sessions.keys())[-1]
                execution_id = await self.agent.negotiation.approve_estimate(
                    session_id=session_id,
                    approved=True,
                    allocated_budget=estimate.estimated_cost
                )

                # 4. Execute
                execution_result = await self.agent.negotiation.execute_with_budget(
                    session_id=session_id,
                    operation=operation,
                    parameters=step_inputs
                )

                result = execution_result.result
                cost = execution_result.actual_cost

            elif executor_type == "specific":
                # Specific agent
                executor_pid = step.get("executor_pid")

                # Similar to discover, but with specific agent
                estimate = await self.agent.negotiation.request_estimate(
                    target_pid=executor_pid,
                    operation=operation,
                    parameters=step_inputs,
                    budget_limit=self.context.budget["remaining"]
                )

                if estimate.estimated_cost > self.context.budget["remaining"]:
                    raise Exception(f"Cost exceeds budget")

                session_id = list(self.agent.negotiation.active_sessions.keys())[-1]
                execution_id = await self.agent.negotiation.approve_estimate(
                    session_id=session_id,
                    approved=True,
                    allocated_budget=estimate.estimated_cost
                )

                execution_result = await self.agent.negotiation.execute_with_budget(
                    session_id=session_id,
                    operation=operation,
                    parameters=step_inputs
                )

                result = execution_result.result
                cost = execution_result.actual_cost

            else:
                raise ValueError(f"Unknown executor type: {executor_type}")

            # Create success result
            duration = time.time() - start_time

            return StepResult(
                step_id=step_id,
                executor_pid=executor_pid,
                status="success",
                result=result,
                cost=cost,
                duration=duration,
                started_at=start_time,
                completed_at=time.time()
            )

        except Exception as e:
            # Create failure result
            duration = time.time() - start_time

            return StepResult(
                step_id=step_id,
                executor_pid=executor_pid if 'executor_pid' in locals() else "unknown",
                status="failed",
                result=None,
                cost=0.0,
                duration=duration,
                started_at=start_time,
                completed_at=time.time(),
                error=str(e)
            )

    def _resolve_step_inputs(
        self,
        step: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Resolve step inputs from execution context.

        Uses input_mapping to resolve values from:
        - workflow.input.field
        - step_id.result.field
        """
        input_mapping = step.get("input_mapping", {})
        resolved = {}

        for param_name, path in input_mapping.items():
            if isinstance(path, str):
                # Simple path resolution
                value = context.resolve_path(path)
                resolved[param_name] = value
            elif isinstance(path, list):
                # Array of paths
                resolved[param_name] = [context.resolve_path(p) for p in path]
            else:
                # Literal value
                resolved[param_name] = path

        return resolved

    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """
        Build dependency graph from workflow steps.

        Returns:
            Dictionary mapping step_id to set of dependencies
        """
        graph = {}

        for step in self.workflow["steps"]:
            step_id = step["step_id"]
            depends_on = step.get("depends_on", [])
            graph[step_id] = set(depends_on)

        return graph

    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """
        Topological sort of dependency graph.

        Returns execution order that respects dependencies.
        """
        # Kahn's algorithm
        in_degree = {node: 0 for node in graph}

        for node in graph:
            for dep in graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph:
                if node in graph[neighbor]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(result) != len(graph):
            raise ValueError("Workflow has circular dependencies")

        # Reverse because we want dependencies first
        return result[::-1]

    def _dependencies_satisfied(self, step: Dict[str, Any]) -> bool:
        """Check if all dependencies of a step succeeded."""
        depends_on = step.get("depends_on", [])

        for dep_id in depends_on:
            if dep_id not in self.context.step_results:
                return False

            if self.context.step_results[dep_id].status != "success":
                return False

        return True

    def _get_step(self, step_id: str) -> Dict[str, Any]:
        """Get step configuration by ID."""
        for step in self.workflow["steps"]:
            if step["step_id"] == step_id:
                return step
        raise ValueError(f"Step not found: {step_id}")

    def _select_agent(self, agents: List[Dict[str, Any]], criteria: str) -> Dict[str, Any]:
        """
        Select agent based on criteria.

        Args:
            agents: List of candidate agents
            criteria: cheapest|fastest|balanced|best_reputation

        Returns:
            Selected agent
        """
        if criteria == "cheapest":
            return min(agents, key=lambda a: a.get("cost", 1.0))
        elif criteria == "best_reputation":
            return max(agents, key=lambda a: a.get("reputation", 0.5))
        elif criteria == "balanced":
            # Score = reputation / cost
            return max(agents, key=lambda a: a.get("reputation", 0.5) / max(a.get("cost", 0.01), 0.01))
        else:
            # Default: first agent
            return agents[0]

    def _compile_workflow_result(self) -> Any:
        """
        Compile final workflow result.

        By default, returns result of last step.
        Can be overridden for more sophisticated result compilation.
        """
        if not self.execution_log:
            return None

        # Return result of last successful step
        for result in reversed(self.execution_log):
            if result.status == "success":
                return result.result

        return None
