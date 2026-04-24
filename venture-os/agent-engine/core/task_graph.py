# Task Graph: DAG of tasks
import json
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Status of a task in the graph."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class TaskNode:
    """Represents a task node in the graph."""

    task_id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskGraph:
    """Directed Acyclic Graph (DAG) for task management."""

    def __init__(self):
        self._nodes: Dict[str, TaskNode] = {}
        self._adjacency: Dict[str, Set[str]] = (
            {}
        )  # task_id -> set of dependent task_ids
        self._reverse_adjacency: Dict[str, Set[str]] = (
            {}
        )  # task_id -> set of dependency task_ids

    # ==================== Node Management ====================

    def add_task(self, task: TaskNode) -> None:
        """Add a task to the graph."""
        self._nodes[task.task_id] = task
        self._adjacency.setdefault(task.task_id, set())
        self._reverse_adjacency.setdefault(task.task_id, set())
        # Wire up pre-declared dependencies
        for dep_id in task.dependencies:
            self._reverse_adjacency[task.task_id].add(dep_id)
            self._adjacency.setdefault(dep_id, set()).add(task.task_id)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the graph."""
        if task_id not in self._nodes:
            return False
        # Clean up edges to/from this task
        for dep_id in list(self._reverse_adjacency.get(task_id, set())):
            self._adjacency.get(dep_id, set()).discard(task_id)
        for downstream_id in list(self._adjacency.get(task_id, set())):
            self._reverse_adjacency.get(downstream_id, set()).discard(task_id)
        del self._nodes[task_id]
        self._adjacency.pop(task_id, None)
        self._reverse_adjacency.pop(task_id, None)
        return True

    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """Get a task by ID."""
        return self._nodes.get(task_id)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task properties."""
        task = self._nodes.get(task_id)
        if not task:
            return False
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return True

    def get_all_tasks(self) -> List[TaskNode]:
        """Get all tasks in the graph."""
        return list(self._nodes.values())

    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskNode]:
        """Get tasks with specific status."""
        return [t for t in self._nodes.values() if t.status == status]

    # ==================== Dependency Management ====================

    def add_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Add a dependency between tasks."""
        if task_id not in self._nodes or dependency_id not in self._nodes:
            return False
        if dependency_id in self._reverse_adjacency.get(task_id, set()):
            return False  # Already exists
        # Prevent cycles: dependency_id must not be downstream of task_id
        if task_id in self.get_all_downstream(dependency_id):
            return False
        self._reverse_adjacency.setdefault(task_id, set()).add(dependency_id)
        self._adjacency.setdefault(dependency_id, set()).add(task_id)
        if dependency_id not in self._nodes[task_id].dependencies:
            self._nodes[task_id].dependencies.append(dependency_id)
        return True

    def remove_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Remove a dependency between tasks."""
        if dependency_id not in self._reverse_adjacency.get(task_id, set()):
            return False
        self._reverse_adjacency[task_id].discard(dependency_id)
        self._adjacency.get(dependency_id, set()).discard(task_id)
        task = self._nodes.get(task_id)
        if task and dependency_id in task.dependencies:
            task.dependencies.remove(dependency_id)
        return True

    def get_dependencies(self, task_id: str) -> List[str]:
        """Get dependencies of a task."""
        return list(self._reverse_adjacency.get(task_id, set()))

    def get_dependents(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task."""
        return list(self._adjacency.get(task_id, set()))

    def has_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Check if dependency exists."""
        return dependency_id in self._reverse_adjacency.get(task_id, set())

    def get_all_upstream(self, task_id: str) -> Set[str]:
        """Get all upstream tasks (transitive dependencies)."""
        visited: Set[str] = set()

        def _dfs(node_id: str) -> None:
            for dep in self._reverse_adjacency.get(node_id, set()):
                if dep not in visited:
                    visited.add(dep)
                    _dfs(dep)

        _dfs(task_id)
        return visited

    def get_all_downstream(self, task_id: str) -> Set[str]:
        """Get all downstream tasks (transitive dependents)."""
        visited: Set[str] = set()

        def _dfs(node_id: str) -> None:
            for dep in self._adjacency.get(node_id, set()):
                if dep not in visited:
                    visited.add(dep)
                    _dfs(dep)

        _dfs(task_id)
        return visited

    # ==================== Graph Operations ====================

    def topological_sort(self) -> List[str]:
        """Return tasks in topological order."""
        in_degree = {
            tid: len(self._reverse_adjacency.get(tid, set()))
            for tid in self._nodes
        }
        queue = [tid for tid, d in in_degree.items() if d == 0]
        queue.sort()  # Deterministic ordering
        result: List[str] = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for downstream in sorted(self._adjacency.get(node, set())):
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)
        return result

    def validate(self) -> Dict[str, Any]:
        """Validate the graph (check for cycles, missing deps)."""
        errors: List[str] = []
        warnings: List[str] = []
        if self.has_cycle():
            errors.append("Graph contains one or more cycles")
        for task_id, deps in self._reverse_adjacency.items():
            for dep_id in deps:
                if dep_id not in self._nodes:
                    errors.append(
                        f"Task '{task_id}' depends on missing task '{dep_id}'"
                    )
        for task_id in self._nodes:
            if (
                not self._reverse_adjacency.get(task_id)
                and not self._adjacency.get(task_id)
                and len(self._nodes) > 1
            ):
                warnings.append(f"Task '{task_id}' is isolated")
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def has_cycle(self) -> bool:
        """Check if graph has a cycle."""
        return len(self.topological_sort()) < len(self._nodes)

    def detect_cycles(self) -> List[List[str]]:
        """Detect and return all cycles in the graph."""
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def _dfs(node_id: str, path: List[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            for downstream in self._adjacency.get(node_id, set()):
                if downstream not in visited:
                    _dfs(downstream, list(path))
                elif downstream in rec_stack:
                    cycle_start = path.index(downstream)
                    cycles.append(path[cycle_start:] + [downstream])
            rec_stack.discard(node_id)

        for node_id in self._nodes:
            if node_id not in visited:
                _dfs(node_id, [])
        return cycles

    def get_critical_path(self) -> List[str]:
        """Get the critical path through the graph."""
        topo = self.topological_sort()
        if not topo:
            return []
        dist: Dict[str, int] = {tid: 0 for tid in self._nodes}
        prev: Dict[str, Optional[str]] = {tid: None for tid in self._nodes}
        for node_id in topo:
            for downstream in self._adjacency.get(node_id, set()):
                if dist[node_id] + 1 > dist[downstream]:
                    dist[downstream] = dist[node_id] + 1
                    prev[downstream] = node_id
        end_node = max(dist, key=lambda k: dist[k])
        path: List[str] = []
        current: Optional[str] = end_node
        while current is not None:
            path.append(current)
            current = prev[current]
        return list(reversed(path))

    def get_parallel_groups(self) -> List[List[str]]:
        """Get groups of tasks that can run in parallel."""
        topo = self.topological_sort()
        levels: Dict[str, int] = {}
        for node_id in topo:
            upstream = self._reverse_adjacency.get(node_id, set())
            if not upstream:
                levels[node_id] = 0
            else:
                levels[node_id] = max(levels.get(dep, 0) for dep in upstream) + 1
        if not levels:
            return []
        max_level = max(levels.values())
        groups: List[List[str]] = [[] for _ in range(max_level + 1)]
        for node_id, level in levels.items():
            groups[level].append(node_id)
        return groups

    # ==================== Execution Management ====================

    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks ready for execution (dependencies satisfied)."""
        return [
            task
            for task in self._nodes.values()
            if task.status in (TaskStatus.PENDING, TaskStatus.READY)
            and self.are_dependencies_satisfied(task.task_id)
        ]

    def are_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all dependencies are completed."""
        for dep_id in self._reverse_adjacency.get(task_id, set()):
            dep = self._nodes.get(dep_id)
            if dep is None or dep.status != TaskStatus.COMPLETED:
                return False
        return True

    def mark_task_started(self, task_id: str, agent_id: Optional[str] = None) -> None:
        """Mark task as started."""
        task = self._nodes.get(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            if agent_id:
                task.assigned_agent = agent_id

    def mark_task_completed(self, task_id: str, result: Any = None) -> None:
        """Mark task as completed."""
        task = self._nodes.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

    def mark_task_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        task = self._nodes.get(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = error

    def mark_task_skipped(self, task_id: str, reason: str = "") -> None:
        """Mark task as skipped."""
        task = self._nodes.get(task_id)
        if task:
            task.status = TaskStatus.SKIPPED
            task.completed_at = datetime.now()
            if reason:
                task.metadata["skip_reason"] = reason

    def mark_task_cancelled(self, task_id: str) -> None:
        """Mark task as cancelled."""
        task = self._nodes.get(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

    def propagate_failure(self, task_id: str) -> List[str]:
        """Propagate failure to dependent tasks."""
        affected: List[str] = []
        for downstream_id in self.get_all_downstream(task_id):
            task = self._nodes.get(downstream_id)
            if task and task.status in (TaskStatus.PENDING, TaskStatus.READY):
                task.status = TaskStatus.SKIPPED
                task.metadata["blocked_by"] = task_id
                affected.append(downstream_id)
        return affected

    # ==================== Query Operations ====================

    def get_leaf_tasks(self) -> List[TaskNode]:
        """Get tasks with no dependencies (can run immediately)."""
        return [
            t for tid, t in self._nodes.items()
            if not self._reverse_adjacency.get(tid)
        ]

    def get_root_tasks(self) -> List[TaskNode]:
        """Get tasks with no dependents (terminal/final tasks)."""
        return [
            t for tid, t in self._nodes.items()
            if not self._adjacency.get(tid)
        ]

    def get_pending_count(self) -> int:
        """Get count of pending tasks."""
        return sum(1 for t in self._nodes.values() if t.status == TaskStatus.PENDING)

    def get_completed_count(self) -> int:
        """Get count of completed tasks."""
        return sum(1 for t in self._nodes.values() if t.status == TaskStatus.COMPLETED)

    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress statistics."""
        total = len(self._nodes)
        counts: Dict[TaskStatus, int] = {s: 0 for s in TaskStatus}
        for task in self._nodes.values():
            counts[task.status] += 1
        completed = counts[TaskStatus.COMPLETED]
        percent = round((completed / total * 100), 2) if total > 0 else 0.0
        return {
            "total": total,
            "completed": completed,
            "failed": counts[TaskStatus.FAILED],
            "running": counts[TaskStatus.RUNNING],
            "pending": counts[TaskStatus.PENDING],
            "ready": counts[TaskStatus.READY],
            "skipped": counts[TaskStatus.SKIPPED],
            "cancelled": counts[TaskStatus.CANCELLED],
            "percent_complete": percent,
        }

    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            t.status
            in (TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.CANCELLED)
            for t in self._nodes.values()
        )

    def has_failures(self) -> bool:
        """Check if any tasks have failed."""
        return any(t.status == TaskStatus.FAILED for t in self._nodes.values())

    # ==================== Serialization ====================

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "nodes": {
                tid: {
                    "task_id": t.task_id,
                    "name": t.name,
                    "description": t.description,
                    "status": t.status.value,
                    "dependencies": t.dependencies,
                    "assigned_agent": t.assigned_agent,
                    "result": t.result,
                    "error": t.error,
                    "created_at": t.created_at.isoformat(),
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "metadata": t.metadata,
                }
                for tid, t in self._nodes.items()
            },
            "adjacency": {tid: list(deps) for tid, deps in self._adjacency.items()},
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load graph from dictionary."""
        self.clear()
        for node_data in data.get("nodes", {}).values():
            task = TaskNode(
                task_id=node_data["task_id"],
                name=node_data["name"],
                description=node_data.get("description", ""),
                status=TaskStatus(node_data.get("status", "pending")),
                dependencies=node_data.get("dependencies", []),
                assigned_agent=node_data.get("assigned_agent"),
                result=node_data.get("result"),
                error=node_data.get("error"),
                created_at=datetime.fromisoformat(node_data["created_at"]),
                started_at=(
                    datetime.fromisoformat(node_data["started_at"])
                    if node_data.get("started_at")
                    else None
                ),
                completed_at=(
                    datetime.fromisoformat(node_data["completed_at"])
                    if node_data.get("completed_at")
                    else None
                ),
                metadata=node_data.get("metadata", {}),
            )
            self._nodes[task.task_id] = task
            self._adjacency.setdefault(task.task_id, set())
            self._reverse_adjacency.setdefault(task.task_id, set())
        # Rebuild adjacency from saved structure
        for tid, deps in data.get("adjacency", {}).items():
            self._adjacency[tid] = set(deps)
        # Rebuild reverse adjacency
        for tid, deps in self._adjacency.items():
            for dep in deps:
                self._reverse_adjacency.setdefault(dep, set()).add(tid)

    def to_json(self) -> str:
        """Convert graph to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def from_json(self, json_str: str) -> None:
        """Load graph from JSON string."""
        self.from_dict(json.loads(json_str))

    # ==================== Visualization ====================

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax."""
        lines = ["graph TD"]
        for tid, task in self._nodes.items():
            safe_id = tid.replace("-", "_")
            lines.append(f'    {safe_id}["{task.name}"]')
        for tid, downstream_ids in self._adjacency.items():
            safe_tid = tid.replace("-", "_")
            for dep in sorted(downstream_ids):
                safe_dep = dep.replace("-", "_")
                lines.append(f"    {safe_tid} --> {safe_dep}")
        return "\n".join(lines)

    def to_dot(self) -> str:
        """Generate DOT/Graphviz syntax."""
        lines = ["digraph TaskGraph {"]
        for tid, task in self._nodes.items():
            lines.append(f'    "{tid}" [label="{task.name}"];')
        for tid, downstream_ids in self._adjacency.items():
            for dep in sorted(downstream_ids):
                lines.append(f'    "{tid}" -> "{dep}";')
        lines.append("}")
        return "\n".join(lines)

    def get_ascii_representation(self) -> str:
        """Get ASCII representation of graph."""
        status_chars = {
            TaskStatus.PENDING: "○",
            TaskStatus.READY: "◎",
            TaskStatus.RUNNING: "●",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED: "✗",
            TaskStatus.SKIPPED: "⊘",
            TaskStatus.CANCELLED: "⊗",
        }
        lines = [f"TaskGraph ({len(self._nodes)} tasks)", "-" * 40]
        for task in self._nodes.values():
            char = status_chars.get(task.status, "?")
            deps = ", ".join(task.dependencies) if task.dependencies else "none"
            lines.append(f"  {char} [{task.task_id}] {task.name}  (deps: {deps})")
        return "\n".join(lines)

    # ==================== Cleanup ====================

    def clear(self) -> None:
        """Clear all tasks from graph."""
        self._nodes.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()

    def reset_statuses(self) -> None:
        """Reset all task statuses to pending."""
        for task in self._nodes.values():
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.result = None
            task.error = None

    def remove_completed(self) -> int:
        """Remove completed tasks. Returns count removed."""
        completed_ids = [
            tid for tid, t in self._nodes.items()
            if t.status == TaskStatus.COMPLETED
        ]
        for tid in completed_ids:
            self.remove_task(tid)
        return len(completed_ids)
