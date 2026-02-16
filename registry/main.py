"""FDO Registry System - Main FastAPI application."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any
import uvicorn
import asyncio
import time

from shared.utils import generate_pid, current_timestamp
from shared.logging_config import get_logger
from shared.fdo_schemas import SELF_DESCRIPTION_SCHEMA
from shared.job_tracker import get_job_tracker
import jsonschema
from registry.file_storage import FileBasedStorage
from registry.models import (
    DOIPRequest, DOIPResponse,
    FDOProfile, FDOType, Operation, MetadataSchema,
    FDORecord, MetadataRecord
)
from registry.event_broadcaster import EventBroadcaster

# Marketplace data structures
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="FDO Registry System",
    description="Central registry for Autonomous FAIR Digital Objects",
    version="1.0.0"
)

# Initialize storage
storage = FileBasedStorage(base_dir="registry/data")

# Initialize event broadcaster
broadcaster = EventBroadcaster()

# Initialize logger
logger = get_logger()

# Registry's own metadata
REGISTRY_METADATA = {
    "pid": "21.T11148/registry-system-001",
    "name": "FDO Registry System",
    "version": "1.0.0",
    "operations": ["create", "read", "update", "delete", "search"]
}

# Marketplace state (in-memory for now, can be persisted later)
agent_status_cache: Dict[str, Dict[str, Any]] = {}
reputation_cache: Dict[str, Dict[str, Any]] = {}
failure_reports: List[Dict[str, Any]] = []

# Heartbeat and cleanup configuration
HEARTBEAT_TIMEOUT = 60  # Mark inactive after 60 seconds without heartbeat
CLEANUP_THRESHOLD = 24 * 60 * 60  # Delete after 24 hours of inactivity
CLEANUP_INTERVAL = 60  # Run cleanup every 60 seconds


async def cleanup_inactive_fdos():
    """Background task to mark inactive FDOs and clean up old ones."""
    while True:
        try:
            current_time = time.time()
            fdos = storage.search_fdos()

            for fdo in fdos:
                pid = fdo.pid
                if not pid:
                    continue

                # Get last heartbeat timestamp
                last_heartbeat = fdo.last_heartbeat or 0
                current_status = fdo.status or 'unknown'
                inactive_since = fdo.inactive_since

                # Calculate time since last heartbeat
                time_since_heartbeat = current_time - last_heartbeat if last_heartbeat else float('inf')

                # Mark as inactive if no heartbeat for HEARTBEAT_TIMEOUT seconds
                if time_since_heartbeat > HEARTBEAT_TIMEOUT and current_status == 'active':
                    updates = {
                        'status': 'inactive',
                        'inactive_since': current_time
                    }
                    storage.update_fdo(pid, updates)
                    print(f"⏸️  Marked FDO {pid} as inactive (no heartbeat for {time_since_heartbeat:.0f}s)")
                    logger.warning("Registry", f"Marked {pid} as inactive (no heartbeat for {time_since_heartbeat:.0f}s)")

                # Delete if inactive for more than CLEANUP_THRESHOLD
                elif current_status == 'inactive' and inactive_since:
                    time_inactive = current_time - inactive_since
                    if time_inactive > CLEANUP_THRESHOLD:
                        try:
                            storage.delete_fdo(pid)
                            # Also delete associated metadata
                            metadata_pid = fdo.metadata_pointer
                            if metadata_pid:
                                try:
                                    storage.delete_metadata(metadata_pid)
                                except:
                                    pass
                            print(f"🗑️  Deleted FDO {pid} (inactive for {time_inactive / 3600:.1f} hours)")
                            logger.info("Registry", f"Deleted FDO {pid} (inactive for {time_inactive / 3600:.1f} hours)")
                        except Exception as e:
                            print(f"⚠️  Failed to delete FDO {pid}: {e}")
                            logger.error("Registry", f"Failed to delete FDO {pid}: {e}")

        except Exception as e:
            print(f"⚠️  Cleanup task error: {e}")

        # Run cleanup every CLEANUP_INTERVAL seconds
        await asyncio.sleep(CLEANUP_INTERVAL)


@app.on_event("startup")
async def startup_event():
    """Initialize registry on startup."""
    print("🚀 FDO Registry System starting...")
    print(f"📋 Registry PID: {REGISTRY_METADATA['pid']}")
    print(f"🔧 Operations: {', '.join(REGISTRY_METADATA['operations'])}")

    # Log registry startup
    logger.startup(
        "Registry",
        version=REGISTRY_METADATA["version"],
        config={
            "port": 8000,
            "heartbeat_timeout": HEARTBEAT_TIMEOUT,
            "cleanup_threshold_hours": CLEANUP_THRESHOLD / 3600
        }
    )

    # DEBUG: Check types on startup
    types_count = len(storage.list_types())
    print(f"📊 DEBUG: Storage has {types_count} types on startup")
    logger.info("Registry", f"Storage initialized with {types_count} types")

    # Initialize with default ai_agent_v1 profile
    default_profile = FDOProfile(
        pid=generate_pid() + "-profile-ai-agent",
        name="ai_agent_v1",
        description="Standard AI agent profile",
        required_attributes=["pid", "operations", "reputation", "cost"],
        optional_attributes=["specialization", "llm_model"],
        created_at=current_timestamp()
    )
    storage.create_profile(default_profile)
    print(f"✅ Created default profile: {default_profile.name}")
    logger.info("Registry", f"Created default profile: {default_profile.name}")

    # Start background cleanup task
    asyncio.create_task(cleanup_inactive_fdos())
    print(f"🧹 Started FDO cleanup task (inactive timeout: {HEARTBEAT_TIMEOUT}s, delete after: {CLEANUP_THRESHOLD / 3600:.0f}h)")
    logger.info("Registry", f"Started FDO cleanup task (inactive: {HEARTBEAT_TIMEOUT}s, delete: {CLEANUP_THRESHOLD/3600:.0f}h)")

    # Pre-load embedding model to avoid cold start delays
    print("🔄 Pre-loading sentence-transformer model...")
    logger.info("Registry", "Pre-loading embedding model for semantic discovery")
    from sentence_transformers import SentenceTransformer
    app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Embedding model loaded and ready")
    logger.info("Registry", "Embedding model loaded successfully")


@app.get("/")
async def root():
    """Root endpoint - registry info."""
    # Count unique type strings actually in use (not FDOType objects)
    fdos = storage.search_fdos()
    unique_types = len(set(fdo.fdo_type_pid for fdo in fdos))

    return {
        "service": "FDO Registry System",
        "pid": REGISTRY_METADATA["pid"],
        "status": "active",
        "stats": {
            "profiles": len(storage.list_profiles()),
            "types": unique_types,  # Count unique type strings in use
            "operations": len(storage.search_operations()),
            "fdos": len(fdos),
            "metadata": len(list(storage.metadata_dir.glob("*.json")))
        }
    }


# DOIP OPERATIONS

@app.post("/doip/create/profile")
async def create_profile(profile: FDOProfile):
    """DOIP Create - Profile."""
    try:
        result = storage.create_profile(profile)
        return DOIPResponse(
            status="success",
            message="Profile created",
            data=result.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/doip/create/type")
async def create_type(fdo_type: FDOType):
    """DOIP Create - Type."""
    try:
        result = storage.create_type(fdo_type)
        return DOIPResponse(
            status="success",
            message="Type created",
            data=result.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/doip/create/operation")
async def create_operation(operation: Operation):
    """DOIP Create - Operation."""
    try:
        result = storage.create_operation(operation)
        return DOIPResponse(
            status="success",
            message="Operation created",
            data=result.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/doip/update/operation/{pid:path}")
async def update_operation(pid: str, operation: Operation):
    """DOIP Update - Operation."""
    try:
        result = storage.update_operation(pid, operation)
        if not result:
            raise HTTPException(status_code=404, detail=f"Operation {pid} not found")
        return DOIPResponse(
            status="success",
            message="Operation updated",
            data=result.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/doip/create/fdo")
async def create_fdo(fdo: FDORecord):
    """DOIP Create - FDO Record."""
    try:
        agent_name = fdo.kernel_attributes.get("name", "Unknown")
        port = fdo.kernel_attributes.get("port", "?")

        logger.info("Registry", f"Registering FDO: {fdo.pid} ({agent_name}) on port {port}")

        # Validate type exists
        if fdo.fdo_type_pid:
            type_record = storage.get_type(fdo.fdo_type_pid)
            if not type_record:
                logger.error("Registry", f"❌ Type {fdo.fdo_type_pid} not found")
                raise HTTPException(
                    status_code=400,
                    detail=f"Type {fdo.fdo_type_pid} does not exist. Run scripts/initialize_types.py first."
                )

            # Validate agent has required capabilities
            expected_capabilities = type_record.get("expected_capabilities", [])
            if expected_capabilities and hasattr(fdo, 'self_description') and fdo.self_description:
                agent_capabilities = list(fdo.self_description.get("capabilities", {}).keys())

                missing_capabilities = set(expected_capabilities) - set(agent_capabilities)
                if missing_capabilities:
                    logger.error("Registry", f"❌ Agent {fdo.pid} missing capabilities: {missing_capabilities}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent missing required capabilities for type {fdo.fdo_type_pid}: {list(missing_capabilities)}"
                    )

            logger.info("Registry", f"✅ Type validation passed for {fdo.pid}")

        # Validate profile exists
        if fdo.fdo_profile_pid:
            profile_record = storage.get_profile(fdo.fdo_profile_pid)
            if not profile_record:
                logger.error("Registry", f"❌ Profile {fdo.fdo_profile_pid} not found")
                raise HTTPException(
                    status_code=400,
                    detail=f"Profile {fdo.fdo_profile_pid} does not exist. Run scripts/initialize_types.py first."
                )

            logger.info("Registry", f"✅ Profile validation passed for {fdo.pid}")

        # Validate self_description if present
        if hasattr(fdo, 'self_description') and fdo.self_description is not None:
            try:
                jsonschema.validate(
                    instance=fdo.self_description,
                    schema=SELF_DESCRIPTION_SCHEMA
                )
                logger.info("Registry", f"✅ Self-description validated for {fdo.pid}")
            except jsonschema.ValidationError as e:
                logger.error("Registry", f"❌ Invalid self-description for {fdo.pid}: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid self_description: {e.message}"
                )
        else:
            logger.warning("Registry", f"⚠️  FDO {fdo.pid} has no self_description")

        result = storage.create_fdo(fdo)

        # Log successful registration
        logger.registration(
            "Registry",
            result.pid,
            result.kernel_attributes.get("port", 0),
            result.operation_pids
        )

        # Broadcast registration event
        await broadcaster.broadcast("fdo_registered", {
            "pid": result.pid,
            "fdo_type": result.fdo_type_pid,
            "port": result.kernel_attributes.get("port"),
            "operations": result.operation_pids
        })

        return DOIPResponse(
            status="success",
            message="FDO created",
            data=result.dict()
        )
    except ValueError as e:
        logger.error("Registry", f"FDO creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/doip/create/metadata")
async def create_metadata(metadata: MetadataRecord):
    """DOIP Create - Metadata."""
    try:
        result = storage.create_metadata(metadata)
        return DOIPResponse(
            status="success",
            message="Metadata created",
            data=result.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/doip/read/fdo/{pid:path}")
async def read_fdo(pid: str):
    """DOIP Read - Get FDO by PID."""
    fdo = storage.get_fdo(pid)
    if not fdo:
        raise HTTPException(status_code=404, detail=f"FDO {pid} not found")

    return DOIPResponse(
        status="success",
        data=fdo.dict()
    )


@app.get("/doip/read/metadata/{pid:path}")
async def read_metadata(pid: str):
    """DOIP Read - Get Metadata by PID."""
    metadata = storage.get_metadata(pid)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata {pid} not found")

    return DOIPResponse(
        status="success",
        data=metadata.dict()
    )


@app.get("/doip/search/fdos")
async def search_fdos_get():
    """DOIP Search - Get all FDOs (GET method for monitor)."""
    results = storage.search_fdos()
    return DOIPResponse(
        status="success",
        message=f"Found {len(results)} FDOs",
        data=[fdo.dict() for fdo in results]
    )


@app.post("/doip/search/fdos")
async def search_fdos(
    fdo_type: Optional[str] = None,
    operation: Optional[str] = None,
    profile: Optional[str] = None
):
    """DOIP Search - Find FDOs by criteria."""
    results = storage.search_fdos(
        fdo_type=fdo_type,
        operation=operation,
        profile=profile
    )

    # Broadcast discovery event
    await broadcaster.broadcast("discovery_request", {
        "query_type": "by_type" if fdo_type else ("by_operation" if operation else "by_profile"),
        "query_value": fdo_type or operation or profile,
        "results_count": len(results)
    })

    return DOIPResponse(
        status="success",
        message=f"Found {len(results)} FDOs",
        data=[fdo.dict() for fdo in results]
    )


@app.get("/doip/search/fdos/active")
async def search_active_fdos():
    """DOIP Search - Find only active FDOs (with recent heartbeats)."""
    all_fdos = storage.search_fdos()
    current_time = time.time()

    # Filter for active FDOs (status='active' or heartbeat within timeout)
    active_fdos = []
    for fdo in all_fdos:
        status = fdo.status or 'unknown'
        last_heartbeat = fdo.last_heartbeat or 0
        time_since_heartbeat = current_time - last_heartbeat if last_heartbeat else float('inf')

        # Consider active if status is 'active' or heartbeat is recent
        if status == 'active' or time_since_heartbeat <= HEARTBEAT_TIMEOUT:
            active_fdos.append(fdo)

    return DOIPResponse(
        status="success",
        message=f"Found {len(active_fdos)} active FDOs",
        data=[fdo.dict() for fdo in active_fdos]
    )


@app.post("/doip/search/operations")
async def search_operations(name: Optional[str] = None):
    """DOIP Search - Find operations."""
    results = storage.search_operations(name=name)

    return DOIPResponse(
        status="success",
        message=f"Found {len(results)} operations",
        data=[op.dict() for op in results]
    )


@app.post("/doip/discover/by_query")
async def discover_by_query(request: Dict[str, Any]):
    """
    Semantic discovery: Find agents that can help with a user query.

    This endpoint uses vector embeddings to semantically match the user's query
    against agent descriptions, returning ranked agents by relevance.

    Args:
        request: {
            "query": str,           # User's natural language query
            "top_k": int,           # Number of agents to return (default: 5)
            "min_score": float      # Minimum similarity score (default: 0.0)
        }

    Returns:
        Ranked list of agents with similarity scores
    """
    from sentence_transformers import SentenceTransformer
    import numpy as np

    # Extract parameters
    query = request.get("query")
    top_k = request.get("top_k", 5)
    min_score = request.get("min_score", 0.0)

    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Load embedding model (cached after first load)
    if not hasattr(app.state, 'embedding_model'):
        logger.info("Registry", "🔄 Loading sentence-transformer model for semantic discovery...")
        app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Registry", "✅ Embedding model loaded")

    model = app.state.embedding_model

    # Get all active agents
    all_fdos = storage.search_fdos()
    current_time = time.time()

    active_agents = []
    for fdo in all_fdos:
        # Filter for active agents only
        status = fdo.status or 'unknown'
        last_heartbeat = fdo.last_heartbeat or 0
        time_since_heartbeat = current_time - last_heartbeat if last_heartbeat else float('inf')

        if status == 'active' or time_since_heartbeat <= HEARTBEAT_TIMEOUT:
            # Extract agent description (nested in agent_info)
            self_desc = fdo.self_description or {}
            agent_info = self_desc.get('agent_info', {})
            description = agent_info.get('description', '')
            name = agent_info.get('name', fdo.pid)

            # Skip if no description
            if not description:
                continue

            active_agents.append({
                'fdo': fdo,
                'name': name,
                'description': description,
                'pid': fdo.pid
            })

    if not active_agents:
        return DOIPResponse(
            status="success",
            message="No active agents with descriptions found",
            data=[]
        )

    # Generate embeddings
    query_embedding = model.encode(query, convert_to_tensor=False)
    descriptions = [agent['description'] for agent in active_agents]
    description_embeddings = model.encode(descriptions, convert_to_tensor=False)

    # Compute cosine similarity
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # Calculate similarity scores
    results = []
    for i, agent in enumerate(active_agents):
        similarity = cosine_similarity(query_embedding, description_embeddings[i])

        # Skip if below minimum score
        if similarity < min_score:
            continue

        results.append({
            'agent': agent['fdo'].dict(),
            'similarity_score': float(similarity),
            'name': agent['name'],
            'description': agent['description'],
            'pid': agent['pid']
        })

    # Sort by similarity score (descending)
    results.sort(key=lambda x: x['similarity_score'], reverse=True)

    # Return top_k results
    results = results[:top_k]

    logger.info("Registry", f"🔍 Semantic discovery: '{query}' → Found {len(results)} matching agents")

    # Broadcast discovery event
    await broadcaster.broadcast("semantic_discovery", {
        "query": query,
        "num_results": len(results),
        "top_match": results[0]['name'] if results else None,
        "top_score": results[0]['similarity_score'] if results else 0
    })

    return DOIPResponse(
        status="success",
        message=f"Found {len(results)} matching agents",
        data=results
    )


@app.post("/doip/discover/by_operation_query")
async def discover_by_operation_query(request: Dict[str, Any]):
    """
    Operation-based semantic discovery: Find operations that match a user query.

    This endpoint searches OPERATIONS (not agents) using semantic matching,
    then returns the matching operations along with all agents that provide them.

    This is more granular and accurate than agent-based discovery because:
    - Operations have specific, focused descriptions
    - Multiple agents can provide the same operation
    - Prevents cross-domain confusion (papers vs facts)

    Args:
        request: {
            "query": str,           # User's natural language query
            "top_k": int,           # Number of operations to return (default: 5)
            "min_score": float      # Minimum similarity score (default: 0.0)
        }

    Returns:
        Ranked list of operations with their providers:
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
    from sentence_transformers import SentenceTransformer
    import numpy as np

    # Extract parameters
    query = request.get("query")
    top_k = request.get("top_k", 5)
    min_score = request.get("min_score", 0.0)

    print(f"DEBUG: Received query='{query}', top_k={top_k}, min_score={min_score}")

    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Load embedding model (cached after first load)
    if not hasattr(app.state, 'embedding_model'):
        logger.info("Registry", "🔄 Loading sentence-transformer model for operation-based discovery...")
        app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Registry", "✅ Embedding model loaded")

    model = app.state.embedding_model

    # Build indexes from all active agents
    all_fdos = storage.search_fdos()
    current_time = time.time()

    print(f"DEBUG: Found {len(all_fdos)} FDOs total")

    # Index 1: Operations (operation_name -> description)
    operations_index = {}

    # Index 2: aFDOs (agent_pid -> {agent_description, operations, ...})
    afdos_index = {}

    for fdo in all_fdos:
        # Filter for active agents only
        status = fdo.status or 'unknown'
        last_heartbeat = fdo.last_heartbeat or 0
        time_since_heartbeat = current_time - last_heartbeat if last_heartbeat else float('inf')

        # Debug: print filtering decision
        print(f"DEBUG: {fdo.pid}: status={status}, heartbeat_age={time_since_heartbeat:.1f}s, will_skip={status != 'active' and time_since_heartbeat > HEARTBEAT_TIMEOUT}")

        if status != 'active' and time_since_heartbeat > HEARTBEAT_TIMEOUT:
            continue

        # Extract agent info
        self_desc = fdo.self_description or {}
        agent_info = self_desc.get('agent_info', {})
        agent_name = agent_info.get('name', fdo.pid)
        agent_description = agent_info.get('description', '')
        capabilities = self_desc.get('capabilities', {})

        # Extract cost from kernel_attributes
        kernel_attrs = fdo.kernel_attributes or {}
        agent_cost = kernel_attrs.get('cost', 0.0)

        # Get reputation for this agent
        rep_data = reputation_cache.get(fdo.pid, {})
        reputation_score = rep_data.get('score', 0.5)

        # Index the aFDO with its agent-level description
        afdos_index[fdo.pid] = {
            'agent_pid': fdo.pid,
            'agent_name': agent_name,
            'agent_description': agent_description,
            'operations': list(capabilities.keys()),
            'cost': agent_cost,
            'status': status,
            'reputation': reputation_score,
            'agent_fdo': fdo.dict()
        }

        # Index each operation this agent provides
        for op_name, op_spec in capabilities.items():
            op_description = op_spec.get('description', '')

            # Skip if no description
            if not op_description:
                continue

            # Store operation description (first one wins if multiple agents provide same operation)
            if op_name not in operations_index:
                operations_index[op_name] = op_description

    if not afdos_index:
        return DOIPResponse(
            status="success",
            message="No active aFDOs found",
            data=[]
        )

    # Debug: log indexed aFDOs
    logger.info("Registry", f"📊 Indexed {len(afdos_index)} aFDOs: {list(afdos_index.keys())}")
    logger.info("Registry", f"📊 Indexed {len(operations_index)} operations: {list(operations_index.keys())}")

    # Generate embeddings for query
    query_embedding = model.encode(query, convert_to_tensor=False)

    # Compute cosine similarity
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # Calculate combined scores for each aFDO
    results = []

    # Step 1: Find c_max for cost normalization (Algorithm 1, line 2)
    c_max = max((agent_data['cost'] for agent_data in afdos_index.values()), default=1.0)
    if c_max == 0:
        c_max = 1.0  # Avoid division by zero

    # Multi-objective scoring weights (α + β + γ = 1)
    # α: semantic similarity weight
    # β: reputation weight
    # γ: cost penalty weight
    ALPHA = 0.6  # Semantic similarity (most important)
    BETA = 0.3   # Reputation (quality matters)
    GAMMA = 0.1  # Cost penalty (prefer cheaper, but not critical)

    for agent_pid, agent_data in afdos_index.items():
        try:
            # Score 1: Match against aFDO description (s^agent_i)
            agent_desc = agent_data['agent_description']
            if agent_desc:
                agent_embedding = model.encode(agent_desc, convert_to_tensor=False)
                agent_score = cosine_similarity(query_embedding, agent_embedding)
            else:
                agent_score = 0.0
                logger.debug("Registry", f"   ⚠️ {agent_data['agent_name']}: No agent description")

            # Score 2: Match against operation descriptions (s^op_{i,j})
            operation_scores = []
            for op_name in agent_data['operations']:
                if op_name in operations_index:
                    op_desc = operations_index[op_name]
                    op_embedding = model.encode(op_desc, convert_to_tensor=False)
                    op_score = cosine_similarity(query_embedding, op_embedding)
                    operation_scores.append((op_name, op_score, op_desc))

            # Sort operations by score (descending)
            operation_scores.sort(key=lambda x: x[1], reverse=True)

            # Get best operation for display and scoring
            best_operation = None
            best_op_desc = ""
            best_op_score = 0.0
            if operation_scores:
                best_operation = operation_scores[0][0]
                best_op_score = operation_scores[0][1]
                best_op_desc = operation_scores[0][2]

            # Paper's Algorithm 1, Line 8: s_{i,j} = max(s^op_{i,j}, s^agent_i)
            # Take MAX of best operation score and agent score
            semantic_similarity = max(best_op_score, agent_score)

            # Get reputation and cost
            reputation = agent_data['reputation']  # r_i in [0,1]
            cost = agent_data['cost']  # c_{i,j}

            # Paper's Algorithm 1, Line 11: Multi-objective score
            # score(a_i, o_{i,j}) = α·s_{i,j} + β·r_i - γ·(c_{i,j}/c_max)
            multi_objective_score = (
                ALPHA * semantic_similarity +
                BETA * reputation -
                GAMMA * (cost / c_max)
            )

            # Debug: log all score components
            logger.info("Registry",
                f"   📊 {agent_data['agent_name']}: "
                f"sem={semantic_similarity:.4f} (max(agent={agent_score:.4f}, best_op={best_op_score:.4f})), "
                f"rep={reputation:.3f}, cost=${cost:.4f}, "
                f"final={multi_objective_score:.4f}")

            # Skip if below minimum score (now using semantic similarity for threshold)
            if semantic_similarity < min_score:
                logger.debug("Registry", f"   ⚠️ Skipping {agent_data['agent_name']} (semantic similarity {semantic_similarity:.4f} < min {min_score})")
                continue

            results.append({
                'agent_pid': agent_pid,
                'agent_name': agent_data['agent_name'],
                'agent_description': agent_desc,
                'best_operation': best_operation,
                'operation_description': best_op_desc,
                'agent_score': float(agent_score),
                'best_operation_score': float(best_op_score),
                'semantic_similarity': float(semantic_similarity),  # s_{i,j} = max(op, agent)
                'num_matching_operations': len(operation_scores),
                'combined_score': float(multi_objective_score),  # α·s + β·r - γ·c
                'cost': agent_data['cost'],
                'cost_normalized': float(cost / c_max),
                'status': agent_data['status'],
                'reputation': agent_data['reputation'],
                'agent_fdo': agent_data['agent_fdo'],
                # Store weights for transparency
                'scoring_weights': {'alpha': ALPHA, 'beta': BETA, 'gamma': GAMMA}
            })
            logger.info("Registry", f"   ✅ ADDED {agent_data['agent_name']} to results (multi-objective score: {multi_objective_score:.4f})")
        except Exception as e:
            logger.error("Registry", f"   ❌ Error scoring {agent_data.get('agent_name', agent_pid)}: {e}")

    # Sort by combined score (descending)
    logger.info("Registry", f"📋 Before sort: {len(results)} agents in results")
    for r in results:
        logger.info("Registry", f"   - {r['agent_name']}: {r['combined_score']:.4f}")

    results.sort(key=lambda x: x['combined_score'], reverse=True)

    logger.info("Registry", f"📋 After sort, before top_k filter: {len(results)} agents")
    for r in results:
        logger.info("Registry", f"   - {r['agent_name']}: {r['combined_score']:.4f}")

    # Return top_k results
    results = results[:top_k]

    logger.info("Registry", f"📋 Final results after top_k={top_k}: {len(results)} agents")
    for r in results:
        logger.info("Registry", f"   - {r['agent_name']}: {r['combined_score']:.4f}")

    logger.info("Registry", f"🔍 Operation-based discovery: '{query}' → Found {len(results)} matching aFDOs")

    # Log top matches with multi-objective breakdown
    for i, result in enumerate(results[:3], 1):
        weights = result['scoring_weights']
        logger.info("Registry",
            f"   {i}. {result['agent_name']} "
            f"(score: {result['combined_score']:.3f} = "
            f"{weights['alpha']}·sem:{result['semantic_similarity']:.3f} + "
            f"{weights['beta']}·rep:{result['reputation']:.3f} - "
            f"{weights['gamma']}·cost:{result['cost_normalized']:.3f}, "
            f"best_op: {result['best_operation']})")

    # Broadcast discovery event
    await broadcaster.broadcast("operation_discovery", {
        "query": query,
        "num_afdos": len(results),
        "top_agent": results[0]['agent_name'] if results else None,
        "top_score": results[0]['combined_score'] if results else 0
    })

    return DOIPResponse(
        status="success",
        message=f"Found {len(results)} matching aFDOs",
        data=results
    )


