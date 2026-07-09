"""System status endpoints for VentureOS Agent Engine."""

import time
import logging
import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from api.middleware.auth import get_current_user
from memory.supabase_client import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])

# In-memory log buffer for streaming (last 100 messages)
_LOG_BUFFER: list = []
_MAX_LOG_BUFFER = 100

# Track startup time for uptime calculation
_START_TIME = time.time()


@router.get("/status")
def get_system_status(
    request: Request, user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Return basic system status.

    ``active_agents`` reflects the ``agents`` DB table rather than the
    in-process orchestrator, because task execution happens in the separate
    ``worker.py`` process — the API process's own Orchestrator instance never
    runs a real request, so its in-memory agent registry is always empty.
    """
    active_agents = 0
    try:
        res = (
            engine.table("agents")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .in_("status", ["active", "running"])
            .execute()
        )
        active_agents = res.count if res.count is not None else len(res.data)
        add_log(f"✓ System status check — {active_agents} agents running", "INFO")
    except Exception as e:
        logger.error(f"Error fetching active agents: {e}")
        add_log(f"✗ Error fetching status: {str(e)}", "ERROR")

    return {
        "active_agents": active_agents,
        "uptime_seconds": int(time.time() - _START_TIME),
        "status": "ok",
    }


@router.get("/goal")
def get_active_goal(
    request: Request, user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Return the user's current active goal, derived from their most recent
    running (or otherwise pending) task in the ``tasks`` table.
    """
    goal: Optional[Dict[str, Any]] = None
    try:
        res = (
            engine.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["running", "pending", "queued"])
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        rows = res.data or []
        # Prefer a running task; fall back to the most recently created pending one.
        task = next((r for r in rows if r["status"] == "running"), None) or (
            rows[0] if rows else None
        )
        if task:
            created_at = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
            elapsed = int((datetime.now(timezone.utc) - created_at).total_seconds())
            goal = {
                "id": task["id"],
                "title": task["title"],
                "status": "executing" if task["status"] == "running" else "paused",
                "completion": task.get("progress", 0),
                "elapsed_seconds": max(elapsed, 0),
            }
            add_log(f"→ Current objective: {task['title']}", "INFO")
        else:
            add_log("→ No active objective", "INFO")
    except Exception as e:
        logger.error(f"Error fetching current goal: {e}")
        add_log(f"✗ Error fetching goal: {str(e)}", "ERROR")

    return {"goal": goal}


def add_log(message: str, level: str = "INFO") -> None:
    """Add a message to the log buffer. Called by other routes."""
    global _LOG_BUFFER
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "level": level,
    }
    _LOG_BUFFER.append(log_entry)
    if len(_LOG_BUFFER) > _MAX_LOG_BUFFER:
        _LOG_BUFFER.pop(0)


async def log_stream_generator(request: Request):
    """Generator that yields SSE-formatted log messages."""
    # Send buffered logs first
    for log_entry in _LOG_BUFFER:
        data = json.dumps(log_entry)
        yield f"data: {data}\n\n"
    
    # Then stream new logs as they arrive
    last_index = len(_LOG_BUFFER)
    while True:
        # Check if client disconnected
        if await request.is_disconnected():
            break
            
        await asyncio.sleep(1)  # Check every second
        
        # Send any new logs
        if last_index < len(_LOG_BUFFER):
            for log_entry in _LOG_BUFFER[last_index:]:
                data = json.dumps(log_entry)
                yield f"data: {data}\n\n"
            last_index = len(_LOG_BUFFER)


@router.get("/stream")
async def get_system_stream(request: Request):
    """Stream real-time system logs as Server-Sent Events (SSE)."""
    return StreamingResponse(
        log_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
