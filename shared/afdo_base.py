"""Base class for all Autonomous FAIR Digital Objects (aFDOs)."""

import sys
import time
import uuid
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
import uvicorn
import asyncio
import httpx

from .utils import generate_pid, current_timestamp, log_activity
from .doip_client import DOIPClient
from .logging_config import get_logger
from .job_tracker import get_job_tracker

# Marketplace imports
from .budget_manager import BudgetManager
from .queue_manager import QueueManager, QueuedRequest
from .reputation_manager import ReputationManager
from .negotiation import Quote, QuoteRequest, NegotiationResult, create_quote_expiry, FlexibleStrategy
from .selection_policy import SelectionPolicy, BalancedPolicy, get_policy_by_name

# FDO schemas
from .fdo_schemas import SELF_DESCRIPTION_SCHEMA
import jsonschema

# Policy Engine
from .policy_engine import PolicyEngine, PolicyDecision, DecisionType

# Schema-Driven Input Preparation (Task 30)
from .input_preparation import SchemaBasedInputPreparator

# Execution Trace & Provenance (Task 32)
from .execution_trace import ExecutionTracer
import os


class aFDOBase(ABC):
    """
    Abstract base class for all aFDOs.

    All aFDO agents inherit from this class to get:
    - Automatic registration with FDO Registry
    - DOIP communication capabilities
    - Activity logging
    - Discovery methods
    - FastAPI server setup
    """

    def __init__(
        self,
        name: str,
        fdo_type: str,
        operations: List[str],
        port: int,
        registry_url: str = "http://localhost:8000",
        cost: float = 0.0,
        has_llm: bool = False,
        **kwargs
    ):
        """
        Initialize aFDO.

        Args:
            name: Human-readable name
            fdo_type: FDO type identifier
            operations: List of operation names this aFDO provides
            port: Port number for this aFDO's server
            registry_url: URL of FDO Registry
            cost: Cost per operation
            has_llm: Whether this aFDO has built-in LLM
            **kwargs: Additional kernel attributes
        """
        # Core attributes - use deterministic PIDs based on agent name
        agent_suffix = name.lower().replace(' ', '-')
        self.pid = generate_pid(suffix=agent_suffix)
        self.name = name
        self.fdo_type = fdo_type
        self.fdo_profile = "21.T11148/profile-ai-agent-v1"

        # Add standard operations that all agents support (Task 30)
        if "get_description" not in operations:
            operations = operations + ["get_description"]
        self.operations = operations

        self.port = port
        self.base_url = f"http://localhost:{port}"

        # Metadata
        self.metadata_pid = generate_pid(suffix=f"metadata-{agent_suffix}")

        # Activity log (structured for outgoing/incoming tracking)
        self.activity_log: List[Dict[str, Any]] = []
        self._activity_log = []  # Outgoing calls
        self._activity_log_incoming = []  # Incoming calls
        self._sync_scheduled = False

        # Kernel attributes
        self.kernel_attributes = {
            "name": name,  # Human-readable name for display
            "port": port,  # Include port for discovery
            "reputation": 0.85,  # Default reputation
            "cost": cost,
            "status": "active",
            "has_llm": has_llm,
            **kwargs
        }

        # Registry client
        self.registry_url = registry_url
        self.registry_client = DOIPClient(registry_url)

        # Marketplace components
        self.queue_manager = QueueManager(
            base_cost=cost,
            max_queue_size=kwargs.get('max_queue_size', 10),
            surge_factor=kwargs.get('surge_factor', 2.0)
        )
        self.reputation_manager = ReputationManager(self.pid)
        self.negotiation_strategy = FlexibleStrategy(
            base_price=cost,
            minimum_price=cost * 0.7  # 30% discount maximum
        )

        # Selection policy (configurable)
        policy_name = kwargs.get('selection_policy', 'balanced')
        if isinstance(policy_name, str):
            self.selection_policy = get_policy_by_name(policy_name)
        else:
            self.selection_policy = policy_name  # Already a policy instance

        # Heartbeat task
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.start_time = time.time()

        # FastAPI app (created later)
        self.app: Optional[FastAPI] = None

        # Centralized logger
        self.logger = get_logger()

        # Job tracking
        self.current_job_id = None

        # Policy Engine (loaded after logger is initialized)
        self.policy_engine: Optional[PolicyEngine] = None

        # Schema-Driven Input Preparation (Task 30)
        self.has_llm = has_llm
        self.input_preparator = SchemaBasedInputPreparator(has_llm=has_llm)

        # Execution Trace & Provenance (Task 32)
        self.trace_directory = os.getenv("TRACE_DIRECTORY", "/tmp/afdo_traces")
        self.current_tracer: Optional[ExecutionTracer] = None

    async def _register_operations_in_registry(self) -> List[str]:
        """
        Register this aFDO's operations in the operation registry.

        Extracts rich descriptions from agent's self-description and stores them
        in operation records for semantic discovery.

        Returns:
            List of operation PIDs
        """
        operation_pids = []

        # Get self-description to extract operation details
        self_description = self.get_self_description()
        capabilities = self_description.get('capabilities', {})

        for op_name in self.operations:
            # Extract operation details from capabilities
            op_spec = capabilities.get(op_name, {})
            op_description = op_spec.get('description', f"Operation: {op_name}")
            input_schema = op_spec.get('input_schema', {})
            output_schema = op_spec.get('output_schema', {})

            # Check if operation already registered
            try:
                existing = await self.registry_client.search_operations(name=op_name)
                if existing:
                    # Operation already registered - UPDATE it with rich description
                    op_pid = existing[0].get('pid')

                    operation = {
                        "pid": op_pid,
                        "name": op_name,
                        "description": op_description,  # Rich semantic description
                        "input_schema": input_schema,
                        "output_schema": output_schema,
                        "created_at": existing[0].get('created_at', current_timestamp())
                    }

                    await self.registry_client.update_operation(op_pid, operation)
                    print(f"  ✅ Updated operation: {op_name} ({op_pid})")
                    operation_pids.append(op_pid)
                    continue
            except:
                pass

            # Register new operation with rich description from capabilities
            try:
                op_pid = generate_pid() + f"-op-{op_name.replace('_', '-')}"

                operation = {
                    "pid": op_pid,
                    "name": op_name,
                    "description": op_description,  # Rich semantic description
                    "input_schema": input_schema,
                    "output_schema": output_schema,
                    "created_at": current_timestamp()
                }

                await self.registry_client.create_operation(operation)
                print(f"  ✅ Registered operation: {op_name} ({op_pid})")
                operation_pids.append(op_pid)
            except Exception as e:
                # If already exists or other error, try to look it up
                print(f"  ⚠️  Could not register operation {op_name}: {e}")
                try:
                    existing = await self.registry_client.search_operations(name=op_name)
                    if existing:
                        op_pid = existing[0].get('pid')
                        operation_pids.append(op_pid)
                except:
                    # Fall back to operation name if can't get PID
                    operation_pids.append(op_name)

        return operation_pids

    async def register_self(self) -> bool:
        """
        Register this aFDO with the FDO Registry.

        Returns:
            True if registration successful
        """
        try:
            self.logger.info(self.name, "Starting registration process...")

            # Register operations first
            print(f"📝 Registering operations...")
            operation_pids = await self._register_operations_in_registry()
            self.logger.debug(self.name, f"Registered {len(operation_pids)} operations")

            # Create metadata record with comprehensive FDO-compliant content
            metadata = {
                "pid": self.metadata_pid,
                "associated_fdo": self.pid,
                "content": self.get_comprehensive_metadata(),
                "created_at": current_timestamp(),
                "updated_at": current_timestamp(),
                "schema_version": "1.0.0",
                "created_by": self.pid,
                "provenance": {
                    "registration_method": "self_registration",
                    "framework": "aFDO_marketplace_v1.0"
                },
                "semantic_links": [
                    {"relation": "describes", "target": self.pid}
                ],
                "license": "research-use"
            }

            await self.registry_client.create_metadata(metadata)
            print(f"✅ Metadata registered: {self.metadata_pid}")
            self.logger.debug(self.name, f"Metadata record created: {self.metadata_pid}")

            # Get self-description from agent
            self_description = self.get_self_description()

            # Validate structure
            try:
                self._validate_self_description(self_description)
                print(f"✅ Self-description validated")
            except jsonschema.ValidationError as e:
                self.logger.error(self.name, f"Invalid self-description: {e}")
                raise

            # Create FDO record with PID-based references and inline self-description
            # For now, use simple type/profile names as PIDs (backward compatible)
            # In a full implementation, these would also be registered separately
            fdo_record = {
                "pid": self.pid,
                "fdo_type_pid": self.fdo_type,  # Use type name as PID for now
                "fdo_profile_pid": self.fdo_profile,  # Use profile name as PID for now
                "operation_pids": operation_pids,
                "metadata_pointer": self.metadata_pid,  # Keep for backward compatibility
                "self_description": self_description,  # Inline self-description (NEW)
                "activity_log": {
                    "calls_made": [],
                    "calls_received": []
                },
                "kernel_attributes": self.kernel_attributes,
                "created_at": current_timestamp(),
                "updated_at": current_timestamp()
            }

            await self.registry_client.create_fdo(fdo_record)
            print(f"✅ aFDO registered: {self.pid}")

            # Log full registration details
            self.logger.registration(
                self.name,
                self.pid,
                self.port,
                self.operations
            )

            return True

        except Exception as e:
            print(f"❌ Registration failed: {e}")
            self.logger.error(self.name, f"Registration failed: {e}")
            return False

    @abstractmethod
    def get_metadata_content(self) -> Dict[str, Any]:
        """
        Get metadata content for this aFDO.

        Subclasses must implement this to provide their specific metadata.

        Returns:
            Metadata dictionary
        """
        pass

    @abstractmethod
    def get_self_description(self) -> Dict[str, Any]:
        """
        Return structured self-description.

        Must conform to SELF_DESCRIPTION_SCHEMA.
        NO free text in operation definitions.

        Returns:
            dict: Structured self-description
        """
        raise NotImplementedError("Each agent must provide structured self-description")

    def _validate_self_description(self, self_desc: dict) -> bool:
        """
        Validate self-description against schema.

        Args:
            self_desc: Self-description to validate

        Returns:
            bool: True if valid

        Raises:
            jsonschema.ValidationError: If invalid
        """
        jsonschema.validate(instance=self_desc, schema=SELF_DESCRIPTION_SCHEMA)
        return True

    def _load_policy_engine(self) -> Optional[PolicyEngine]:
        """
        Load policy engine from file.

        Looks for policy.json in:
        1. Agent's directory (agents/my_agent/policy.json)
        2. Shared policies (shared/policies/default_<type>_policy.json)
        3. From FDO record (future: policy stored in registry)
        """
        # Try agent-specific policy file
        try:
            agent_dir = Path(sys.modules[self.__class__.__module__].__file__).parent
            policy_file = agent_dir / "policy.json"

            if policy_file.exists():
                self.logger.info(self.name, f"📋 Loading agent-specific policy: {policy_file}")
                return PolicyEngine(
                    agent_pid=self.pid,
                    agent_capabilities=self.operations,
                    policy_file=str(policy_file)
                )
        except Exception as e:
            self.logger.debug(self.name, f"Could not load agent-specific policy: {e}")

        # Try default policies based on agent type
        agent_type = self._infer_agent_type(self.fdo_type)
        default_policy_file = Path(__file__).parent / "policies" / f"default_{agent_type}_policy.json"

        if default_policy_file.exists():
            self.logger.info(self.name, f"📋 Loading default {agent_type} policy: {default_policy_file}")
            return PolicyEngine(
                agent_pid=self.pid,
                agent_capabilities=self.operations,
                policy_file=str(default_policy_file)
            )

        # No policy found
        self.logger.debug(self.name, "⚠️ No policy file found for agent")
        return None

    def _infer_agent_type(self, fdo_type: str) -> str:
        """
        Infer agent type category from FDO type.

        Args:
            fdo_type: The FDO type identifier

        Returns:
            One of: 'task', 'composite', 'interface'
        """
        fdo_type_lower = fdo_type.lower()

        # Interface agents
        if any(keyword in fdo_type_lower for keyword in ['interface', 'ui', 'chat', 'web']):
            return 'interface'

        # Composite/coordinator agents
        if any(keyword in fdo_type_lower for keyword in ['coordinator', 'planner', 'composite', 'orchestrator']):
            return 'composite'

        # Default to task agent
        return 'task'

    def get_comprehensive_metadata(self) -> Dict[str, Any]:
        """
        Generate comprehensive self-describing metadata per FDO principles.

        Enhances the base metadata with provenance, technical details,
        semantic links, and compliance information for full FDO compliance.

        Returns:
            Comprehensive metadata dictionary
        """
        base = self.get_metadata_content()
        return {
            **base,
            "schema_version": "1.0.0",
            "provenance": {
                "creation_method": "automated_registration",
                "framework": "aFDO_marketplace_v1.0",
                "registration_timestamp": current_timestamp(),
                "framework_version": "1.0.0"
            },
            "technical_details": {
                "port": self.port,
                "base_url": self.base_url,
                "operations_count": len(self.operations),
                "has_marketplace_features": True,
                "has_llm": self.kernel_attributes.get("has_llm", False),
                "base_cost": self.kernel_attributes.get("cost", 0.0)
            },
            "semantic_links": [
                {"relation": "implements", "target": self.fdo_profile},
                {"relation": "type_of", "target": self.fdo_type},
                {"relation": "registered_in", "target": "21.T11148/registry-system-001"}
            ],
            "compliance": {
                "FDO_compliant": True,
                "FAIR_enabled": True,
                "DOIP_protocol": "2.0",
                "supports_marketplace": True
            },
            "discovery": {
                "operations": self.operations,
                "specialization": self.kernel_attributes.get("specialization"),
                "reputation": self.kernel_attributes.get("reputation", 0.85)
            }
        }

    async def discover_by_operation(self, operation: str) -> List[Dict[str, Any]]:
        """
        Discover aFDOs that provide a specific operation.

        Args:
            operation: Operation name to search for

        Returns:
            List of matching aFDOs
        """
        try:
            results = await self.registry_client.search_fdos(operation=operation)
            print(f"🔍 Found {len(results)} aFDOs with operation '{operation}'")
            return results
        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            return []

    async def discover_by_type(self, fdo_type: str) -> List[Dict[str, Any]]:
        """
        Discover aFDOs of a specific type.

        Args:
            fdo_type: FDO type to search for

        Returns:
            List of matching aFDOs
        """
        try:
            results = await self.registry_client.search_fdos(fdo_type=fdo_type)
            print(f"🔍 Found {len(results)} aFDOs of type '{fdo_type}'")
            return results
        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            return []

    async def discover_by_query(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic discovery: Find agents that can help with a user query.

        Uses vector embeddings to semantically match the query against agent
        descriptions, returning ranked agents by relevance.

        Args:
            query: User's natural language query
            top_k: Number of agents to return (default: 5)
            min_score: Minimum similarity score (default: 0.0)

        Returns:
            List of matching agents with similarity scores, sorted by relevance
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.registry_url}/doip/discover/by_query",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "min_score": min_score
                    }
                )
                response.raise_for_status()
                result = response.json()

                if result.get('status') == 'success':
                    agents = result.get('data', [])
                    print(f"🔍 Semantic discovery: '{query}' → Found {len(agents)} agents")

                    # Log top matches
                    for i, agent in enumerate(agents[:3], 1):
                        score = agent.get('similarity_score', 0)
                        name = agent.get('name', 'Unknown')
                        print(f"   {i}. {name} (similarity: {score:.3f})")

                    return agents
                else:
                    print(f"❌ Semantic discovery failed: {result.get('message', 'Unknown error')}")
                    return []

        except Exception as e:
            print(f"❌ Semantic discovery failed: {e}")
            self.logger.error(self.name, f"Semantic discovery error: {e}")
            return []

    async def discover_by_operation_query(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Operation-based semantic discovery: Find operations that match a query.

        Searches OPERATIONS (not agents) semantically, then returns matching
        operations with all agents that provide them. This is more accurate
        than agent-based discovery.

        Args:
            query: User's natural language query
            top_k: Number of operations to return (default: 5)
            min_score: Minimum similarity score (default: 0.0)

        Returns:
            List of operations with providers:
            [{
                "operation": "search_papers",
                "similarity_score": 0.85,
                "description": "...",
                "providers": [
                    {"agent_pid": "...", "agent_name": "...", "cost": 0.01, ...},
                    ...
                ]
            }, ...]
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.registry_url}/doip/discover/by_operation_query",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "min_score": min_score
                    }
                )
                response.raise_for_status()
                result = response.json()

                if result.get('status') == 'success':
                    operations = result.get('data', [])
                    print(f"🔍 Operation-based discovery: '{query}' → Found {len(operations)} operations")

                    # Log top matches
                    for i, op in enumerate(operations[:3], 1):
                        # Use correct field names from registry response
                        # Use 'or' to handle None values!
                        score = op.get('semantic_similarity') or op.get('similarity_score') or 0.0
                        op_name = op.get('best_operation') or op.get('operation') or 'Unknown'
                        agent_name = op.get('agent_name') or 'Unknown'
                        print(f"   {i}. {agent_name} / {op_name} (similarity: {score:.3f})")

                    return operations
                else:
                    print(f"❌ Operation discovery failed: {result.get('message', 'Unknown error')}")
                    return []

        except Exception as e:
            print(f"❌ Operation discovery failed: {e}")
            self.logger.error(self.name, f"Operation discovery error: {e}")
            return []

    async def _report_call_event(self, target_pid: str, operation: str, status: str):
        """Report call event to registry (for monitoring)."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.registry_url}/events/call",
                    json={
                        "caller_pid": self.pid,
                        "target_pid": target_pid,
                        "operation": operation,
                        "status": status
                    }
                )
        except:
            pass  # Non-critical, monitoring only

    def _log_outgoing_call(self, target_pid: str, operation: str,
                           status: str, duration: float, cost: float = 0.0,
                           error: str = None):
        """Log call made to another agent."""
        from datetime import datetime

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "target_pid": target_pid,
            "operation": operation,
            "status": status,  # "success" or "failed"
            "duration": round(duration, 2),
            "cost": cost
        }

        if error:
            entry["error"] = error

        # Add to in-memory log
        self._activity_log.append(entry)

        # Keep only last 100
        if len(self._activity_log) > 100:
            self._activity_log = self._activity_log[-100:]

        # Log to console/file
        self.logger.info(self.name, f"📤 OUTGOING | To: {target_pid} | Op: {operation} | Status: {status}")

        # Schedule sync to registry (batched every 5 seconds)
        self._schedule_sync()

    def _log_incoming_call(self, caller_pid: str, operation: str,
                           status: str, duration: float, error: str = None):
        """Log call received from another agent."""
        from datetime import datetime

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "caller_pid": caller_pid,
            "operation": operation,
            "status": status,
            "duration": round(duration, 2)
        }

        if error:
            entry["error"] = error

        # Add to in-memory log
        self._activity_log_incoming.append(entry)

        # Keep only last 100
        if len(self._activity_log_incoming) > 100:
            self._activity_log_incoming = self._activity_log_incoming[-100:]

        # Log to console/file
        self.logger.info(self.name, f"📥 INCOMING | From: {caller_pid} | Op: {operation} | Status: {status}")

        # Schedule sync to registry (batched every 5 seconds)
        self._schedule_sync()

    def _schedule_sync(self):
        """Schedule activity log sync to registry (batched)."""
        if not self._sync_scheduled:
            self._sync_scheduled = True

            # Sync after 5 seconds (batch multiple logs together)
            asyncio.create_task(self._delayed_sync())

    async def _delayed_sync(self):
        """Wait and sync to registry."""
        await asyncio.sleep(5)

        try:
            await self._sync_activity_to_registry()
        finally:
            self._sync_scheduled = False

    async def _sync_activity_to_registry(self):
        """Update activity log in registry."""
        activity_data = {
            "calls_made": self._activity_log.copy(),
            "calls_received": self._activity_log_incoming.copy()
        }

        # Update FDO record in registry
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.patch(
                    f"{self.registry_url}/registry/fdos/{self.pid}/field/activity_log",
                    json={"value": activity_data}
                )
                if response.status_code == 200:
                    self.logger.debug(self.name, f"Activity log synced to registry")
        except Exception as e:
            self.logger.debug(self.name, f"Activity log sync failed: {e}")

    async def call_other_afdo(
        self,
        target_pid: str,
        operation: str,
        data: Dict[str, Any],
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call an operation on another aFDO.

        Discovers target port from registry (no hardcoding).

        Args:
            target_pid: PID of target aFDO
            operation: Operation to call
            data: Parameters for the operation
            job_id: Optional job ID for tracking (creates new job if None)

        Returns:
            Result from the operation
        """
        # Job tracking - use provided job_id or current context
        if job_id is None:
            job_id = self.current_job_id

        # If still no job_id, start new job
        if job_id is None:
            tracker = get_job_tracker()
            job_id = tracker.start_job(self.pid)
            self.current_job_id = job_id

        # Log call initiation
        tracker = get_job_tracker()
        tracker.add_call(
            job_id=job_id,
            caller_pid=self.pid,
            target_pid=target_pid,
            operation=operation,
            status="initiated"
        )

        start_time = time.time()
        try:
            # Get target aFDO info from registry
            print(f"🔍 Looking up {target_pid} in registry... [job:{job_id}]")
            self.logger.debug(self.name, f"Looking up {target_pid} in registry")

            target_info = await self.registry_client.read_fdo(target_pid)
            target_data = target_info.get('data', {})

            # Get port from kernel_attributes (THE RIGHT WAY!)
            kernel_attrs = target_data.get('kernel_attributes', {})
            target_port = kernel_attrs.get('port')

            if not target_port:
                error_msg = f"Target aFDO {target_pid} does not have 'port' in kernel_attributes"
                self.logger.error(self.name, error_msg)
                raise ValueError(f"{error_msg}. Cannot determine how to reach it.")

            target_url = f"http://localhost:{target_port}"
            print(f"📤 Calling {target_pid} at port {target_port} [job:{job_id}]")

            # Log inter-agent call
            self.logger.agent_call(self.name, target_pid, operation)

            # Report call initiated (fire and forget)
            asyncio.create_task(self._report_call_event(target_pid, operation, "initiated"))

            # Make DOIP call with parent trace context for nested tracing
            parent_request_id = None
            if hasattr(self, 'current_tracer') and self.current_tracer:
                parent_request_id = self.current_tracer.request_id

            result = await self.registry_client.extend_operation(
                target_url=target_url,
                operation=operation,
                caller_pid=self.pid,
                data=data,
                parent_request_id=parent_request_id
            )

            duration = time.time() - start_time

            # Extract cost from result if available
            result_cost = 0.0
            if isinstance(result, dict):
                result_cost = result.get("cost", 0.0)

            # Log success in job tracker
            tracker.add_call(
                job_id=job_id,
                caller_pid=self.pid,
                target_pid=target_pid,
                operation=operation,
                status="success",
                duration=duration,
                cost=result_cost
            )

            # Log outgoing call with new structured logging
            self._log_outgoing_call(
                target_pid=target_pid,
                operation=operation,
                status="success",
                duration=duration,
                cost=result_cost
            )

            # Report success (fire and forget)
            asyncio.create_task(self._report_call_event(target_pid, operation, "success"))

            print(f"✅ Call successful: {target_pid}.{operation}() [job:{job_id}]")
            self.logger.agent_response(self.name, target_pid, True, duration)

            return result

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Call to {target_pid}.{operation}() failed: {e} [job:{job_id}]")

            self.logger.error(self.name, f"Call to {target_pid}.{operation}() failed: {e}")

            # Log failure in job tracker
            tracker = get_job_tracker()
            tracker.add_call(
                job_id=job_id,
                caller_pid=self.pid,
                target_pid=target_pid,
                operation=operation,
                status="failed",
                duration=duration,
                error=str(e)
            )

            # Log failed call with new structured logging
            self._log_outgoing_call(
                target_pid=target_pid,
                operation=operation,
                status="failed",
                duration=duration,
                cost=0.0,
                error=str(e)
            )

            # Report failure (fire and forget)
            asyncio.create_task(self._report_call_event(target_pid, operation, "failed"))

            raise

    # MARKETPLACE METHODS

    async def get_quote(
        self,
        operation: str,
        parameters: Dict[str, Any],
        priority: str = "normal"
    ) -> Quote:
        """
        Provide a quote for an operation.

        Args:
            operation: Operation name
            parameters: Operation parameters
            priority: Priority level (low, normal, high, urgent)

        Returns:
            Quote with pricing and timing information
        """
        if operation not in self.operations:
            raise ValueError(f"Operation '{operation}' not supported")

        # Get current pricing and queue status
        current_cost = self.queue_manager.get_current_price()
        queue_status = self.queue_manager.get_queue_status()

        # Estimate duration (subclasses can override)
        estimated_duration = self._estimate_operation_duration(operation, parameters)

        # Create quote
        quote = Quote(
            quote_id=str(uuid.uuid4()),
            agent_pid=self.pid,
            operation=operation,
            estimated_cost=current_cost,
            estimated_duration=estimated_duration,
            queue_position=queue_status.queue_length,
            availability_status=queue_status.availability_status,
            expires_at=create_quote_expiry(minutes=5),
            negotiable=True,
            minimum_price=self.negotiation_strategy.minimum_price
        )

        return quote

    def _estimate_operation_duration(self, operation: str, parameters: Dict[str, Any]) -> float:
        """
        Estimate operation duration in seconds.

        Subclasses can override this for better estimates.

        Args:
            operation: Operation name
            parameters: Operation parameters

        Returns:
            Estimated duration in seconds
        """
        return 5.0  # Default estimate

    async def negotiate(
        self,
        quote_request: QuoteRequest
    ) -> NegotiationResult:
        """
        Negotiate terms for an operation.

        Args:
            quote_request: Negotiation request

        Returns:
            Negotiation result (accepted/rejected/counter-offer)
        """
        # Get current status
        queue_status = self.queue_manager.get_queue_status()
        current_load = queue_status.current_load

        # Get caller reputation if available
        caller_reputation = None
        if quote_request.caller_pid:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(
                        f"{self.registry_url}/reputation/{quote_request.caller_pid}"
                    )
                    if response.status_code == 200:
                        data = response.json()
                        caller_reputation = data.get("data", {}).get("score")
            except:
                pass

        # Evaluate offer using strategy
        result = self.negotiation_strategy.evaluate_offer(
            offered_price=quote_request.max_budget,
            current_load=current_load,
            caller_reputation=caller_reputation,
            reason=quote_request.priority
        )

        return result

    async def select_service_provider(
        self,
        operation: str,
        parameters: Dict[str, Any],
        budget: BudgetManager,
        policy: Optional[SelectionPolicy] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> Tuple[str, Quote]:
        """
        Select best service provider for an operation.

        Args:
            operation: Operation name
            parameters: Operation parameters
            budget: Budget manager for cost checking
            policy: Selection policy (defaults to self.selection_policy)
            exclude_agents: Optional list of agent PIDs to exclude

        Returns:
            Tuple of (selected_agent_pid, quote)

        Raises:
            ValueError: If no suitable provider found
        """
        if policy is None:
            policy = self.selection_policy

        # Discover providers from registry
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.registry_url}/market/agents/by_operation/{operation}"
                )

                if response.status_code != 200:
                    raise ValueError(f"Failed to discover providers for {operation}")

                data = response.json()
                providers = data.get("data", [])

        except Exception as e:
            raise ValueError(f"Provider discovery failed: {e}")

        if not providers:
            raise ValueError(f"No providers found for operation: {operation}")

        # Filter out excluded agents
        if exclude_agents:
            providers = [p for p in providers if p["pid"] not in exclude_agents]

        if not providers:
            raise ValueError(f"No available providers after exclusions")

        # Create quotes from provider info
        quotes = []
        reputations = {}

        for provider in providers:
            quote = Quote(
                quote_id=str(uuid.uuid4()),
                agent_pid=provider["pid"],
                operation=operation,
                estimated_cost=provider["current_cost"],
                estimated_duration=5.0,  # Could be fetched from provider
                queue_position=provider["queue_length"],
                availability_status=provider["availability_status"],
                expires_at=create_quote_expiry(minutes=5)
            )
            quotes.append(quote)
            reputations[provider["pid"]] = provider["reputation"]

        # Select using policy
        selected_quote = policy.select(quotes, reputations)

        if not selected_quote:
            raise ValueError("No suitable provider matches selection criteria")

        # Check budget
        if not budget.can_afford(selected_quote.estimated_cost):
            raise ValueError(
                f"Insufficient budget: need ${selected_quote.estimated_cost:.4f}, "
                f"have ${budget.get_available():.4f}"
            )

        return selected_quote.agent_pid, selected_quote

    async def call_with_alternatives(
        self,
        operation: str,
        parameters: Dict[str, Any],
        budget: BudgetManager,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Call operation with automatic failure handling and alternatives.

        Args:
            operation: Operation name
            parameters: Operation parameters
            budget: Budget manager
            max_retries: Maximum number of alternative attempts

        Returns:
            Operation result with cost metadata

        Raises:
            Exception: If all attempts fail
        """
        attempted_agents = []
        last_error = None

        self.logger.debug(self.name, f"Starting call_with_alternatives for {operation}")

        for attempt in range(max_retries + 1):
            try:
                # Select provider (excluding failed ones)
                agent_pid, quote = await self.select_service_provider(
                    operation=operation,
                    parameters=parameters,
                    budget=budget,
                    exclude_agents=attempted_agents
                )

                attempted_agents.append(agent_pid)
                self.logger.info(
                    self.name,
                    f"Selected provider {agent_pid} for {operation} (cost: ${quote.estimated_cost:.4f})"
                )

                # Reserve budget
                reservation_id = budget.reserve(quote.estimated_cost, operation, agent_pid)
                if not reservation_id:
                    raise ValueError("Insufficient budget for reservation")

                self.logger.budget_transaction(
                    self.name,
                    "RESERVE",
                    quote.estimated_cost,
                    budget.get_available()
                )

                # Call agent
                start_time = time.time()
                result = await self.call_other_afdo(
                    target_pid=agent_pid,
                    operation=operation,
                    data=parameters
                )
                duration = time.time() - start_time

                # Extract actual cost from result (or use estimated)
                actual_cost = result.get("cost", quote.estimated_cost)

                # Commit budget
                budget.commit(reservation_id, actual_cost)
                self.logger.budget_transaction(
                    self.name,
                    "COMMIT",
                    actual_cost,
                    budget.get_available()
                )

                # Report success to registry
                await self._report_operation_success(
                    agent_pid=agent_pid,
                    operation=operation,
                    estimated_cost=quote.estimated_cost,
                    actual_cost=actual_cost,
                    estimated_duration=quote.estimated_duration,
                    actual_duration=duration
                )

                # Add cost metadata to result
                if isinstance(result, dict):
                    result["cost"] = actual_cost
                    result["duration"] = duration
                    result["provider"] = agent_pid

                self.logger.info(
                    self.name,
                    f"Successfully completed {operation} via {agent_pid} (cost: ${actual_cost:.4f})"
                )

                return result

            except Exception as e:
                last_error = e

                # Release reservation if it exists
                if 'reservation_id' in locals():
                    budget.release(reservation_id)
                    self.logger.budget_transaction(
                        self.name,
                        "RELEASE",
                        quote.estimated_cost if 'quote' in locals() else 0.0,
                        budget.get_available()
                    )

                # Report failure
                if attempted_agents:
                    await self._report_failure(
                        agent_pid=attempted_agents[-1],
                        operation=operation,
                        error=str(e)
                    )

                if attempt < max_retries:
                    print(f"  ⚠ Attempt {attempt + 1} failed: {e}")
                    self.logger.warning(
                        self.name,
                        f"Attempt {attempt + 1} failed: {e}"
                    )
                    print(f"  🔄 Trying alternative provider...")
                    self.logger.info(self.name, "Trying alternative provider...")
                else:
                    error_msg = f"All {max_retries + 1} attempts failed. Last error: {e}"
                    self.logger.error(self.name, error_msg)
                    raise Exception(error_msg) from last_error

        # Should not reach here, but just in case
        raise Exception(f"Operation failed after {max_retries + 1} attempts")

    async def _report_operation_success(
        self,
        agent_pid: str,
        operation: str,
        estimated_cost: float,
        actual_cost: float,
        estimated_duration: float,
        actual_duration: float
    ):
        """Report successful operation to registry for reputation tracking."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.registry_url}/reputation/update",
                    json={
                        "agent_pid": agent_pid,
                        "operation_id": str(uuid.uuid4()),
                        "success": True,
                        "estimated_duration": estimated_duration,
                        "actual_duration": actual_duration,
                        "estimated_cost": estimated_cost,
                        "actual_cost": actual_cost
                    }
                )
        except:
            pass  # Non-critical

    async def _report_failure(
        self,
        agent_pid: str,
        operation: str,
        error: str
    ):
        """Report operation failure to registry."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.registry_url}/failures/report",
                    json={
                        "caller_pid": self.pid,
                        "failed_agent_pid": agent_pid,
                        "operation": operation,
                        "error_type": "execution_error",
                        "error_message": error
                    }
                )
        except:
            pass  # Non-critical

    # POLICY ENGINE METHODS

    async def handle_operation_with_policy(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any],
        authentication: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle operation using policy engine with execution tracing (Task 32).

        This method wraps the abstract handle_operation method with policy-based
        decision making and captures complete execution trace.

        Args:
            operation: Operation name
            caller_pid: PID of calling aFDO
            parameters: Operation parameters
            authentication: Full authentication object (may contain parent_request_id)

        Returns:
            Operation result (with _trace field if enabled)
        """
        # Create execution tracer (Task 32)
        # Extract parent_request_id for nested tracing
        authentication = authentication or {}
        parent_request_id = authentication.get("parent_request_id")

        user_query = parameters.get("message", operation)
        tracer = ExecutionTracer(
            user_query=user_query,
            parent_request_id=parent_request_id
        )
        self.current_tracer = tracer

        # Log initial receipt
        tracer.log_event(
            agent_name=self.name,
            agent_pid=self.pid,
            action_type="receive",
            operation=operation,
            input_data=parameters,
            notes=f"Request received from {caller_pid}"
        )

        self.logger.info(self.name, f"🔧 Received '{operation}' from {caller_pid}")

        try:
            # Handle standard operations that all agents support (Task 30)
            if operation == "get_description":
                self.logger.info(self.name, "📋 Returning self-description")
                result = self.get_self_description()

                # Log return
                tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="return",
                    operation=operation,
                    output_data={"description": "Self-description returned"},
                    notes="Returned self-description"
                )

                return self._finalize_with_trace(result, tracer)

            if not self.policy_engine:
                # No policy - execute directly
                result = await self.handle_operation(operation, caller_pid, parameters)

                tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="return",
                    operation=operation,
                    notes="Executed without policy engine"
                )

                return self._finalize_with_trace(result, tracer)

            # Consult policy engine
            context = {
                "caller_pid": caller_pid,
                "budget": parameters.get("budget"),
                "policy": parameters.get("policy", "balanced"),
                "custom": {}
            }

            policy_start = time.time()
            decision = await self.policy_engine.decide(
                operation=operation,
                parameters=parameters,
                context=context
            )
            policy_duration = int((time.time() - policy_start) * 1000)

            # Log policy evaluation
            tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="policy_evaluation",
                operation="evaluate_policy",
                input_data={"operation": operation},
                output_data={"decision": decision.decision.value},
                duration_ms=policy_duration,
                policy_rule=decision.rule_id,
                policy_reasoning=decision.reasoning,
                notes=f"Policy matched rule: {decision.rule_id}"
            )

            self.logger.info(self.name, f"🧠 Policy decision: {decision.decision.value}")
            self.logger.info(self.name, f"   Rule: {decision.rule_id}")
            self.logger.info(self.name, f"   Reasoning: {decision.reasoning}")

            # Execute decision
            exec_start = time.time()
            result = await self._execute_policy_decision(decision, operation, caller_pid, parameters)
            exec_duration = int((time.time() - exec_start) * 1000)

            # Log execution complete
            tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="return",
                operation=operation,
                duration_ms=exec_duration,
                notes=f"Request completed successfully with policy: {decision.decision.value}"
            )

            return self._finalize_with_trace(result, tracer)

        except Exception as e:
            # Log error
            tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="error",
                operation=operation,
                error=str(e),
                notes="Request failed with error"
            )

            # Save trace even on error
            trace_file = tracer.save_to_file(self.trace_directory)
            self.logger.error(self.name, f"❌ Error during execution. Trace saved to: {trace_file}")

            raise

    def _finalize_with_trace(self, result: Dict[str, Any], tracer: ExecutionTracer) -> Dict[str, Any]:
        """
        Finalize result with trace information.

        Saves trace to file and adds trace info to result.
        """
        # Save trace
        trace_file = tracer.save_to_file(self.trace_directory)
        summary = tracer.get_summary()

        self.logger.info(self.name, f"📊 Trace saved: {trace_file}")

        # Add trace info to result
        if isinstance(result, dict):
            result["_trace"] = {
                "request_id": tracer.request_id,
                "trace_file": trace_file,
                "summary": summary
            }

        return result

    async def _execute_policy_decision(
        self,
        decision: PolicyDecision,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a policy decision."""

        # Check for "consult_for_workflow" action in decision parameters
        action = decision.parameters.get("action")
        if action == "consult_for_workflow":
            return await self._consult_for_workflow(decision, operation, parameters)

        if decision.decision == DecisionType.HANDLE_ALONE:
            # Execute directly
            return await self.handle_operation(operation, caller_pid, parameters)

        elif decision.decision == DecisionType.QUERY_REGISTRY_FOR_HELPER:
            # Query registry for helper
            return await self._query_and_delegate_to_helper(decision, operation, parameters)

        elif decision.decision == DecisionType.QUERY_REGISTRY_FOR_PLANNER:
            # Query registry for planner
            return await self._query_and_delegate_to_planner(decision, operation, parameters)

        elif decision.decision == DecisionType.QUERY_REGISTRY_FOR_COORDINATOR:
            # Query registry for coordinator
            return await self._query_and_delegate_to_coordinator(decision, operation, parameters)

        elif decision.decision == DecisionType.DELEGATE_FULLY:
            # Full delegation (interface agents)
            return await self._delegate_fully(decision, operation, parameters)

        elif decision.decision == DecisionType.COLLABORATE:
            # Multi-agent collaboration (composite agents)
            return await self._collaborate(decision, operation, parameters)

        elif decision.decision == DecisionType.CONSULT_FOR_WORKFLOW:
            # Consult LLM for dynamic workflow generation
            return await self._consult_for_workflow(decision, operation, parameters)

        elif decision.decision == DecisionType.DECOMPOSE_AND_COORDINATE:
            # Decompose task into subtasks, delegate each, compose results
            return await self._decompose_and_coordinate(decision, operation, parameters)

        elif decision.decision == DecisionType.SEMANTIC_DISCOVERY:
            # NEW: Use semantic discovery to find best agent and cascade delegate
            result = await self._semantic_discovery_and_cascade(decision, operation, parameters)

            # Format response for Chat UI if needed
            if self.name == "Chat UI" and isinstance(result, dict) and 'data' in result:
                data = result['data']

                # Format for user display
                if isinstance(data, dict) and ('summary' in data or 'answer' in data or 'papers' in data):
                    formatted = self._format_response_for_ui(data)
                    if formatted:
                        return formatted

            return result

        elif decision.decision == DecisionType.CONSULT_LLM_FOR_ROUTING:
            # NEW: Ask LLM Consultant for routing advice, then delegate
            return await self._consult_llm_for_routing(decision, operation, parameters)

        elif decision.decision == DecisionType.SEQUENCE:
            # Execute a sequence of steps defined in policy
            result = await self._execute_sequence(decision, operation, parameters)

            # Format response for Chat UI if needed
            if self.name == "Chat UI" and isinstance(result, dict) and 'data' in result:
                data = result['data']

                # Format for user display
                if isinstance(data, dict) and ('summary' in data or 'answer' in data or 'papers' in data):
                    formatted = self._format_response_for_ui(data)
                    if formatted:
                        return formatted

            return result

        else:
            raise ValueError(f"Unknown decision type: {decision.decision}")

    async def _query_and_delegate_to_helper(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query registry and delegate SPECIFIC subtask to helper.

        Updated to:
        1. Query registry based on NEEDS (not agent names)
        2. Handle empty registry results with fallback
        3. Delegate specific subtask (not whole task)
        """

        registry_query = decision.parameters.get("registry_query", {})
        operations_to_find = registry_query.get("operations", [])
        fallback_operations = registry_query.get("fallback_operations", [])
        selection_criteria = registry_query.get("selection_criteria", "balanced")
        use_semantic_discovery = registry_query.get("use_semantic_discovery", True)

        # Handle special "from_request" operation
        if operations_to_find and operations_to_find[0] == "from_request":
            operations_to_find = [operation]

        # Get user query for semantic discovery
        user_query = parameters.get("message") or parameters.get("query") or ""

        # OPERATION-BASED SEMANTIC DISCOVERY: Use actual user query for discovery
        if use_semantic_discovery and user_query:
            self.logger.info(self.name, f"🔍 Operation-based semantic discovery for query: '{user_query}'")

            # Log semantic discovery start (Task 32)
            if self.current_tracer:
                self.current_tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="discover",
                    operation="operation_semantic_discovery",
                    input_data={"query": user_query},
                    notes="Discovering operations using semantic matching"
                )

            # Use operation-based semantic discovery
            operation_results = await self.discover_by_operation_query(
                query=user_query,
                top_k=5,
                min_score=0.1  # Minimum 10% similarity
            )

            if operation_results:
                # Select the best matching operation
                top_operation = operation_results[0]
                operation_found = top_operation['operation']
                similarity_score = top_operation['similarity_score']
                providers = top_operation['providers']

                self.logger.info(self.name, f"   ✅ Best operation: {operation_found} (similarity: {similarity_score:.3f})")
                self.logger.info(self.name, f"   📋 Available providers: {len(providers)}")

                # Filter out self to prevent infinite recursion
                providers = [p for p in providers if p['agent_pid'] != self.pid]

                if not providers:
                    self.logger.warning(self.name, f"   ⚠️ No providers found (all filtered out)")
                    helpers = []
                else:
                    # Select best provider based on cost and status
                    # Sort by: active first, then by cost
                    providers.sort(key=lambda p: (p['status'] != 'active', p['cost']))

                    selected_provider = providers[0]
                    provider_name = selected_provider['agent_name']
                    provider_cost = selected_provider['cost']

                    self.logger.info(self.name, f"   🎯 Selected provider: {provider_name} (cost: ${provider_cost:.3f})")

                    # Build helpers list with just the selected provider's agent
                    helpers = [selected_provider['agent_fdo']]

            else:
                self.logger.info(self.name, f"   ⚠️ No operations matched, falling back to operation-name discovery")
                helpers = []
                operation_found = None

        # FALLBACK: Operation-based discovery if semantic fails or disabled
        if not helpers and operations_to_find:
            self.logger.info(self.name, f"🔍 Operation-based discovery for: {operations_to_find}")

            # Log discovery start (Task 32)
            if self.current_tracer:
                self.current_tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="discover",
                    operation="query_registry",
                    input_data={"operations": operations_to_find},
                    notes="Discovering agents from registry (operation-based)"
                )

            operation_found = None

            # Try primary operations
            for op in operations_to_find:
                self.logger.info(self.name, f"   Searching for: {op}")
                found = await self.discover_by_operation(op)
                if found:
                    helpers = found
                    operation_found = op
                    self.logger.info(self.name, f"   ✅ Found {len(found)} agent(s)")
                    break

            # Try fallback operations if primary not found
            if not helpers and fallback_operations:
                self.logger.info(self.name, f"   Primary not found, trying fallbacks: {fallback_operations}")
                for op in fallback_operations:
                    self.logger.info(self.name, f"   Searching for: {op}")
                    found = await self.discover_by_operation(op)
                    if found:
                        helpers = found
                        operation_found = op
                        self.logger.info(self.name, f"   ✅ Found {len(found)} agent(s)")
                        break

        # Handle empty registry result
        if not helpers:
            self.logger.warning(self.name, f"⚠️ No agents found for any of: {operations_to_find + fallback_operations}")

            # Log no agents found (Task 32)
            if self.current_tracer:
                self.current_tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="discover",
                    operation="query_registry",
                    output_data={"found": 0},
                    notes="No agents found - executing fallback"
                )

            # Execute fallback strategy
            if decision.fallback:
                self.logger.info(self.name, f"🔄 Executing fallback: {decision.fallback.get('type')}")
                return await self._execute_fallback(decision.fallback, operation, parameters)
            else:
                raise ValueError(f"No suitable agents found and no fallback strategy defined")

        # Helpers found - select and delegate
        selected = self._select_helper(helpers, selection_criteria)

        # Extract name from selected helper
        helper_name = selected.get("name") or selected.get("kernel_attributes", {}).get("name", "Unknown")
        helper_cost = selected.get("cost") or selected.get("current_cost") or selected.get("kernel_attributes", {}).get("cost", 0.0)

        self.logger.info(self.name, f"✅ Selected: {helper_name} (${helper_cost:.3f})")

        # Log selection (Task 32)
        if self.current_tracer:
            self.current_tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="select",
                operation="select_helper",
                output_data={"selected": helper_name, "cost": helper_cost, "candidates": len(helpers)},
                notes=f"Selected {helper_name} from {len(helpers)} candidates"
            )

        # SCHEMA-DRIVEN INPUT PREPARATION (Task 30 - NO HARDCODING!)
        prep_start = time.time()
        delegate_params = await self._prepare_input_for_delegee(
            user_query=parameters.get("message", ""),
            delegee_pid=selected["pid"],
            delegee_name=helper_name,
            operation=operation_found or operation
        )
        prep_duration = int((time.time() - prep_start) * 1000)

        # Log input preparation (Task 32)
        if self.current_tracer:
            self.current_tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="prepare_input",
                operation="prepare_for_delegee",
                input_data={"original": parameters.get("message", "")[:100]},
                output_data={"prepared": str(delegate_params)[:100]},
                duration_ms=prep_duration,
                notes="Prepared input based on delegee's schema (Task 30)"
            )

        self.logger.info(self.name, f"🚀 Delegating: {operation_found or operation}")

        # Log delegation (Task 32)
        if self.current_tracer:
            self.current_tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="delegate",
                operation=operation_found or operation,
                input_data=delegate_params,
                delegated_to=helper_name,
                delegated_to_pid=selected["pid"],
                cost=helper_cost,
                notes=f"Delegating to {helper_name}"
            )

        # Delegate SPECIFIC operation (not whole task!)
        delegation_start = time.time()
        result = await self.call_other_afdo(
            target_pid=selected["pid"],
            operation=operation_found or operation,
            data=delegate_params
        )
        delegation_duration = int((time.time() - delegation_start) * 1000)

        # Log result received (Task 32)
        if self.current_tracer:
            result_preview = str(result)[:200] if result else "None"
            self.current_tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="receive_result",
                operation=operation_found or operation,
                output_data={"preview": result_preview},
                duration_ms=delegation_duration,
                delegated_to=helper_name,
                notes=f"Received result from {helper_name}"
            )

        # Format result for user (NEVER show commands!)
        no_commands = decision.parameters.get("no_command_suggestions", False)
        return self._format_delegation_result(
            result=result,
            agent_name=helper_name,
            no_commands=no_commands
        )

    async def _prepare_input_for_delegee(
        self,
        user_query: str,
        delegee_pid: str,
        delegee_name: str,
        operation: str
    ) -> Dict[str, Any]:
        """
        Prepare input for delegee using schema-driven approach (Task 30).

        This method implements FAIR/FDO principles:
        1. Delegee self-describes its input requirements (in metadata)
        2. Delegator discovers schema at runtime
        3. LLM transforms based on schema (NO hardcoding!)

        Steps:
        1. Get delegee's self-description
        2. Extract input schema for operation
        3. Use SchemaBasedInputPreparator to transform

        Args:
            user_query: Original user query
            delegee_pid: PID of the delegee agent
            delegee_name: Name of delegee (for logging)
            operation: Operation being called

        Returns:
            Prepared parameters matching delegee's schema
        """

        self.logger.info(self.name, f"🔧 Preparing input for {delegee_name}.{operation}")

        try:
            # Step 1: Get delegee's self-description
            self.logger.info(self.name, f"   📋 Fetching input schema from {delegee_name}...")

            delegee_response = await self.call_other_afdo(
                target_pid=delegee_pid,
                operation="get_description",
                data={}
            )

            # Extract data from DOIP response
            delegee_description = delegee_response.get("data", delegee_response)

            # Step 2: Extract input schema for the operation
            input_schema = self._extract_input_schema(
                delegee_description,
                operation
            )

            if not input_schema:
                self.logger.warning(self.name, f"   ⚠️ No input schema found for {operation}")
                # Fallback: basic preparation
                return {"topic": user_query, "query": user_query}

            self.logger.info(self.name, f"   ✅ Got input schema")

            # Step 3: Use SchemaBasedInputPreparator to transform based on schema
            prepared_params = await self.input_preparator.prepare_input(
                user_query=user_query,
                input_schema=input_schema,
                operation_name=operation,
                delegee_name=delegee_name
            )

            self.logger.info(self.name, f"   Original query: {user_query[:100]}")
            self.logger.info(self.name, f"   Prepared params: {prepared_params}")

            return prepared_params

        except Exception as e:
            self.logger.error(self.name, f"❌ Schema-based preparation failed: {e}")
            # Fallback: basic extraction
            return {"topic": user_query, "query": user_query}

    def _extract_input_schema(
        self,
        delegee_description: Dict[str, Any],
        operation: str
    ) -> Dict[str, Any]:
        """
        Extract input schema for specific operation from delegee's description.

        This is a key part of the FAIR/FDO approach - agents declare their
        input requirements in machine-actionable metadata.

        Args:
            delegee_description: Delegee's self-description (from get_description)
            operation: Operation name

        Returns:
            Input schema for the operation
        """

        capabilities = delegee_description.get("capabilities", {})
        operation_spec = capabilities.get(operation, {})
        input_schema = operation_spec.get("input_schema", {})

        return input_schema

    def _format_delegation_result(
        self,
        result: Dict[str, Any],
        agent_name: str,
        no_commands: bool = False
    ) -> Dict[str, Any]:
        """
        Format delegation result for user.

        CRITICAL: NEVER show agent names or commands to user!

        Args:
            result: Result from delegated agent
            agent_name: Name of agent (for logging only)
            no_commands: If True, ensure no command suggestions

        Returns:
            User-friendly response
        """

        self.logger.info(self.name, f"📝 Formatting result from {agent_name}")

        # Extract the actual content
        if isinstance(result, dict):
            # Handle DOIP protocol response structure
            if "data" in result and isinstance(result["data"], dict):
                data = result["data"]
                response_text = (
                    data.get("summary") or
                    data.get("response") or
                    data.get("content") or
                    data.get("answer") or
                    data.get("message") or
                    str(data)
                )
            else:
                # Direct response fields
                response_text = (
                    result.get("summary") or
                    result.get("response") or
                    result.get("content") or
                    result.get("answer") or
                    result.get("message") or
                    str(result)
                )
        else:
            response_text = str(result)

        # CRITICAL: Remove any command suggestions
        if no_commands or True:  # Always remove commands for safety
            # Remove phrases that mention agents or commands
            phrases_to_remove = [
                "i recommend using",
                "you can use",
                "try using",
                "use the command",
                "search_wikipedia",
                "get_article_summary",
                f"the {agent_name.lower()}",
                "wikipedia agent",
                "arxiv agent",
                "agent"
            ]

            lower_response = response_text.lower()
            for phrase in phrases_to_remove:
                if phrase in lower_response:
                    # Truncate at the suggestion
                    idx = lower_response.find(phrase)
                    response_text = response_text[:idx].strip()
                    self.logger.warning(self.name, f"⚠️ Removed command suggestion: '{phrase}'")
                    break

        # Return in standard format
        return {
            "status": "success",
            "message": response_text
        }

    async def _query_and_delegate_to_planner(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Query registry for planner and delegate."""

        registry_query = decision.parameters.get("registry_query", {})
        operations = registry_query.get("operations", ["plan_task", "coordinate_workflow"])

        # Try to find a planner
        planners = []
        for op in operations:
            planners = await self.discover_by_operation(op)
            if planners:
                break

        if not planners:
            # Fallback to handling alone
            self.logger.warning(self.name, "⚠️ No planners found, handling alone")
            return await self.handle_operation(operation, "self", parameters)

        # Select first planner
        planner = planners[0]
        self.logger.info(self.name, f"✅ Delegating to planner: {planner['pid']}")

        # Delegate to planner
        return await self.call_other_afdo(
            target_pid=planner["pid"],
            operation=operation,
            data=parameters
        )

    async def _query_and_delegate_to_coordinator(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Query registry for coordinator and delegate."""
        # Similar to planner delegation
        return await self._query_and_delegate_to_planner(decision, operation, parameters)

    async def _delegate_fully(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full delegation (for interface agents).

        Interface agents interpret user intent and route to appropriate agents.
        """
        registry_query = decision.parameters.get("registry_query", {})
        operations = registry_query.get("operations", [])

        # Find appropriate coordinator/planner
        agents = []
        for op in operations:
            agents = await self.discover_by_operation(op)
            if agents:
                break

        if not agents:
            return {
                "status": "error",
                "message": "No suitable agents found to handle request"
            }

        # Select and delegate
        agent = agents[0]
        self.logger.info(self.name, f"✅ Delegating fully to: {agent['pid']}")

        return await self.call_other_afdo(
            target_pid=agent["pid"],
            operation=operation,
            data=parameters
        )

    async def _collaborate(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Multi-agent collaboration (for composite agents).

        This is a placeholder for complex multi-agent collaboration logic.
        Composite agents would override this to implement their specific
        collaboration strategies.
        """
        # Default: try to handle alone
        self.logger.info(self.name, "🤝 Collaboration mode - attempting to handle")
        return await self.handle_operation(operation, "self", parameters)

    async def _consult_for_workflow(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consult LLM to generate workflow dynamically.

        This is the KEY method for autonomous workflow generation:
        1. Agent realizes task is too complex
        2. Agent queries registry for consultant
        3. Consultant generates workflow on-the-fly
        4. Agent executes generated workflow

        NO predefined workflows!
        """

        # Step 1: Query registry for workflow consultant
        self.logger.info(self.name, "🧠 Consulting LLM for workflow generation")

        consultants = await self.discover_by_operation("generate_workflow")

        if not consultants:
            raise ValueError("No workflow consultant available in system")

        consultant_pid = consultants[0]["pid"]
        self.logger.info(self.name, f"   Selected consultant: {consultant_pid}")

        # Step 2: Prepare task description and context
        task_description = parameters.get("question") or parameters.get("query") or str(parameters)

        context = {
            "budget": parameters.get("budget", 10.0),
            "quality_preference": parameters.get("quality_preference", "balanced")
        }

        # Step 3: Call consultant to generate workflow
        self.logger.info(self.name, "   Requesting workflow generation...")

        consultant_params = {
            "task_description": task_description,
            "requester_capabilities": self.operations,
            "requester_pid": self.pid,
            "context": context
        }

        result = await self.call_other_afdo(
            target_pid=consultant_pid,
            operation="generate_workflow",
            data=consultant_params
        )

        # Step 4: Extract generated workflow
        workflow = result.get("data", {}).get("workflow")
        reasoning = result.get("data", {}).get("reasoning")

        if not workflow:
            raise ValueError("Consultant failed to generate workflow")

        self.logger.info(self.name, f"✅ Workflow generated: {workflow.get('name')}")
        self.logger.info(self.name, f"   Steps: {len(workflow.get('steps', []))}")
        self.logger.info(self.name, f"   Reasoning: {reasoning}")

        # Step 5: Load workflow into engine
        if not self.workflow_engine:
            raise ValueError("Workflow engine not initialized")

        self.workflow_engine.load_workflow(workflow)

        # Step 6: Estimate workflow cost
        workflow_input = {
            "question": task_description
        }

        estimate = await self.workflow_engine.estimate_workflow(workflow_input)
        estimated_cost = estimate.get("estimated_cost", 0.0)

        self.logger.info(self.name, f"💰 Estimated workflow cost: ${estimated_cost:.4f}")

        # Step 7: Execute workflow
        budget = parameters.get("budget", 10.0)

        if estimated_cost > budget:
            self.logger.warning(self.name, f"⚠️ Estimated cost ${estimated_cost:.4f} exceeds budget ${budget:.4f}")
            # Could ask for approval here, but for now we proceed

        self.logger.info(self.name, "🚀 Executing generated workflow...")

        execution_result = await self.workflow_engine.execute_workflow(
            workflow_input=workflow_input,
            budget=budget
        )

        # Step 8: Return results
        actual_cost = execution_result.get("cost_summary", {}).get("actual_cost", 0.0)

        self.logger.info(self.name, f"✅ Workflow execution complete")
        self.logger.info(self.name, f"   Actual cost: ${actual_cost:.4f}")

        return {
            "status": "success",
            "result": execution_result.get("result"),
            "workflow_used": workflow.get("name"),
            "cost": actual_cost,
            "steps_executed": len(execution_result.get("step_results", []))
        }

    async def _decompose_and_coordinate(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decompose task into subtasks, delegate subtasks, compose results.

        This implements the WORK DISTRIBUTION pattern (not delegation chains).

        Key principles:
        1. Agent does its OWN work first
        2. Agent identifies SPECIFIC subtasks to delegate
        3. Agent delegates each subtask with SPECIFIC input
        4. Agent processes/composes results
        5. Agent returns final result
        """

        self.logger.info(self.name, "🧩 Decompose & Coordinate: Starting work distribution")

        # Step 1: Identify what work THIS agent will do
        my_work = decision.parameters.get("my_work", [])
        delegate_types = decision.parameters.get("delegate", [])

        self.logger.info(self.name, f"📝 My work: {my_work}")
        self.logger.info(self.name, f"🔍 Will delegate: {delegate_types}")

        # Step 2: Plan specific subtasks (agent-specific logic)
        self.logger.info(self.name, "📋 Planning specific subtasks...")

        subtasks = await self._plan_subtasks(
            operation=operation,
            parameters=parameters,
            delegate_types=delegate_types
        )

        if not subtasks:
            self.logger.info(self.name, "   No subtasks to delegate - handling alone")
            return await self.handle_operation(operation, "self", parameters)

        self.logger.info(self.name, f"   ✅ Planned {len(subtasks)} subtasks:")
        for i, subtask in enumerate(subtasks, 1):
            self.logger.info(self.name, f"      {i}. {subtask.get('operation')} - {subtask.get('description', 'N/A')}")

        # Step 3: Execute each subtask by delegating to discovered agents
        subtask_results = []

        for i, subtask in enumerate(subtasks, 1):
            subtask_op = subtask.get("operation")
            subtask_params = subtask.get("parameters", {})
            subtask_desc = subtask.get("description", subtask_op)

            self.logger.info(self.name, f"[{i}/{len(subtasks)}] Executing subtask: {subtask_desc}")

            try:
                # Discover agent for this SPECIFIC subtask
                self.logger.info(self.name, f"   🔍 Discovering agent for operation: {subtask_op}")

                helpers = await self.discover_by_operation(subtask_op)

                if not helpers:
                    # Try fallback operations
                    fallback_ops = subtask.get("fallback_operations", [])
                    for fallback_op in fallback_ops:
                        self.logger.info(self.name, f"   🔄 Trying fallback operation: {fallback_op}")
                        helpers = await self.discover_by_operation(fallback_op)
                        if helpers:
                            subtask_op = fallback_op  # Use fallback operation
                            break

                if helpers:
                    # Select helper based on criteria
                    selection_criteria = subtask.get("selection_criteria", "balanced")
                    selected = self._select_helper(helpers, selection_criteria)

                    # Extract name from selected helper
                    helper_name = selected.get("name") or selected.get("kernel_attributes", {}).get("name", "Unknown")
                    helper_cost = selected.get("cost") or selected.get("current_cost") or selected.get("kernel_attributes", {}).get("cost", 0.0)

                    self.logger.info(self.name, f"   ✅ Selected: {helper_name} (${helper_cost:.3f})")

                    # Delegate SPECIFIC subtask (not whole task!)
                    result = await self.call_other_afdo(
                        target_pid=selected["pid"],
                        operation=subtask_op,
                        data=subtask_params
                    )

                    subtask_results.append({
                        "subtask": subtask_desc,
                        "operation": subtask_op,
                        "result": result,
                        "agent": helper_name,
                        "cost": helper_cost
                    })

                    self.logger.info(self.name, "   ✅ Subtask completed")

                else:
                    # No helpers found for this subtask
                    self.logger.warning(self.name, f"   ⚠️ No agent found for operation: {subtask_op}")

                    # Check if subtask is optional
                    if subtask.get("optional", False):
                        self.logger.info(self.name, "   ℹ️ Subtask is optional - continuing")
                        continue
                    else:
                        self.logger.warning(self.name, "   ⚠️ Subtask is required but no agent available")
                        subtask_results.append({
                            "subtask": subtask_desc,
                            "operation": subtask_op,
                            "result": None,
                            "error": "No agent available",
                            "skipped": True
                        })

            except Exception as e:
                self.logger.error(self.name, f"   ❌ Subtask failed: {e}")

                # Check failure handling
                on_failure = subtask.get("on_failure", "abort")

                if on_failure == "continue":
                    self.logger.info(self.name, "   🔄 Continuing despite failure")
                    subtask_results.append({
                        "subtask": subtask_desc,
                        "result": None,
                        "error": str(e),
                        "failed": True
                    })
                    continue
                elif on_failure == "abort":
                    self.logger.error(self.name, "   ❌ Aborting due to subtask failure")
                    raise

        # Step 4: Compose final result from subtask results
        self.logger.info(self.name, "🎨 Composing final result from subtask outputs...")

        final_result = await self._compose_results(
            operation=operation,
            original_parameters=parameters,
            subtask_results=subtask_results
        )

        self.logger.info(self.name, "✅ Decompose & Coordinate: Complete")

        return final_result

    def _determine_query_parameter_name(self, operation_schema: Dict[str, Any]) -> str:
        """
        Determine the correct parameter name for passing user query to an operation.

        Examines the operation's input_schema to find which parameter should receive
        the user query text. Handles different naming conventions (query, topic, message, etc.)

        Args:
            operation_schema: The operation's schema from capabilities

        Returns:
            Parameter name to use (defaults to 'query' if can't determine)
        """
        input_schema = operation_schema.get('input_schema', {})
        required_params = input_schema.get('required', [])
        properties = input_schema.get('properties', {})

        # Priority order for common query parameter names
        common_query_params = ['query', 'topic', 'message', 'text', 'question', 'prompt']

        # First, check required parameters for common query param names
        for param_name in common_query_params:
            if param_name in required_params and param_name in properties:
                param_info = properties[param_name]
                # Verify it's a string type (query parameters should be strings)
                if param_info.get('type') == 'string':
                    return param_name

        # If not found in common names, use first required string parameter
        for param_name in required_params:
            if param_name in properties:
                param_info = properties[param_name]
                if param_info.get('type') == 'string':
                    return param_name

        # Default fallback
        return 'query'

    async def _execute_sequence(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a sequence of steps defined in policy.

        This is a GENERIC handler - it executes ANY sequence from policy.
        Policy defines WHAT steps to execute, this code defines HOW to execute them.

        Steps can include:
        - semantic_discovery: Find agent by capability
        - delegate: Call specific agent
        - Any other action type

        Variable substitution:
        - ${variable_name} in step inputs gets replaced with stored variables
        - output_variable in step config stores result for next steps

        Example policy:
        {
          "type": "sequence",
          "parameters": {
            "steps": [
              {
                "name": "step1_analyze",
                "action": "semantic_discovery",
                "capability_query": "Analyze queries",
                "call_operation": "analyze_query_intent",
                "input": {"query": "${user_query}"},
                "output_variable": "capability_description"
              },
              {
                "name": "step2_execute",
                "action": "semantic_discovery",
                "capability_query": "${capability_description}",
                "call_best_match": true,
                "input": {"query": "${user_query}"}
              }
            ]
          }
        }
        """
        self.logger.info(self.name, "📋 Policy action: SEQUENCE")

        # Get steps from policy
        steps = decision.parameters.get("steps", [])
        if not steps:
            raise ValueError("SEQUENCE action requires 'steps' in parameters")

        # Initialize variable store with request parameters
        user_query_value = parameters.get("message") or parameters.get("query") or ""
        variables = {
            "user_query": user_query_value,
            "operation": operation,
            "parameters": parameters
        }

        # CRITICAL: Extract all individual parameters as top-level variables
        # This allows policy to use ${claim}, ${task}, etc. instead of ${parameters.claim}
        for key, value in parameters.items():
            if key not in variables:  # Don't override existing keys
                variables[key] = value

        self.logger.info(self.name, f"   Variables: user_query='{user_query_value[:50] if user_query_value else '***EMPTY***'}', params_keys={list(parameters.keys())}")
        self.logger.info(self.name, f"   Executing {len(steps)} step sequence")

        result = None

        # Execute each step in sequence
        for idx, step in enumerate(steps, 1):
            step_name = step.get("name", f"step_{idx}")
            action_type = step.get("action")

            self.logger.info(self.name, f"   📍 Step {idx}/{len(steps)}: {step_name} ({action_type})")

            # Substitute variables in step configuration
            step_config = self._substitute_variables(step, variables)
            self.logger.debug(self.name, f"      Step config after substitution: {step_config.get('input', {})}")

            # Execute step based on action type
            if action_type == "semantic_discovery":
                result = await self._execute_semantic_discovery_step(step_config, variables)
            elif action_type == "delegate":
                result = await self._execute_delegate_step(step_config, variables)
            else:
                raise ValueError(f"Unknown step action type: {action_type}")

            # Store output if variable name specified
            output_var = step.get("output_variable")
            if output_var and result:
                # Extract the relevant data from result
                if isinstance(result, dict):
                    if 'data' in result:
                        variables[output_var] = result['data']
                    elif 'result' in result:
                        variables[output_var] = result['result']
                    else:
                        variables[output_var] = result
                else:
                    variables[output_var] = result

                self.logger.debug(self.name, f"      Stored '{output_var}' = {str(variables[output_var])[:100]}")

        # Return final result
        return result

    def _substitute_variables(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively substitute ${variable_name} placeholders with values.

        Args:
            config: Configuration dict that may contain ${var} placeholders
            variables: Available variables for substitution

        Returns:
            New dict with variables substituted
        """
        import re

        def substitute_value(value):
            if isinstance(value, str):
                # Find all ${variable_name} patterns
                pattern = r'\$\{(\w+)\}'

                def replace_var(match):
                    var_name = match.group(1)
                    if var_name in variables:
                        replacement = variables[var_name]
                        # If replacement is not a string, convert it
                        if not isinstance(replacement, str):
                            return str(replacement)
                        return replacement
                    else:
                        self.logger.warning(self.name, f"      Variable '${{{var_name}}}' not found")
                        return match.group(0)  # Keep original if not found

                return re.sub(pattern, replace_var, value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value

        return substitute_value(config)

    async def _execute_semantic_discovery_step(
        self,
        step_config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a semantic_discovery step - POLICY-DRIVEN (no hardcoding).

        Step config:
        - capability_query: What capability to search for
        - call_operation: Specific operation to call (optional)
        - call_best_match: If true, call best match with input (optional)
        - input: Input data for the call

        POLICY-DRIVEN PARAMETERS (read from step_config.parameters):
        - top_k: How many agents to consider (default: 5)
        - min_similarity: Minimum score threshold (default: 0.03)
        - collect_all_results: If true, call ALL top_k agents and aggregate (default: False)
        - parallel_execution: If true, call agents in parallel (default: False)
        - min_successful: Minimum successful calls needed (default: 1)
        - operation_to_call: Operation name or 'auto_detect' (default: auto_detect)
        """
        capability_query = step_config.get("capability_query", "")
        call_operation = step_config.get("call_operation")
        call_best_match = step_config.get("call_best_match", False)
        step_input = step_config.get("input", {})

        # READ POLICY PARAMETERS (not hardcoded!)
        params = step_config.get("parameters", {})
        top_k = params.get("top_k", 5)
        min_similarity = params.get("min_similarity", 0.03)
        collect_all_results = params.get("collect_all_results", False)
        parallel_execution = params.get("parallel_execution", False)
        min_successful = params.get("min_successful", 1)
        operation_param = params.get("operation_to_call", "auto_detect")
        pass_parameters = params.get("pass_parameters", {})
        continue_if = params.get("continue_if", {})  # Policy-driven fallback conditions

        self.logger.debug(self.name, f"      Searching for: {capability_query[:100]}")
        self.logger.debug(self.name, f"      Policy: top_k={top_k}, collect_all={collect_all_results}, parallel={parallel_execution}")

        # Discover agents by capability
        discovery_results = await self.discover_by_operation_query(
            query=capability_query,
            top_k=top_k,  # From policy!
            min_score=min_similarity  # From policy!
        )

        # CRITICAL: Filter out agents with no valid operation
        # Registry sometimes returns agents with best_operation=None due to cost-weighted scoring
        # These agents cannot actually handle the request, so skip them
        valid_results = [
            r for r in discovery_results
            if r.get('best_operation') or r.get('operation')
        ]

        if valid_results:
            discovery_results = valid_results
            self.logger.debug(self.name, f"      Filtered to {len(discovery_results)} agents with valid operations")

        if not discovery_results:
            raise ValueError(f"No agents found for capability: {capability_query[:100]}")

        # POLICY-DRIVEN: Call one agent OR multiple agents?
        if not collect_all_results:
            # OLD BEHAVIOR: Call only best match (when policy says so)
            best_match = discovery_results[0]
            agent_pid = best_match['agent_pid']
            agent_name = best_match.get('agent_name', agent_pid)

            self.logger.info(self.name, f"      Found: {agent_name} (score: {best_match.get('combined_score', 0):.3f})")

            # Determine operation to call
            if call_operation:
                operation_to_call = call_operation
            elif call_best_match:
                # Use correct field name from registry response
                # CRITICAL: Use 'or' to handle None values, not just missing keys!
                # .get() returns None if value IS None, only uses default if key missing
                operation_to_call = best_match.get('best_operation') or best_match.get('operation') or 'receive_query'
            elif operation_param != "auto_detect":
                operation_to_call = operation_param
            else:
                # Just return discovery results without calling
                return {"discovery_results": discovery_results, "best_match": best_match}

            # Merge pass_parameters with step_input
            call_input = {**step_input, **pass_parameters}

            # Call the agent
            self.logger.debug(self.name, f"      Calling: {agent_name}.{operation_to_call}")

            # Log delegation event to tracer
            if self.current_tracer:
                self.current_tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="delegate",
                    operation=operation_to_call,
                    input_data=call_input,
                    delegated_to=agent_name,
                    delegated_to_pid=agent_pid,
                    notes=f"Sequence step: delegating to {agent_name}"
                )

            delegation_start = time.time()
            result = await self.call_other_afdo(
                target_pid=agent_pid,
                operation=operation_to_call,
                data=call_input
            )
            delegation_duration = int((time.time() - delegation_start) * 1000)

            # Extract cost from result
            result_cost = 0.0
            if isinstance(result, dict):
                result_cost = result.get('cost', 0.0)
                if result_cost == 0.0 and '_trace' in result:
                    trace_summary = result['_trace'].get('summary', {})
                    result_cost = trace_summary.get('total_cost', 0.0)

                if result_cost == 0.0:
                    try:
                        target_info = await self.registry_client.read_fdo(agent_pid)
                        target_data = target_info.get('data', {})
                        kernel_attrs = target_data.get('kernel_attributes', {})
                        result_cost = kernel_attrs.get('cost', 0.0)
                    except:
                        pass

            # Log result received
            if self.current_tracer:
                self.current_tracer.log_event(
                    agent_name=self.name,
                    agent_pid=self.pid,
                    action_type="receive_result",
                    operation=operation_to_call,
                    output_data={"status": "success"},
                    duration_ms=delegation_duration,
                    cost=result_cost,
                    notes=f"Received response from {agent_name} (cost: ${result_cost:.4f})"
                )

            return result

        else:
            # NEW BEHAVIOR: Multi-agent delegation (when policy says collect_all_results=true)
            self.logger.info(
                self.name,
                f"      📊 Multi-source delegation: calling {min(top_k, len(discovery_results))} agents "
                f"({'parallel' if parallel_execution else 'sequential'})"
            )

            agents_to_call = discovery_results[:top_k]
            successful_results = []
            failed_count = 0
            total_cost = 0.0

            async def call_single_agent(agent_info):
                """Helper to call a single agent."""
                agent_pid = agent_info['agent_pid']
                agent_name = agent_info.get('agent_name', agent_pid)

                # Determine operation
                if call_operation:
                    operation_to_call = call_operation
                elif operation_param != "auto_detect":
                    operation_to_call = operation_param
                else:
                    # Use correct field name from registry response
                    # CRITICAL: Use 'or' to handle None values!
                    operation_to_call = agent_info.get('best_operation') or agent_info.get('operation') or 'receive_query'

                # Merge pass_parameters with step_input
                call_input = {**step_input, **pass_parameters}

                self.logger.debug(self.name, f"        → Calling {agent_name}.{operation_to_call}")

                # Log delegation
                if self.current_tracer:
                    self.current_tracer.log_event(
                        agent_name=self.name,
                        agent_pid=self.pid,
                        action_type="delegate",
                        operation=operation_to_call,
                        input_data=call_input,
                        delegated_to=agent_name,
                        delegated_to_pid=agent_pid,
                        notes=f"Multi-source delegation to {agent_name}"
                    )

                try:
                    delegation_start = time.time()
                    result = await self.call_other_afdo(
                        target_pid=agent_pid,
                        operation=operation_to_call,
                        data=call_input
                    )
                    delegation_duration = int((time.time() - delegation_start) * 1000)

                    # Extract cost
                    result_cost = 0.0
                    if isinstance(result, dict):
                        result_cost = result.get('cost', 0.0)
                        if result_cost == 0.0 and '_trace' in result:
                            trace_summary = result['_trace'].get('summary', {})
                            result_cost = trace_summary.get('total_cost', 0.0)

                        if result_cost == 0.0:
                            try:
                                target_info = await self.registry_client.read_fdo(agent_pid)
                                target_data = target_info.get('data', {})
                                kernel_attrs = target_data.get('kernel_attributes', {})
                                result_cost = kernel_attrs.get('cost', 0.0)
                            except:
                                pass

                    # Log result
                    if self.current_tracer:
                        self.current_tracer.log_event(
                            agent_name=self.name,
                            agent_pid=self.pid,
                            action_type="receive_result",
                            operation=operation_to_call,
                            output_data={"status": "success"},
                            duration_ms=delegation_duration,
                            cost=result_cost,
                            notes=f"Received from {agent_name} (cost: ${result_cost:.4f})"
                        )

                    self.logger.debug(self.name, f"        ✓ {agent_name} succeeded (cost: ${result_cost:.4f})")

                    return {
                        "success": True,
                        "source": agent_name,
                        "source_pid": agent_pid,
                        "data": result,
                        "cost": result_cost,
                        "operation": operation_to_call
                    }

                except Exception as e:
                    self.logger.warning(self.name, f"        ✗ {agent_name} failed: {e}")
                    return {
                        "success": False,
                        "source": agent_name,
                        "source_pid": agent_pid,
                        "error": str(e)
                    }

            # Execute: Parallel or Sequential (policy-driven!)
            if parallel_execution:
                # PARALLEL: Call all agents simultaneously
                import asyncio
                results = await asyncio.gather(*[call_single_agent(agent) for agent in agents_to_call], return_exceptions=True)
            else:
                # SEQUENTIAL: Call one by one with policy-driven early stopping
                results = []
                for agent in agents_to_call:
                    result = await call_single_agent(agent)
                    results.append(result)

                    # Early stopping (policy-driven): Check if we should continue to next agent
                    if min_successful == 1 and result.get("success"):
                        should_continue = False

                        # Check continue_if conditions from policy
                        if continue_if:
                            result_data = result.get("data", {})
                            for field, expected_values in continue_if.items():
                                # Ensure expected_values is a list
                                if not isinstance(expected_values, list):
                                    expected_values = [expected_values]

                                # Check if result field matches any of the expected values
                                field_value = result_data.get(field)
                                if field_value in expected_values:
                                    should_continue = True
                                    self.logger.info(
                                        self.name,
                                        f"        🔄 Continue to next agent: {result.get('source')} returned {field}={field_value}"
                                    )
                                    break

                        # If no continue conditions matched, we have a good result - stop early
                        if not should_continue:
                            self.logger.info(
                                self.name,
                                f"        🎯 Early stop: Got good result from {result.get('source')}, skipping remaining {len(agents_to_call) - len(results)} agents"
                            )
                            break

            # Aggregate results
            for result in results:
                if isinstance(result, dict) and result.get("success"):
                    successful_results.append(result)
                    total_cost += result.get("cost", 0.0)
                else:
                    failed_count += 1

            # Check if we have enough successful results (policy-driven!)
            if len(successful_results) < min_successful:
                raise ValueError(
                    f"Multi-source delegation failed: only {len(successful_results)}/{len(agents_to_call)} succeeded "
                    f"(minimum required: {min_successful})"
                )

            self.logger.info(
                self.name,
                f"      ✅ Multi-source complete: {len(successful_results)}/{len(agents_to_call)} succeeded "
                f"(total cost: ${total_cost:.4f})"
            )

            # Return aggregated results
            return {
                "multi_source_results": successful_results,
                "successful_count": len(successful_results),
                "failed_count": failed_count,
                "total_cost": total_cost,
                "sources": [r["source"] for r in successful_results]
            }

    async def _execute_delegate_step(
        self,
        step_config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a delegate step - call specific agent directly.

        Step config:
        - target_pid: Agent PID to call
        - operation: Operation to call
        - input: Input data
        """
        target_pid = step_config.get("target_pid")
        operation = step_config.get("operation")
        step_input = step_config.get("input", {})

        if not target_pid or not operation:
            raise ValueError("delegate step requires 'target_pid' and 'operation'")

        self.logger.debug(self.name, f"      Calling: {target_pid}.{operation}")

        # Log delegation event to tracer
        if self.current_tracer:
            self.current_tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="delegate",
                operation=operation,
                input_data=step_input,
                delegated_to=target_pid,
                delegated_to_pid=target_pid,
                notes=f"Sequence step: delegating to {target_pid}"
            )

        delegation_start = time.time()
        result = await self.call_other_afdo(
            target_pid=target_pid,
            operation=operation,
            data=step_input
        )
        delegation_duration = int((time.time() - delegation_start) * 1000)

        # Extract cost from result
        result_cost = 0.0
        if isinstance(result, dict):
            # Check for cost in result or in nested trace
            result_cost = result.get('cost', 0.0)
            if result_cost == 0.0 and '_trace' in result:
                trace_summary = result['_trace'].get('summary', {})
                result_cost = trace_summary.get('total_cost', 0.0)

            # If still no cost, use the agent's declared cost as fallback
            if result_cost == 0.0:
                try:
                    target_pid = agent_pid if 'agent_pid' in locals() else target_pid
                    target_info = await self.registry_client.read_fdo(target_pid)
                    target_data = target_info.get('data', {})
                    kernel_attrs = target_data.get('kernel_attributes', {})
                    result_cost = kernel_attrs.get('cost', 0.0)
                except:
                    pass  # If lookup fails, cost remains 0.0

        # Log result received
        if self.current_tracer:
            self.current_tracer.log_event(
                agent_name=self.name,
                agent_pid=self.pid,
                action_type="receive_result",
                operation=operation,
                output_data={"status": "success"},
                duration_ms=delegation_duration,
                cost=result_cost,
                notes=f"Received response from {target_pid} (cost: ${result_cost:.4f})"
            )

        return result

    async def _semantic_discovery_and_cascade(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        NEW POLICY ACTION: Use semantic discovery to find best agent and cascade delegate.

        With resilient fallback and reputation tracking:
        1. Get user query from parameters
        2. Use operation-based semantic discovery via registry (gets top_k candidates)
        3. Try each candidate in order (sorted by reputation + similarity)
        4. On failure, try next candidate
        5. Update reputation: success → increase, failure → decrease
        6. Return first successful result

        Fully policy-driven - no hardcoded logic!
        """
        self.logger.info(self.name, "🔍 Policy action: SEMANTIC_DISCOVERY")

        # Extract query from parameters
        user_query = parameters.get("message") or parameters.get("query") or ""

        if not user_query:
            raise ValueError("SEMANTIC_DISCOVERY requires 'message' or 'query' parameter")

        # Use operation-based semantic discovery
        # Low min_score (0.03) to allow matches even with weak semantic similarity
        operation_results = await self.discover_by_operation_query(
            query=user_query,
            top_k=5,  # Get more candidates for fallback chain
            min_score=0.03
        )

        if not operation_results:
            self.logger.warning(self.name, "   ⚠️ No agents found via semantic discovery")
            raise ValueError("No agents found for query - cannot delegate")

        # Build fallback chain from semantic discovery results
        # New format: results are already ranked aFDOs with combined scores
        all_candidates = []
        for agent_result in operation_results:
            agent_pid = agent_result['agent_pid']

            # Skip self to prevent infinite recursion
            if agent_pid == self.pid:
                continue

            operation_name = agent_result['best_operation']

            # Extract operation schema from agent FDO for parameter mapping
            agent_fdo = agent_result.get('agent_fdo', {})
            self_desc = agent_fdo.get('self_description', {})
            capabilities = self_desc.get('capabilities', {})
            operation_schema = capabilities.get(operation_name, {})

            # Add candidate with operation info including schema for parameter mapping
            all_candidates.append({
                'operation': operation_name,
                'similarity_score': agent_result['combined_score'],  # Use combined score
                'agent_pid': agent_pid,
                'agent_name': agent_result['agent_name'],
                'status': agent_result.get('status'),
                'cost': agent_result.get('cost', 999),
                'reputation': agent_result.get('reputation', 0.5),
                'operation_schema': operation_schema  # Include schema for smart parameter mapping
            })

        if not all_candidates:
            raise ValueError("No suitable agents found - cannot delegate")

        # Sort candidates by: active first, then reputation (high to low), then similarity, then cost
        all_candidates.sort(
            key=lambda c: (
                c.get('status') != 'active',  # Active agents first
                -c.get('reputation', 0.5),     # Higher reputation first
                -c.get('similarity_score', 0), # Higher similarity first
                c.get('cost', 999)             # Lower cost first
            )
        )

        self.logger.info(self.name, f"   🔗 Fallback chain: {len(all_candidates)} candidates")

        # Try each candidate in order until one succeeds
        last_error = None
        for idx, candidate in enumerate(all_candidates, 1):
            agent_pid = candidate['agent_pid']
            agent_name = candidate['agent_name']
            operation_name = candidate['operation']
            similarity_score = candidate['similarity_score']
            reputation = candidate.get('reputation', 0.5)

            self.logger.info(
                self.name,
                f"   🎯 Try #{idx}: {agent_name} (op: {operation_name}, "
                f"similarity: {similarity_score:.3f}, reputation: {reputation:.2f})"
            )

            try:
                # Determine correct parameter name from operation schema
                operation_schema = candidate.get('operation_schema', {})
                param_name = self._determine_query_parameter_name(operation_schema)

                # Build data dict with correctly named parameter
                call_data = {param_name: user_query}

                # Log delegation event for trace visibility
                if self.current_tracer:
                    self.current_tracer.log_event(
                        agent_name=self.name,
                        agent_pid=self.pid,
                        action_type="delegate",
                        operation=operation_name,
                        input_data=call_data,
                        delegated_to=agent_name,
                        delegated_to_pid=agent_pid,
                        cost=candidate.get('cost', 0.0),  # Agent's base cost
                        notes=f"Cascading to {agent_name} (similarity: {similarity_score:.3f}, reputation: {reputation:.2f}, cost: ${candidate.get('cost', 0.0):.4f})"
                    )

                # Try to call the discovered operation first
                # If that fails with 404, fall back to receive_query
                result = None
                try:
                    result = await self.call_other_afdo(
                        target_pid=agent_pid,
                        operation=operation_name,
                        data=call_data
                    )
                except Exception as e:
                    # If operation not found, try receive_query as fallback
                    if "404" in str(e) or "not found" in str(e).lower():
                        self.logger.info(self.name, f"      ↻ Operation '{operation_name}' not found, trying 'receive_query'")
                        result = await self.call_other_afdo(
                            target_pid=agent_pid,
                            operation="receive_query",
                            data={"query": user_query}
                        )
                    else:
                        raise

                # Validate response: Does it contain something useful?
                response_data = result.get('data', {}) if isinstance(result, dict) else {}

                if not self._has_useful_content(response_data):
                    # Empty/useless response - treat as soft failure
                    self.logger.warning(
                        self.name,
                        f"   ⚠️ EMPTY: {agent_name} returned no useful data"
                    )

                    # Update reputation with "empty_response" outcome
                    await self._update_agent_reputation(
                        agent_pid=agent_pid,
                        operation=operation_name,
                        outcome="empty_response",
                        query=user_query,
                        error="Response contains no useful data"
                    )

                    # Continue to next candidate
                    last_error = Exception(f"{agent_name} returned empty response")
                    continue

                # Success with useful content! Update reputation positively
                await self._update_agent_reputation(
                    agent_pid=agent_pid,
                    operation=operation_name,
                    outcome="success",
                    query=user_query
                )

                self.logger.info(self.name, f"   ✅ SUCCESS: {agent_name} delivered useful result")
                return result

            except Exception as e:
                # Failure - update reputation negatively
                await self._update_agent_reputation(
                    agent_pid=agent_pid,
                    operation=operation_name,
                    outcome="failure",
                    query=user_query,
                    error=str(e)
                )

                self.logger.warning(
                    self.name,
                    f"   ❌ FAILED: {agent_name} - {str(e)[:100]}"
                )
                last_error = e

                # Continue to next candidate
                continue

        # All candidates failed
        self.logger.error(self.name, f"   ⛔ All {len(all_candidates)} candidates failed")
        raise ValueError(f"All delegation attempts failed. Last error: {last_error}")

    def _has_useful_content(self, data: Dict[str, Any]) -> bool:
        """
        Simple check: Does the response contain useful data?

        Returns False if:
        - Empty dict
        - All list fields are empty
        - All text fields are empty/whitespace
        - Low confidence score

        Args:
            data: Response data dict

        Returns:
            True if response has useful content, False if empty/useless
        """
        if not data:
            return False

        # Check confidence score if provided
        confidence = data.get('confidence')
        if confidence is not None and confidence < 0.3:
            return False

        # Common list fields that should have items
        list_fields = ['books', 'papers', 'results', 'items', 'documents', 'articles']
        has_list_content = False

        for field in list_fields:
            if field in data:
                items = data[field]
                if isinstance(items, list) and len(items) > 0:
                    has_list_content = True
                    break

        # Common text fields that should have content
        text_fields = ['answer', 'summary', 'response', 'text', 'content', 'description', 'result']
        has_text_content = False

        for field in text_fields:
            if field in data:
                text = data[field]
                if isinstance(text, str) and text.strip():
                    has_text_content = True
                    break

        # Has useful content if either lists or text are present
        return has_list_content or has_text_content

    async def _update_agent_reputation(
        self,
        agent_pid: str,
        operation: str,
        outcome: str,
        query: str = None,
        error: str = None
    ) -> None:
        """
        Update agent reputation in registry based on delegation outcome.

        Args:
            agent_pid: Agent PID
            operation: Operation that was attempted
            outcome: 'success' or 'failure'
            query: Original query (for logging)
            error: Error message if failure
        """
        try:
            # Report to registry
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.registry_url}/reputation/update",
                    json={
                        "agent_pid": agent_pid,
                        "operation": operation,
                        "outcome": outcome,
                        "reporter_pid": self.pid,
                        "query": query,
                        "error": error
                    }
                )
                response.raise_for_status()

            self.logger.debug(
                self.name,
                f"   📊 Reputation updated: {agent_pid}.{operation} → {outcome}"
            )

        except Exception as e:
            # Don't fail the whole operation if reputation update fails
            self.logger.warning(
                self.name,
                f"   ⚠️ Failed to update reputation for {agent_pid}: {e}"
            )

    def _format_response_for_ui(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format delegated agent response for UI display.

        Converts various response formats (summary, answer, papers) into
        a unified {response: str, status: str} format for the frontend.
        """
        if not isinstance(data, dict):
            return None

        # If already formatted, return as-is
        if 'response' in data and 'status' in data:
            return data

        response_text = None

        # Format based on response type
        if 'answer' in data:
            response_text = data['answer']
        elif 'summary' in data:
            # Format Wikipedia-style responses
            response_text = f"**{data.get('title', 'Result')}**\n\n{data['summary']}"
            if 'url' in data:
                response_text += f"\n\nSource: {data['url']}"
        elif 'response' in data:
            response_text = data['response']
        elif 'papers' in data:
            # Format paper list
            papers = data['papers']
            if isinstance(papers, list) and len(papers) > 0:
                response_text = f"Found {len(papers)} papers:\n\n"
                for i, paper in enumerate(papers[:5], 1):
                    title = paper.get('title', 'Untitled')
                    authors = paper.get('authors', 'Unknown authors')
                    response_text += f"{i}. **{title}**\n   Authors: {authors}\n\n"

        if response_text:
            return {
                "response": response_text,
                "status": "success"
            }

        return None

    async def _consult_llm_for_routing(
        self,
        decision: PolicyDecision,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        NEW POLICY ACTION: Ask LLM Consultant for routing advice, then delegate.

        Used by non-LLM agents when they need reasoning about where to delegate:
        1. Agent has data/results but doesn't know what to do next
        2. Consult LLM Consultant: "I have X, user wants Y, what should I do?"
        3. LLM Consultant analyzes and suggests operation/delegation
        4. Agent executes the suggestion

        Fully policy-driven - no hardcoded logic!
        """
        self.logger.info(self.name, "🤔 Policy action: CONSULT_LLM_FOR_ROUTING")

        # Build consultation query
        user_query = parameters.get("message") or parameters.get("query") or ""
        my_data = parameters.get("data") or parameters.get("results") or {}

        consultation_query = decision.parameters.get("llm_query_template",
            "User query: {user_query}\n"
            "My capabilities: {my_capabilities}\n"
            "Data I have: {my_data}\n\n"
            "Question: What operation or agent should I delegate to? "
            "Should I handle this alone or delegate? If delegate, to what agent type?"
        )

        # Format consultation query
        formatted_query = consultation_query.format(
            user_query=user_query,
            my_capabilities=", ".join(self.operations),
            my_data=str(my_data)[:200]  # Truncate for brevity
        )

        self.logger.info(self.name, f"   🔄 Consulting LLM Consultant for routing advice...")

        # Find LLM Consultant via semantic discovery
        llm_agents = await self.discover_by_operation_query(
            query="provide reasoning and analysis advice",
            top_k=1,
            min_score=0.0
        )

        if not llm_agents or len(llm_agents) == 0:
            raise ValueError("Cannot find LLM Consultant for routing advice")

        llm_operation = llm_agents[0]
        providers = llm_operation.get('providers', [])

        if not providers:
            raise ValueError("LLM Consultant has no providers")

        llm_provider = providers[0]
        llm_pid = llm_provider['agent_pid']
        llm_name = llm_provider['agent_name']

        self.logger.info(self.name, f"   ✅ Found: {llm_name}")

        # Ask LLM Consultant for advice
        advice_result = await self.call_other_afdo(
            target_pid=llm_pid,
            operation="receive_query",
            data={"query": formatted_query}
        )

        # Parse LLM advice
        advice = advice_result.get('data', {}).get('response', '')

        self.logger.info(self.name, f"   💡 LLM advice: {advice[:100]}...")

        # TODO: Parse LLM advice and execute suggested action
        # For now, return the advice for the agent to handle
        return {
            "llm_advice": advice,
            "suggested_action": "delegate",  # Parse from LLM response
            "user_query": user_query,
            "routing_decision": "consult_llm_complete"
        }

    async def _plan_subtasks(
        self,
        operation: str,
        parameters: Dict[str, Any],
        delegate_types: list
    ) -> list:
        """
        Plan specific subtasks to delegate.

        This method should be OVERRIDDEN by specific agents.
        Each agent knows how to break down its own tasks.

        Args:
            operation: Original operation
            parameters: Original parameters
            delegate_types: Types of work to delegate

        Returns:
            List of subtask definitions with operation, parameters, etc.

        Default implementation returns empty list (no subtasks).
        """

        self.logger.info(self.name, "📋 Planning subtasks (default implementation - override in subclass)")

        # Default: no subtasks
        # Subclasses should override this method

        return []

    async def _compose_results(
        self,
        operation: str,
        original_parameters: Dict[str, Any],
        subtask_results: list
    ) -> Dict[str, Any]:
        """
        Compose final result from subtask outputs.

        This method should be OVERRIDDEN by specific agents.
        Each agent knows how to compose its own results.

        Args:
            operation: Original operation
            original_parameters: Original parameters
            subtask_results: Results from subtasks

        Returns:
            Final composed result

        Default implementation just returns all subtask results.
        """

        self.logger.info(self.name, "🎨 Composing results (default implementation - override in subclass)")

        # Default: just return all results
        return {
            "operation": operation,
            "subtask_results": subtask_results,
            "subtasks_completed": sum(1 for r in subtask_results if not r.get("skipped") and not r.get("failed")),
            "subtasks_total": len(subtask_results)
        }

    def _select_helper(
        self,
        helpers: list,
        criteria: str
    ) -> Dict[str, Any]:
        """
        Select helper from candidates based on criteria.

        Args:
            helpers: List of candidate agents
            criteria: Selection criteria

        Returns:
            Selected agent
        """

        if not helpers:
            raise ValueError("No helpers available")

        if criteria == "cheapest":
            # Get cost from various possible locations
            def get_cost(h):
                return h.get("cost") or h.get("current_cost") or h.get("kernel_attributes", {}).get("cost", 1.0)
            return min(helpers, key=get_cost)

        elif criteria == "fastest":
            # Could use response time if tracked
            return helpers[0]  # For now, just return first

        elif criteria == "best_reputation":
            def get_reputation(h):
                return h.get("reputation") or h.get("kernel_attributes", {}).get("reputation", 0.5)
            return max(helpers, key=get_reputation)

        elif criteria == "balanced":
            # Balance cost and reputation
            def score(h):
                cost = h.get("cost") or h.get("current_cost") or h.get("kernel_attributes", {}).get("cost", 1.0)
                reputation = h.get("reputation") or h.get("kernel_attributes", {}).get("reputation", 0.5)
                # Higher reputation, lower cost = better score
                return reputation / max(cost, 0.01)

            return max(helpers, key=score)

        else:
            # Default: first helper
            return helpers[0]

    async def _execute_fallback(
        self,
        fallback: Dict[str, Any],
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute fallback strategy when delegation fails.

        Fallback types:
        - handle_alone: Try with own capabilities
        - return_partial: Return what we can
        - return_error: Cannot proceed
        """

        fallback_type = fallback.get("type", "handle_alone")
        fallback_params = fallback.get("parameters", {})

        if fallback_type == "handle_alone":
            self.logger.info(self.name, "🔧 Fallback: Handling with own capabilities")

            # Inform user if requested
            if fallback_params.get("inform_user"):
                self.logger.info(self.name, "ℹ️ User notification: Specialized agents unavailable, using built-in capabilities")

            # Try best effort
            try:
                result = await self.handle_operation(operation, "self", parameters)

                if fallback_params.get("best_effort"):
                    if isinstance(result, dict):
                        result["note"] = "Completed with built-in capabilities (no specialized agents available)"

                return result

            except Exception as e:
                if fallback_params.get("best_effort"):
                    # Return something even if failed
                    return {
                        "error": str(e),
                        "partial": True,
                        "note": "Could not complete fully without specialized agents"
                    }
                else:
                    raise

        elif fallback_type == "return_partial":
            self.logger.info(self.name, "⚠️ Fallback: Returning partial result")

            # Execute what we can
            try:
                result = await self.handle_operation(operation, "self", parameters)
            except Exception as e:
                result = {"error": str(e)}

            if isinstance(result, dict):
                result["partial"] = True
                result["note"] = fallback_params.get("partial_message", "Partial result - some capabilities unavailable")

            return result

        elif fallback_type == "return_error":
            self.logger.error(self.name, "❌ Fallback: Cannot proceed")

            error_msg = fallback_params.get("error_message", "Cannot complete task without required agents")
            raise ValueError(error_msg)

        else:
            raise ValueError(f"Unknown fallback type: {fallback_type}")

    async def start_heartbeat(self):
        """Start sending periodic heartbeat to registry."""
        self.logger.debug(self.name, "Heartbeat loop started")
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                await self._send_heartbeat()
            except asyncio.CancelledError:
                self.logger.info(self.name, "Heartbeat loop cancelled")
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")
                self.logger.error(self.name, f"Heartbeat error: {e}")

    async def _send_heartbeat(self):
        """Send current status to registry."""
        try:
            queue_status = self.queue_manager.get_queue_status()
            reputation_score = self.reputation_manager.calculate_score()

            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.registry_url}/status/update",
                    json={
                        "agent_pid": self.pid,
                        "queue_length": queue_status.queue_length,
                        "current_cost": queue_status.current_price,
                        "availability_status": queue_status.availability_status,
                        "current_load": queue_status.current_load,
                        "estimated_wait": queue_status.estimated_wait_time
                    }
                )

            self.logger.heartbeat(
                self.name,
                status=f"{queue_status.availability_status}, queue={queue_status.queue_length}"
            )
        except Exception as e:
            self.logger.debug(self.name, f"Heartbeat send failed: {e}")
            pass  # Non-critical

    @abstractmethod
    async def handle_operation(
        self,
        operation: str,
        caller_pid: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle an operation request.

        Subclasses must implement this to handle their specific operations.

        Args:
            operation: Operation name
            caller_pid: PID of calling aFDO
            parameters: Operation parameters

        Returns:
            Operation result
        """
        pass

    def create_app(self) -> FastAPI:
        """
        Create FastAPI application for this aFDO.

        Returns:
            FastAPI app instance
        """
        app = FastAPI(
            title=self.name,
            description=f"aFDO: {self.fdo_type}",
            version="1.0.0"
        )

        @app.on_event("startup")
        async def startup():
            """Register with registry on startup."""
            print(f"🚀 Starting {self.name}")
            print(f"📋 PID: {self.pid}")
            print(f"🔧 Operations: {', '.join(self.operations)}")

            # Log startup
            self.logger.startup(
                self.name,
                version="1.0.0",
                config={
                    "port": self.port,
                    "type": self.fdo_type,
                    "operations": len(self.operations)
                }
            )

            success = await self.register_self()
            if not success:
                print("⚠️  Registration failed, but continuing...")
                self.logger.warning(self.name, "Registration failed but continuing")

            # Load policy engine
            self.policy_engine = self._load_policy_engine()
            if self.policy_engine:
                policy_info = self.policy_engine.get_policy_info()
                print(f"🧠 Policy loaded: {policy_info['policy_id']} v{policy_info['policy_version']}")
                print(f"   {policy_info['rule_count']} rules, default: {policy_info['default_action']}")
                self.logger.info(self.name, f"Policy engine loaded: {policy_info['policy_id']}")
            else:
                print("⚠️  No policy engine - using direct execution")
                self.logger.info(self.name, "No policy engine - using direct execution")

            # Initialize protocol engines
            try:
                from shared.protocols.negotiation import NegotiationProtocol
                from shared.protocols.workflow_engine import WorkflowEngine

                self.negotiation = NegotiationProtocol(self)
                self.workflow_engine = WorkflowEngine(self)

                print("🔧 Negotiation protocol initialized")
                print("🔧 Workflow engine initialized")
                self.logger.info(self.name, "Protocol engines initialized")
            except Exception as e:
                self.logger.warning(self.name, f"Failed to initialize protocol engines: {e}")
                # Set to None if import fails
                self.negotiation = None
                self.workflow_engine = None

            # Start heartbeat task
            self.heartbeat_task = asyncio.create_task(self.start_heartbeat())
            print(f"💓 Heartbeat started")
            self.logger.info(self.name, "Heartbeat task started")

        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "name": self.name,
                "pid": self.pid,
                "type": self.fdo_type,
                "operations": self.operations,
                "status": "active"
            }

        @app.get("/metadata")
        async def get_agent_metadata():
            """Return comprehensive self-describing metadata per FDO principles."""
            return {
                "status": "success",
                "pid": self.pid,
                "metadata_pid": self.metadata_pid,
                "metadata": self.get_comprehensive_metadata()
            }

        @app.post("/doip/extend/{operation}")
        async def handle_doip_request(operation: str, request: Dict[str, Any]):
            """Handle DOIP extended operation request."""
            authentication = request.get("authentication", {})
            caller_pid = authentication.get("caller_pid", "unknown")
            parameters = request.get("parameters", {})

            # Handle protocol operations (estimate requests, approvals)
            if operation.startswith("__estimate_") and self.negotiation:
                # Extract actual operation
                actual_operation = operation.replace("__estimate_", "")

                # Provide cost estimate via negotiation protocol
                try:
                    estimate = await self.negotiation.provide_estimate(
                        caller_pid=caller_pid,
                        operation=actual_operation,
                        parameters=parameters,
                        budget_limit=parameters.get("budget_limit")
                    )
                    return {
                        "protocol_version": "2.0",
                        "status": "success",
                        "data": estimate.to_dict()
                    }
                except Exception as e:
                    self.logger.error(self.name, f"Failed to provide estimate: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

            elif operation == "__approval_decision" and self.negotiation:
                # Acknowledge approval decision
                return {
                    "protocol_version": "2.0",
                    "status": "success",
                    "data": {"status": "acknowledged"}
                }

            # Regular operation check
            if operation not in self.operations:
                error_msg = f"Operation '{operation}' not supported"
                self.logger.warning(self.name, error_msg)
                raise HTTPException(status_code=400, detail=error_msg)

            # Log operation start
            self.logger.operation_start(self.name, operation, caller_pid, parameters)

            start_time = time.time()

            try:
                # Use policy-based handling if policy engine is available
                if self.policy_engine:
                    result = await self.handle_operation_with_policy(operation, caller_pid, parameters, authentication)
                else:
                    result = await self.handle_operation(operation, caller_pid, parameters)
                duration = time.time() - start_time

                # Log successful incoming call with new structured logging
                self._log_incoming_call(
                    caller_pid=caller_pid,
                    operation=operation,
                    status="success",
                    duration=duration
                )

                # Create result summary for logging
                result_summary = ""
                if isinstance(result, dict):
                    if "status" in result:
                        result_summary = f"status={result['status']}"
                    elif "message" in result:
                        msg = result["message"]
                        result_summary = f"message={msg[:50]}..." if len(msg) > 50 else f"message={msg}"

                self.logger.operation_success(self.name, operation, duration, result_summary)

                # If result is already in DOIP format, return it as-is (avoid double-wrapping)
                if isinstance(result, dict) and 'protocol_version' in result and 'status' in result:
                    return result

                # Otherwise, wrap in DOIP format
                return {
                    "protocol_version": "2.0",
                    "status": "success",
                    "data": result
                }

            except Exception as e:
                duration = time.time() - start_time

                # Log failed incoming call with new structured logging
                self._log_incoming_call(
                    caller_pid=caller_pid,
                    operation=operation,
                    status="failed",
                    duration=duration,
                    error=str(e)
                )

                self.logger.operation_error(self.name, operation, str(e), duration)

                raise HTTPException(status_code=500, detail=str(e))

        # MARKETPLACE ENDPOINTS

        @app.post("/marketplace/quote")
        async def request_quote(quote_request: Dict[str, Any]):
            """Provide a quote for an operation."""
            operation = quote_request.get("operation")
            parameters = quote_request.get("parameters", {})
            priority = quote_request.get("priority", "normal")

            if not operation:
                raise HTTPException(status_code=400, detail="operation required")

            try:
                quote = await self.get_quote(operation, parameters, priority)
                return {
                    "status": "success",
                    "quote": quote.to_dict()
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/marketplace/negotiate")
        async def negotiate_terms(negotiation_request: Dict[str, Any]):
            """Negotiate terms for an operation."""
            try:
                # Convert dict to QuoteRequest
                quote_req = QuoteRequest(
                    operation=negotiation_request.get("operation"),
                    parameters=negotiation_request.get("parameters", {}),
                    max_budget=negotiation_request.get("max_budget", 0.0),
                    priority=negotiation_request.get("priority", "normal"),
                    caller_pid=negotiation_request.get("caller_pid")
                )

                result = await self.negotiate(quote_req)

                return {
                    "status": "success",
                    "negotiation": result.to_dict()
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/marketplace/status")
        async def get_marketplace_status():
            """Get current marketplace status (queue, pricing, reputation)."""
            queue_status = self.queue_manager.get_queue_status()
            reputation_score = self.reputation_manager.calculate_score()

            return {
                "status": "success",
                "data": {
                    "pid": self.pid,
                    "queue_length": queue_status.queue_length,
                    "current_price": queue_status.current_price,
                    "base_price": queue_status.base_price,
                    "price_multiplier": queue_status.price_multiplier,
                    "availability_status": queue_status.availability_status,
                    "estimated_wait": queue_status.estimated_wait_time,
                    "reputation_score": reputation_score,
                    "performance_stats": self.queue_manager.get_performance_stats()
                }
            }

        self.app = app
        return app

    def run(self):
        """Run this aFDO's server."""
        if not self.app:
            self.create_app()

        print(f"\n{'='*60}")
        print(f"🚀 Starting {self.name}")
        print(f"📡 Port: {self.port}")
        print(f"🌐 URL: {self.base_url}")
        print(f"{'='*60}\n")

        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