@app.delete("/doip/delete/fdo/{pid:path}")
async def delete_fdo(pid: str):
    """DOIP Delete - Remove FDO."""
    success = storage.delete_fdo(pid)
    if not success:
        raise HTTPException(status_code=404, detail=f"FDO {pid} not found")

    return DOIPResponse(
        status="success",
        message=f"FDO {pid} deleted"
    )


@app.patch("/registry/fdos/{pid:path}/field/{field_name}")
async def update_fdo_field(pid: str, field_name: str, request: Dict[str, Any]):
    """
    Update a single field in FDO record.

    Used for incremental updates like activity logs.
    """
    new_value = request.get("value")

    if new_value is None:
        raise HTTPException(status_code=400, detail="Missing 'value' in request body")

    # Load FDO
    fdo = storage.get_fdo(pid)
    if not fdo:
        raise HTTPException(status_code=404, detail=f"FDO {pid} not found")

    # Update field
    updates = {
        field_name: new_value,
        "updated_at": current_timestamp()
    }
    storage.update_fdo(pid, updates)

    logger.debug("Registry", f"Updated field '{field_name}' for FDO {pid}")

    return {
        "status": "success",
        "pid": pid,
        "field": field_name,
        "message": f"Field '{field_name}' updated successfully"
    }


@app.get("/registry/fdos/{pid:path}/activity_log")
async def get_activity_log(pid: str):
    """Get activity log for a specific FDO."""
    # Load FDO
    fdo = storage.get_fdo(pid)
    if not fdo:
        raise HTTPException(status_code=404, detail=f"FDO {pid} not found")

    activity_log = fdo.get("activity_log", {"calls_made": [], "calls_received": []})

    # Ensure proper structure
    if isinstance(activity_log, list):
        # Old format, convert to new
        activity_log = {"calls_made": [], "calls_received": []}

    logger.debug("Registry", f"Retrieved activity log for FDO {pid}")

    return {
        "status": "success",
        "pid": pid,
        "activity_log": activity_log
    }


