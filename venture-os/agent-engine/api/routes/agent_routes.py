# Agent execution endpoints
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/agents", tags=["agents"])


# ==================== Agent CRUD ====================


async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """List all available agents."""
    pass


async def get_agent(
    agent_id: str = Path(..., description="Agent ID")
) -> Dict[str, Any]:
    """Get agent details by ID."""
    pass


async def create_agent(agent_config: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Create a new agent."""
    pass


async def update_agent(
    agent_id: str = Path(...), updates: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Update agent configuration."""
    pass


async def delete_agent(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Delete an agent."""
    pass


# ==================== Agent Execution ====================


async def execute_agent(
    agent_id: str = Path(...), request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Execute an agent with given input."""
    pass


async def execute_agent_stream(
    agent_id: str = Path(...), request: Dict[str, Any] = Body(...)
) -> StreamingResponse:
    """Execute agent with streaming response."""
    pass


async def execute_agent_async(
    agent_id: str = Path(...), request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Queue agent execution asynchronously."""
    pass


async def cancel_execution(execution_id: str = Path(...)) -> Dict[str, Any]:
    """Cancel a running agent execution."""
    pass


async def get_execution_status(execution_id: str = Path(...)) -> Dict[str, Any]:
    """Get status of an agent execution."""
    pass


async def get_execution_result(execution_id: str = Path(...)) -> Dict[str, Any]:
    """Get result of a completed execution."""
    pass


# ==================== Agent Types ====================


async def list_agent_types() -> List[Dict[str, Any]]:
    """List available agent types."""
    pass


async def get_agent_type_schema(agent_type: str = Path(...)) -> Dict[str, Any]:
    """Get configuration schema for agent type."""
    pass


async def validate_agent_config(
    agent_type: str = Path(...), config: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Validate agent configuration."""
    pass


# ==================== Agent Capabilities ====================


async def get_agent_capabilities(agent_id: str = Path(...)) -> Dict[str, Any]:
    """Get agent capabilities."""
    pass


async def get_agent_tools(agent_id: str = Path(...)) -> List[Dict[str, Any]]:
    """Get tools available to agent."""
    pass


async def enable_agent_tool(
    agent_id: str = Path(...), tool_name: str = Path(...)
) -> Dict[str, Any]:
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
