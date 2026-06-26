
# Memory endpoints — all queries filtered by authenticated user_id
from typing import Any, Dict, List, Optional
import json
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from api.middleware.auth import get_current_user
from memory.supabase_client import engine

router = APIRouter(prefix="/memory", tags=["memory"])


# ==================== Request Models ====================


class StoreMemoryRequest(BaseModel):
    key: str
    value: Any
    memory_type: str = "long_term"  # short_term | long_term | episodic | semantic | working
    agent_id: Optional[str] = None


class UpdateMemoryRequest(BaseModel):
    value: Optional[Any] = None
    memory_type: Optional[str] = None


# ==================== Memory CRUD ====================


@router.get("/")
async def list_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    memory_type: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """List memory entries for the authenticated user."""
    query = engine.table("memory_items").select("*").eq("user_id", user_id)
    if memory_type:
        query = query.eq("memory_type", memory_type)
    if agent_id:
        query = query.eq("agent_id", agent_id)
    res = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    return {"memories": res.data, "total": len(res.data)}


@router.get("/{memory_id}")
async def get_memory(
    memory_id: str = Path(..., description="Memory entry UUID"),
    user_id: str = Depends(get_current_user),
) ->  Any:
    """Get a single memory entry by ID."""
    res = (
        engine.table("memory_items")
        .select("*")
        .eq("id", memory_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Memory entry not found.")
    return res.data


@router.post("/", status_code=201)
async def store_memory(
    body: StoreMemoryRequest,
    user_id: str = Depends(get_current_user),
) -> Any:
    """Store a new memory entry."""
    data = {
        "user_id": user_id,
        "key": body.key,
        "value": body.value,
        "memory_type": body.memory_type,
        "agent_id": body.agent_id,
    }
    res = engine.table("memory_items").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to store memory entry.")
    return res.data[0]


@router.patch("/{memory_id}")
async def update_memory(
    memory_id: str = Path(...),
    body: UpdateMemoryRequest = Body(...),
    user_id: str = Depends(get_current_user),
) -> Any:
    """Update a memory entry."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    res = (
        engine.table("memory_items")
        .update(updates)
        .eq("id", memory_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Memory entry not found.")
    return res.data[0]


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str = Path(...),
    user_id: str = Depends(get_current_user),
) -> Any:
    """Delete a memory entry."""
    res = (
        engine.table("memory_items")
        .delete()
        .eq("id", memory_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Memory entry not found.")
    return {"deleted": memory_id}


# async def hybrid_search(
#     query: str = Body(...), filters: Dict[str, Any] = Body({}), top_k: int = Body(10)
# ) -> Dict[str, Any]:
#     """Hybrid search with filters."""
#     pass


# ==================== Context Retrieval ====================


# async def get_context(
#     agent_id: str = Query(...),
#     task_id: Optional[str] = Query(None),
#     max_entries: int = Query(10),
# ) -> Dict[str, Any]:
#     """Get relevant context for agent."""
#     pass


# async def get_conversation_history(
#     conversation_id: str = Path(...), skip: int = Query(0), limit: int = Query(50)
# ) -> Dict[str, Any]:
#     """Get conversation history."""
#     pass


# async def add_to_conversation(
#     conversation_id: str = Path(...), message: Dict[str, Any] = Body(...)
# ) -> Dict[str, Any]:
#     """Add message to conversation."""
#     pass


# async def clear_conversation(conversation_id: str = Path(...)) -> Dict[str, Any]:
#     """Clear conversation history."""
#     pass


# # ==================== Cache Operations ====================


# async def get_cached(key: str = Path(...)) -> Dict[str, Any]:
#     """Get cached value."""
#     pass


# async def set_cached(
#     key: str = Path(...), value: Any = Body(...), ttl: Optional[int] = Body(None)
# ) -> Dict[str, Any]:
#     """Set cached value."""
#     pass


# async def delete_cached(key: str = Path(...)) -> Dict[str, Any]:
#     """Delete cached value."""
#     pass


# async def clear_cache(pattern: Optional[str] = Query(None)) -> Dict[str, Any]:
#     """Clear cache entries."""
#     pass


# async def get_cache_stats() -> Dict[str, Any]:
#     """Get cache statistics."""
#     pass


# # ==================== Namespace Operations ====================


# async def list_namespaces() -> Dict[str, Any]:
#     """List all namespaces."""
#     pass


# async def create_namespace(namespace: str = Body(...)) -> Dict[str, Any]:
#     """Create a namespace."""
#     pass


# async def delete_namespace(namespace: str = Path(...)) -> Dict[str, Any]:
#     """Delete a namespace and all its data."""
#     pass


# async def get_namespace_stats(namespace: str = Path(...)) -> Dict[str, Any]:
#     """Get namespace statistics."""
#     pass


# # ==================== Bulk Operations ====================


# async def store_memories_bulk(
#     memories: List[Dict[str, Any]] = Body(...),
# ) -> Dict[str, Any]:
#     """Store multiple memories."""
#     pass


# async def delete_memories_bulk(memory_ids: List[str] = Body(...)) -> Dict[str, Any]:
#     """Delete multiple memories."""
#     pass


# async def export_memories(
#     namespace: Optional[str] = Query(None), format: str = Query("json")
# ) -> Dict[str, Any]:
#     """Export memories."""
#     pass


# async def import_memories(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
#     """Import memories."""
#     pass


# # ==================== Agent Memory ====================


# async def get_agent_memory(agent_id: str = Path(...)) -> Dict[str, Any]:
#     """Get all memory for an agent."""
#     pass


# async def clear_agent_memory(agent_id: str = Path(...)) -> Dict[str, Any]:
#     """Clear all memory for an agent."""
#     pass


# async def get_agent_working_memory(agent_id: str = Path(...)) -> Dict[str, Any]:
#     """Get agent's working memory."""
#     pass


# async def update_agent_working_memory(
#     agent_id: str = Path(...), data: Dict[str, Any] = Body(...)
# ) -> Dict[str, Any]:
#     """Update agent's working memory."""
#     pass


# # ==================== Statistics ====================


# async def get_memory_stats() -> Dict[str, Any]:
#     """Get overall memory statistics."""
#     pass


# async def get_memory_usage() -> Dict[str, Any]:
#     """Get memory usage by tier."""
#     pass


# # Register routes
# def register_routes() -> APIRouter:
#     """Register all memory routes."""
#     pass