@app.get("/registry/fdos/{pid:path}/self_description")
async def get_self_description(pid: str):
    """Get self-description for a specific FDO."""
    try:
        fdo = storage.get_fdo(pid)
        if not fdo:
            raise HTTPException(status_code=404, detail=f"FDO {pid} not found")

        # Get self_description (could be dict attribute or nested in fdo dict)
        if hasattr(fdo, 'self_description'):
            self_description = fdo.self_description
        elif isinstance(fdo, dict):
            self_description = fdo.get("self_description")
        else:
            self_description = None

        if self_description is None:
            raise HTTPException(
                status_code=404,
                detail=f"FDO {pid} has no self_description"
            )

        return {
            "status": "success",
            "pid": pid,
            "self_description": self_description
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registry", f"Error getting self-description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# TYPE AND PROFILE ENDPOINTS

@app.get("/registry/types")
async def list_types():
    """List all type FDO records."""
    import sys
    sys.stderr.write(">>>>  ENDPOINT CALLED! <<<<\n")
    sys.stderr.flush()
    logger.info("Registry", "🔍 list_types endpoint called")
    types = storage.list_types()
    sys.stderr.write(f">>>> GOT {len(types)} TYPES <<<<\n")
    sys.stderr.flush()
    logger.info("Registry", f"🔍 Got {len(types)} types from storage.list_types()")
    return {
        "status": "success",
        "count": len(types),
        "types": types
    }


@app.get("/registry/types/{type_pid:path}")
async def get_type(type_pid: str):
    """Get specific type FDO record."""
    type_record = storage.get_type(type_pid)
    if not type_record:
        raise HTTPException(status_code=404, detail=f"Type {type_pid} not found")

    return {
        "status": "success",
        "type": type_record
    }


@app.get("/registry/profiles")
async def list_profiles():
    """List all profile FDO records."""
    profiles = storage.list_profiles()
    return {
        "status": "success",
        "count": len(profiles),
        "profiles": profiles
    }


@app.get("/registry/profiles/{profile_pid:path}")
async def get_profile(profile_pid: str):
    """Get specific profile FDO record."""
    profile_record = storage.get_profile(profile_pid)
    if not profile_record:
        raise HTTPException(status_code=404, detail=f"Profile {profile_pid} not found")

    return {
        "status": "success",
        "profile": profile_record
    }


@app.get("/registry/fdos/by-type/{type_pid:path}")
async def get_fdos_by_type(type_pid: str):
    """Get all FDOs of a specific type."""
    all_fdos = storage.search_fdos()

    matching_fdos = [
        fdo.dict() if hasattr(fdo, 'dict') else fdo
        for fdo in all_fdos
        if fdo.fdo_type_pid == type_pid
    ]

    return {
        "status": "success",
        "type_pid": type_pid,
        "count": len(matching_fdos),
        "fdos": matching_fdos
    }


# MARKETPLACE ENDPOINTS

@app.get("/market/agents/by_operation/{operation}")
async def get_agents_for_operation(
    operation: str,
    sort_by: str = "reputation",  # reputation, cost, load
    limit: Optional[int] = None
):
    """
    Get all agents providing an operation, ranked by criteria.

    Args:
        operation: Operation name to search for
        sort_by: Sort criteria (reputation, cost, load)
        limit: Optional limit on number of results

    Returns:
        List of agents with live marketplace data
    """
    # Find agents by operation
    fdos = storage.search_fdos(operation=operation)

    if not fdos:
        return {
            "status": "success",
            "message": f"No agents found for operation: {operation}",
            "data": []
        }

    # Enrich with marketplace data
    agents_info = []
    for fdo in fdos:
        status = agent_status_cache.get(fdo.pid, {})
        reputation = reputation_cache.get(fdo.pid, {})

        agent_info = {
            "pid": fdo.pid,
            "fdo_type": fdo.fdo_type_pid,
            "operation": operation,
            "base_cost": fdo.kernel_attributes.get("cost", 0.0),
            "current_cost": status.get("current_cost", fdo.kernel_attributes.get("cost", 0.0)),
            "reputation": reputation.get("score", 0.85),
            "queue_length": status.get("queue_length", 0),
            "estimated_wait": status.get("estimated_wait", 0.0),
            "availability_status": status.get("availability_status", "available"),
            "port": fdo.kernel_attributes.get("port"),
            "last_heartbeat": status.get("last_heartbeat", "unknown")
        }
        agents_info.append(agent_info)

    # Sort based on criteria
    if sort_by == "cost":
        agents_info.sort(key=lambda x: x["current_cost"])
    elif sort_by == "load":
        agents_info.sort(key=lambda x: x["queue_length"])
    else:  # reputation (default)
        agents_info.sort(key=lambda x: x["reputation"], reverse=True)

    # Apply limit if specified
    if limit:
        agents_info = agents_info[:limit]

    return {
        "status": "success",
        "message": f"Found {len(agents_info)} agents for {operation}",
        "data": agents_info
    }


@app.get("/market/agents/all")
async def get_all_agents_market_view():
    """Get marketplace view of all registered agents."""
    fdos = storage.search_fdos()

    agents_info = []
    for fdo in fdos:
        status = agent_status_cache.get(fdo.pid, {})
        reputation = reputation_cache.get(fdo.pid, {})

        agent_info = {
            "pid": fdo.pid,
            "fdo_type": fdo.fdo_type_pid,
            "operations": fdo.operation_pids,
            "base_cost": fdo.kernel_attributes.get("cost", 0.0),
            "current_cost": status.get("current_cost", fdo.kernel_attributes.get("cost", 0.0)),
            "reputation": reputation.get("score", 0.85),
            "queue_length": status.get("queue_length", 0),
            "availability_status": status.get("availability_status", "available"),
            "port": fdo.kernel_attributes.get("port")
        }
        agents_info.append(agent_info)

    return {
        "status": "success",
        "data": agents_info
    }


@app.post("/reputation/update")
async def update_reputation(update_data: Dict[str, Any]):
    """
    Update agent reputation with objective metrics.

    Expected data:
        agent_pid, operation, outcome ('success'/'failure'),
        reporter_pid (who reported), query (optional), error (optional)
    """
    agent_pid = update_data.get("agent_pid")
    operation = update_data.get("operation", "")
    outcome = update_data.get("outcome")  # 'success', 'empty_response', or 'failure'

    if not agent_pid:
        raise HTTPException(status_code=400, detail="agent_pid required")

    # Create composite key for per-operation reputation
    rep_key = f"{agent_pid}:{operation}" if operation else agent_pid

    # Get or create reputation entry (per operation)
    if rep_key not in reputation_cache:
        reputation_cache[rep_key] = {
            "agent_pid": agent_pid,
            "operation": operation,
            "score": 0.5,  # Start neutral
            "total_operations": 0,
            "successful_operations": 0,
            "empty_responses": 0,
            "failed_operations": 0,
            "avg_duration_accuracy": 1.0,
            "avg_cost_accuracy": 1.0,
            "caller_ratings": [],
            "last_updated": current_timestamp()
        }

    rep = reputation_cache[rep_key]

    # Update metrics based on outcome
    rep["total_operations"] += 1

    if outcome == "success":
        rep["successful_operations"] += 1
        outcome_weight = 1.0  # Full positive credit
    elif outcome == "empty_response":
        rep["empty_responses"] = rep.get("empty_responses", 0) + 1
        outcome_weight = 0.2  # Partial credit (agent worked but returned nothing useful)
    else:  # failure
        rep["failed_operations"] += 1
        outcome_weight = 0.0  # No credit

    # Calculate weighted success rate
    # success=1.0, empty=0.2, failure=0.0
    total_weight = (
        rep["successful_operations"] * 1.0 +
        rep.get("empty_responses", 0) * 0.2 +
        rep["failed_operations"] * 0.0
    )
    weighted_success_rate = total_weight / rep["total_operations"]

    # Update score with exponential moving average
    # New score = 70% weighted_success_rate + 30% old_score (gives weight to history)
    rep["score"] = (weighted_success_rate * 0.7) + (rep["score"] * 0.3)

    rep["last_updated"] = current_timestamp()

    # Log outcome with stats
    stats = f"✓{rep['successful_operations']}"
    if rep.get("empty_responses", 0) > 0:
        stats += f" ⚠{rep['empty_responses']}"
    if rep["failed_operations"] > 0:
        stats += f" ✗{rep['failed_operations']}"

    logger.info(
        "Registry",
        f"📊 Reputation updated: {agent_pid}.{operation} → {outcome} "
        f"(score: {rep['score']:.3f}, {stats})"
    )

    return {
        "status": "success",
        "message": "Reputation updated",
        "data": rep
    }


@app.post("/reputation/rate")
async def rate_agent(rating_data: Dict[str, Any]):
    """
    Submit caller rating for an agent.

    Expected data:
        agent_pid, caller_pid, overall (1.0-5.0), optional: speed, quality, value, reliability, comment
    """
    agent_pid = rating_data.get("agent_pid")
    overall = rating_data.get("overall")

    if not agent_pid or overall is None:
        raise HTTPException(status_code=400, detail="agent_pid and overall rating required")

    if not (1.0 <= overall <= 5.0):
        raise HTTPException(status_code=400, detail="Rating must be between 1.0 and 5.0")

    # Get or create reputation entry
    if agent_pid not in reputation_cache:
        reputation_cache[agent_pid] = {
            "score": 0.85,
            "total_operations": 0,
            "successful_operations": 0,
            "caller_ratings": [],
            "last_updated": current_timestamp()
        }

    rep = reputation_cache[agent_pid]

    # Add rating (convert 1-5 to 0-1 scale)
    rep["caller_ratings"].append({
        "caller_pid": rating_data.get("caller_pid", "anonymous"),
        "overall": overall,
        "timestamp": current_timestamp(),
        "comment": rating_data.get("comment")
    })

    # Keep only last 50 ratings
    if len(rep["caller_ratings"]) > 50:
        rep["caller_ratings"] = rep["caller_ratings"][-50:]

    # Calculate average rating
    avg_rating = sum(r["overall"] for r in rep["caller_ratings"]) / len(rep["caller_ratings"])
    rep["avg_caller_rating"] = (avg_rating - 1.0) / 4.0  # Convert to 0-1 scale

    # Recalculate score
    success_rate = rep["successful_operations"] / rep["total_operations"] if rep["total_operations"] > 0 else 1.0
    rep["score"] = (
        (success_rate * 0.4) +
        (rep.get("avg_duration_accuracy", 1.0) * 0.2) +
        (rep["avg_caller_rating"] * 0.3) +
        (0.1)
    )

    rep["last_updated"] = current_timestamp()

    return {
        "status": "success",
        "message": "Rating submitted",
        "data": {
            "new_score": rep["score"],
            "average_rating": avg_rating
        }
    }


@app.get("/reputation/{agent_pid:path}")
async def get_reputation(agent_pid: str):
    """Get detailed reputation breakdown for an agent."""
    reputation = reputation_cache.get(agent_pid)

    if not reputation:
        # Return default reputation
        return {
            "status": "success",
            "data": {
                "agent_pid": agent_pid,
                "score": 0.85,
                "total_operations": 0,
                "message": "No reputation data yet"
            }
        }

    return {
        "status": "success",
        "data": {
            "agent_pid": agent_pid,
            **reputation
        }
    }


@app.post("/status/update")
async def update_agent_status(status_data: Dict[str, Any]):
    """
    Update agent's live status (heartbeat).

    Expected data:
        agent_pid, queue_length, current_cost, availability_status, current_load
    """
    agent_pid = status_data.get("agent_pid")
    if not agent_pid:
        raise HTTPException(status_code=400, detail="agent_pid required")

    current_time = time.time()

    # Update status cache
    agent_status_cache[agent_pid] = {
        "queue_length": status_data.get("queue_length", 0),
        "current_cost": status_data.get("current_cost", 0.0),
        "availability_status": status_data.get("availability_status", "available"),
        "current_load": status_data.get("current_load", 0.0),
        "estimated_wait": status_data.get("estimated_wait", 0.0),
        "last_heartbeat": current_timestamp()
    }

    # Update FDO record with heartbeat timestamp and status
    try:
        fdo_info = storage.get_fdo(agent_pid)
        if fdo_info:
            updates = {
                'last_heartbeat': current_time,
                'status': 'active',
                'inactive_since': None  # Clear inactive timestamp
            }
            storage.update_fdo(agent_pid, updates)

            # Log heartbeat received (debug level to avoid spam)
            agent_name = fdo_info.kernel_attributes.get("name", agent_pid)
            logger.debug(
                "Registry",
                f"💓 Heartbeat from {agent_name} (queue={status_data.get('queue_length', 0)}, load={status_data.get('current_load', 0):.2f})"
            )
    except Exception as e:
        # Don't fail the heartbeat if FDO update fails
        print(f"⚠️  Failed to update FDO heartbeat for {agent_pid}: {e}")
        logger.error("Registry", f"Failed to update FDO heartbeat for {agent_pid}: {e}")

    return {
        "status": "success",
        "message": "Status updated"
    }


@app.get("/status/agents")
async def get_all_agent_status():
    """Get live status of all agents."""
    return {
        "status": "success",
        "data": agent_status_cache
    }


@app.get("/status/agent/{agent_pid:path}")
async def get_agent_status(agent_pid: str):
    """Get specific agent's live status."""
    status = agent_status_cache.get(agent_pid)

    if not status:
        return {
            "status": "success",
            "data": {
                "agent_pid": agent_pid,
                "availability_status": "unknown",
                "message": "No status data available"
            }
        }

    return {
        "status": "success",
        "data": {
            "agent_pid": agent_pid,
            **status
        }
    }


@app.post("/failures/report")
async def report_failure(failure_data: Dict[str, Any]):
    """
    Report agent failure.

    Expected data:
        caller_pid, failed_agent_pid, operation, error_type, error_message
    """
    failure_data["timestamp"] = current_timestamp()
    failure_reports.append(failure_data)

    # Log failure
    caller_pid = failure_data.get("caller_pid", "unknown")
    failed_agent_pid = failure_data.get("failed_agent_pid", "unknown")
    operation = failure_data.get("operation", "unknown")
    error_message = failure_data.get("error_message", "")

    logger.error(
        "Registry",
        f"Failure reported: {failed_agent_pid}.{operation}() by {caller_pid} - {error_message}"
    )

    # Keep only last 1000 failure reports
    if len(failure_reports) > 1000:
        failure_reports.pop(0)

    # Update reputation (penalize failed agent)
    if failed_agent_pid:
        await update_reputation({
            "agent_pid": failed_agent_pid,
            "operation_id": f"failure-{current_timestamp()}",
            "success": False
        })

    return {
        "status": "success",
        "message": "Failure reported"
    }


@app.get("/failures/{agent_pid:path}")
async def get_failure_history(agent_pid: str, limit: int = 10):
    """Get failure history for an agent."""
    agent_failures = [
        f for f in failure_reports
        if f.get("failed_agent_pid") == agent_pid
    ]

    # Return most recent failures
    agent_failures.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "status": "success",
        "data": agent_failures[:limit]
    }


