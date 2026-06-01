"""System status endpoints for VentureOS Agent Engine."""

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request

router = APIRouter(prefix="/system", tags=["system"])

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
        except Exception:
            pass

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
            goal = getattr(orchestrator, "current_objective", None)
        except Exception:
            pass

    if goal:
        return {
            "goal": {
                "title": goal,
                "status": "executing",
            }
        }
    return {"goal": None}
