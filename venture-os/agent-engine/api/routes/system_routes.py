"""System status endpoints for VentureOS Agent Engine."""

import time
import logging
import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])

# In-memory log buffer for streaming (last 100 messages)
_LOG_BUFFER: list = []
_MAX_LOG_BUFFER = 100

# Track startup time for uptime calculation
_START_TIME = time.time()


@router.get("/status")
def get_system_status(request: Request) -> Dict[str, Any]:
    """Return basic system / orchestrator status."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    active_agents = 0
    if orchestrator is not None:
        try:
            active_agents = len(getattr(orchestrator, "active_agents", {}))
            logger.debug(f"Active agents: {active_agents}")
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
def get_active_goal(request: Request) -> Dict[str, Any]:
    """Return the current active goal / objective from the orchestrator."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    goal: Optional[str] = None
    if orchestrator is not None:
        try:
            goal = getattr(orchestrator, "current_objectives", None)
            logger.debug(f"Current goal: {goal}")
            if goal:
                add_log(f"→ Current objective: {goal}", "INFO")
            else:
                add_log("→ No active objective", "INFO")
        except Exception as e:
            logger.error(f"Error fetching current goal: {e}")
            add_log(f"✗ Error fetching goal: {str(e)}", "ERROR")

    if goal:
        return {
            "goal": {
                "title": goal,
                "status": "executing",
            }
        }
    return {"goal": None}


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
