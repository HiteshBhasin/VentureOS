# Agent endpoints — all queries filtered by authenticated user_id
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from api.middleware.auth import get_current_user
from memory.supabase_client import engine

router = APIRouter(prefix="/agents", tags=["agents"])


# ==================== Request Models ====================


class CreateAgentRequest(BaseModel):
    name: str
    type: str  # coding | research | review | runtime | meta | custom
    description: str = ""
    model: str = "gpt-4"
    llm_config: Dict[str, Any] = {}
    memory_config: Dict[str, Any] = {}
    tool_config: List[Dict[str, Any]] = []


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    activity: Optional[str] = None
    progress: Optional[int] = None
    description: Optional[str] = None
    model: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    tool_config: Optional[List[Dict[str, Any]]] = None


# ==================== Agent CRUD ====================


@router.get("/")
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """List all agents belonging to the authenticated user."""
    query = engine.table("agents").select("*").eq("user_id", user_id)
    if agent_type:
        query = query.eq("type", agent_type)
    res = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    return {"agents": res.data, "total": len(res.data)}


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str = Path(..., description="Agent UUID"),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get a single agent by ID."""
    res = (
        engine.table("agents")
        .select("*")
        .eq("id", agent_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return res.data


@router.post("/", status_code=201)
async def create_agent(
    body: CreateAgentRequest,
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new agent for the authenticated user."""
    data = {
        "user_id": user_id,
        "name": body.name,
        "type": body.type,
        "description": body.description,
        "model": body.model,
        "status": "idle",
        "activity": "IDLE",
        "progress": 0,
        "llm_config": body.llm_config,
        "memory_config": body.memory_config,
        "tool_config": body.tool_config,
        "tokens_per_sec": 0.0,
        "cost_estimate": 0.0,
    }
    res = engine.table("agents").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create agent.")
    return res.data[0]


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str = Path(...),
    body: UpdateAgentRequest = Body(...),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update an agent's fields."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    res = (
        engine.table("agents")
        .update(updates)
        .eq("id", agent_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return res.data[0]


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str = Path(...),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete an agent."""
    res = (
        engine.table("agents")
        .delete()
        .eq("id", agent_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return {"deleted": agent_id}

    """Enable a tool for agent."""
    pass


async def disable_agent_tool(
    agent_id: str = Path(...), tool_name: str = Path(...)
) -> Dict[str, Any]:
    """Disable a tool for agent."""
    pass


# ==================== Agent Stats ====================


async def get_agent_stats(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Get agent statistics."""
    pass


async def get_agent_history(
    agent_id: str = Path(...), skip: int = Query(0), limit: int = Query(50)
) -> Dict[str, Any]:
    """Get agent execution history."""
    pass


async def reset_agent_stats(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Reset agent statistics."""
    pass


# ==================== Agent State ====================


async def get_agent_state(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Get current agent state."""
    pass


async def set_agent_state(
    agent_id: str = Path(...), state: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Set agent state."""
    pass


async def reset_agent_state(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Reset agent to initial state."""
    pass


# ==================== Agent Health ====================


async def check_agent_health(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Check agent health status."""
    pass


async def restart_agent(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Restart an agent."""
    pass


# Register routes
def register_routes() -> APIRouter:
    """Register all agent routes."""
    pass