@app.get("/alternatives/{agent_pid:path}/{operation}")
async def get_alternatives(agent_pid: str, operation: str, exclude_failed: bool = True):
    """
    Get alternative agents for an operation (excluding the specified agent).

    Useful for failure recovery - find alternatives when primary agent fails.
    """
    # Find all agents with this operation
    fdos = storage.search_fdos(operation=operation)

    # Exclude the failed agent
    alternatives = [fdo for fdo in fdos if fdo.pid != agent_pid]

    if exclude_failed:
        # Optionally exclude agents with recent failures
        recent_failed = set()
        for failure in failure_reports[-50:]:  # Last 50 failures
            recent_failed.add(failure.get("failed_agent_pid"))

        alternatives = [fdo for fdo in alternatives if fdo.pid not in recent_failed]

    # Enrich with marketplace data
    alternatives_info = []
    for fdo in alternatives:
        status = agent_status_cache.get(fdo.pid, {})
        reputation = reputation_cache.get(fdo.pid, {})

        alternatives_info.append({
            "pid": fdo.pid,
            "fdo_type": fdo.fdo_type_pid,
            "current_cost": status.get("current_cost", fdo.kernel_attributes.get("cost", 0.0)),
            "reputation": reputation.get("score", 0.85),
            "queue_length": status.get("queue_length", 0),
            "availability_status": status.get("availability_status", "available"),
            "port": fdo.kernel_attributes.get("port")
        })

    # Sort by reputation (best alternatives first)
    alternatives_info.sort(key=lambda x: x["reputation"], reverse=True)

    return {
        "status": "success",
        "message": f"Found {len(alternatives_info)} alternatives",
        "data": alternatives_info
    }


