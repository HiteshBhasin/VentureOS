# Task endpoints — all queries filtered by authenticated user_id
import os
from pathlib import Path as FSPath
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from api.middleware.auth import get_current_user
from memory.supabase_client import engine

router = APIRouter(prefix="/tasks", tags=["tasks"])

# api/routes/task_routes.py -> routes -> api -> agent-engine -> generated_projects/
_GENERATED_ROOT = (FSPath(__file__).resolve().parents[2] / "generated_projects").resolve()

VALID_STATUSES = {
    "pending",
    "queued",
    "running",
    "paused",
    "completed",
    "failed",
    "cancelled",
}
VALID_PRIORITIES = {"low", "medium", "high"}

# ==================== Request Models ====================


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    type: str = "custom"
    agent_id: Optional[str] = None
    goal_id: Optional[str] = None
    tags: List[str] = []


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[int] = None
    agent_id: Optional[str] = None
    goal_id: Optional[str] = None
    tags: Optional[List[str]] = None


# ==================== Task CRUD ====================


@router.get("/")
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """List all tasks belonging to the authenticated user."""
    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}"
        )
    query = engine.table("tasks").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)
    if agent_id:
        query = query.eq("agent_id", agent_id)
    res = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    return {"tasks": res.data, "total": len(res.data)}


@router.get("/{task_id}")
async def get_task(
    task_id: str = Path(..., description="Task UUID"),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get a single task by ID."""
    res = (
        engine.table("tasks")
        .select("*")
        .eq("id", task_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"task": res.data}


@router.post("/", status_code=201)
async def create_task(
    body: CreateTaskRequest,
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new task. The background worker picks it up and runs the orchestrator."""
    if body.priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Must be one of: {VALID_PRIORITIES}",
        )
    data = {
        "user_id": user_id,
        "title": body.title,
        "description": body.description,
        "priority": body.priority,
        "type": body.type,
        "status": "pending",
        "progress": 0,
        "tags": body.tags,
        "agent_id": body.agent_id,
        "goal_id": body.goal_id,
    }
    res = engine.table("tasks").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create task.")

    return res.data[0]


@router.patch("/{task_id}")
async def update_task(
    task_id: str = Path(...),
    body: UpdateTaskRequest = Body(...),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update a task's fields."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}"
        )
    res = (
        engine.table("tasks")
        .update(updates)
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"task": res.data[0]}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str = Path(...),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a task."""
    res = (
        engine.table("tasks")
        .delete()
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"deleted": task_id}


# ==================== Status Shortcut ====================


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str = Path(...),
    status: str = Body(..., embed=True),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Quickly update only the status of a task."""
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}"
        )
    res = (
        engine.table("tasks")
        .update({"status": status})
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"task": res.data[0]}


# ==================== Generated Project Files ====================
# Lets the dashboard show a completed task's output in-page — file list +
# readable content — instead of a filesystem path the user has to go find
# themselves in an OS file browser.