@app.get("/analytics/market")
async def get_market_analytics():
    """Get marketplace analytics and statistics."""
    fdos = storage.search_fdos()

    # Calculate statistics
    total_agents = len(fdos)
    agents_by_type = {}
    total_operations = 0

    for fdo in fdos:
        fdo_type = fdo.fdo_type_pid
        agents_by_type[fdo_type] = agents_by_type.get(fdo_type, 0) + 1
        total_operations += len(fdo.operation_pids)

    # Calculate average costs and reputations
    costs = []
    reputations = []
    for fdo in fdos:
        costs.append(fdo.kernel_attributes.get("cost", 0.0))
        rep = reputation_cache.get(fdo.pid, {})
        reputations.append(rep.get("score", 0.85))

    avg_cost = sum(costs) / len(costs) if costs else 0.0
    avg_reputation = sum(reputations) / len(reputations) if reputations else 0.85

    # Active agents (with recent heartbeat)
    active_agents = len(agent_status_cache)

    return {
        "status": "success",
        "data": {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "agents_by_type": agents_by_type,
            "total_operations_offered": total_operations,
            "average_cost": avg_cost,
            "average_reputation": avg_reputation,
            "total_failure_reports": len(failure_reports),
            "marketplace_health": "healthy" if active_agents > 0 else "no_active_agents"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(data)
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)


@app.get("/monitor")
async def serve_monitor():
    """Serve monitoring dashboard."""
    monitor_file = Path(__file__).parent / "static" / "monitor.html"
    if monitor_file.exists():
        return FileResponse(str(monitor_file))
    return {"message": "Monitor dashboard not found"}


@app.post("/events/call")
async def report_call_event(event_data: Dict[str, Any]):
    """Receive call event from agents."""
    await broadcaster.broadcast("call_made", event_data)
    return {"status": "received"}


# JOB MONITORING ENDPOINTS

@app.get("/monitor/jobs/active")
async def get_active_jobs():
    """Get all active jobs with call chains."""
    tracker = get_job_tracker()
    return {
        "status": "success",
        "data": tracker.get_active_jobs(),
        "count": len(tracker.get_active_jobs())
    }


@app.get("/monitor/jobs/history")
async def get_job_history(limit: int = 20):
    """Get recent completed jobs."""
    tracker = get_job_tracker()
    return {
        "status": "success",
        "data": tracker.get_completed_jobs(limit),
        "count": len(tracker.get_completed_jobs(limit))
    }


@app.get("/monitor/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get details of a specific job."""
    tracker = get_job_tracker()
    job = tracker.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "status": "success",
        "data": job
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