async def _get_task_or_404(task_id: str, user_id: str) -> Dict[str, Any]:
    res = (
        engine.table("tasks")
        .select("*")
        .eq("id", task_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found.")
    return res.data


def _resolve_project_dir(task: Dict[str, Any]) -> FSPath:
    """Resolve a task's project_path, enforcing it stays within
    generated_projects/ — the DB value is trusted data we wrote ourselves,
    but validating anyway means a compromised/edited row can't be used to
    read arbitrary files off the server's filesystem."""
    result = task.get("result") or {}
    project_path = result.get("project_path")
    if not project_path:
        raise HTTPException(
            status_code=404, detail="This task has no generated project output."
        )
    resolved = FSPath(project_path).resolve()
    if resolved != _GENERATED_ROOT and _GENERATED_ROOT not in resolved.parents:
        raise HTTPException(status_code=400, detail="Invalid project path.")
    if not resolved.is_dir():
        raise HTTPException(
            status_code=404, detail="Project folder no longer exists on disk."
        )
    return resolved


@router.get("/{task_id}/files")
async def list_task_files(
    task_id: str = Path(...),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """List every file in a completed task's generated project folder."""
    task = await _get_task_or_404(task_id, user_id)
    project_dir = _resolve_project_dir(task)
    files = [
        {
            "path": str(p.relative_to(project_dir)).replace(os.sep, "/"),
            "size_bytes": p.stat().st_size,
        }
        for p in sorted(project_dir.rglob("*"))
        if p.is_file()
    ]
    return {"files": files}


@router.get("/{task_id}/files/{file_path:path}")
async def get_task_file(
    task_id: str = Path(...),
    file_path: str = Path(...),
    user_id: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return the text content of one file from a task's generated project."""
    task = await _get_task_or_404(task_id, user_id)
    project_dir = _resolve_project_dir(task)
    target = (project_dir / file_path).resolve()
    if target != project_dir and project_dir not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not read file: {exc}")
    return {"path": file_path, "content": content, "size_bytes": target.stat().st_size}


# ==================== Task Execution ====================


# async def execute_task(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Execute a task."""
#     pass


# async def cancel_task(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Cancel a running task."""
#     pass


# async def retry_task(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Retry a failed task."""
#     pass


# async def pause_task(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Pause a running task."""
#     pass


# async def resume_task(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Resume a paused task."""
#     pass


# ==================== Task Status ====================


# async def get_task_status(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Get task execution status."""
#     pass


# async def get_task_progress(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Get task progress."""
#     pass


# async def get_task_result(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Get task result."""
#     pass


# async def get_task_logs(
#     task_id: str = Path(...), skip: int = Query(0), limit: int = Query(100)
# ) -> Dict[str, Any]:
#     """Get task execution logs."""
#     pass


# ==================== Task Dependencies ====================


# async def get_task_dependencies(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Get task dependencies."""
#     pass


# async def add_task_dependency(
#     task_id: str = Path(...), dependency_id: str = Body(...)
# ) -> Dict[str, Any]:
#     """Add dependency to task."""
#     pass


# async def remove_task_dependency(
#     task_id: str = Path(...), dependency_id: str = Path(...)
# ) -> Dict[str, Any]:
#     """Remove dependency from task."""
#     pass


# async def get_dependent_tasks(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Get tasks dependent on this task."""
#     pass


# ==================== Task Graph ====================


# async def get_task_graph() -> Dict[str, Any]:
#     """Get full task graph."""
#     pass


# async def get_task_graph_status() -> Dict[str, Any]:
#     """Get task graph execution status."""
#     pass


# async def execute_task_graph(graph_id: Optional[str] = Query(None)) -> Dict[str, Any]:
#     """Execute task graph."""
#     pass


# async def validate_task_graph() -> Dict[str, Any]:
#     """Validate task graph for cycles."""
#     pass


# ==================== Bulk Operations ====================


# async def create_tasks_bulk(tasks: List[Dict[str, Any]] = Body(...)) -> Dict[str, Any]:
#     """Create multiple tasks."""
#     pass


# async def delete_tasks_bulk(task_ids: List[str] = Body(...)) -> Dict[str, Any]:
#     """Delete multiple tasks."""
#     pass


# async def cancel_tasks_bulk(task_ids: List[str] = Body(...)) -> Dict[str, Any]:
#     """Cancel multiple tasks."""
#     pass


# async def update_tasks_status(
#     task_ids: List[str] = Body(...), status: str = Body(...)
# ) -> Dict[str, Any]:
#     """Update status of multiple tasks."""
#     pass


# ==================== Task Assignment ====================


# async def assign_task(
#     task_id: str = Path(...), agent_id: str = Body(...)
# ) -> Dict[str, Any]:
#     """Assign task to agent."""
#     pass


# async def unassign_task(task_id: str = Path(...)) -> Dict[str, Any]:
#     """Unassign task from agent."""
#     pass


# async def get_tasks_by_agent(agent_id: str = Path(...)) -> Dict[str, Any]:
#     """Get tasks assigned to agent."""
#     pass


# ==================== Task Statistics ====================


# async def get_task_stats() -> Dict[str, Any]:
#     """Get task statistics."""
#     pass


# async def get_task_metrics(
#     start_time: Optional[str] = Query(None), end_time: Optional[str] = Query(None)
# ) -> Dict[str, Any]:
#     """Get task metrics for time range."""
#     pass


# # Register routes
# def register_routes() -> APIRouter:
#     """Register all task routes."""
#     pass
