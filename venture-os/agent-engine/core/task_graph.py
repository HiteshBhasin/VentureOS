# Task Graph: DAG of tasks
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
        pass

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the graph."""
        pass

    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """Get a task by ID."""
        pass

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task properties."""
        pass

    def get_all_tasks(self) -> List[TaskNode]:
        """Get all tasks in the graph."""
        pass

    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskNode]:
        """Get tasks with specific status."""
        pass

    # ==================== Dependency Management ====================

    def add_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Add a dependency between tasks."""
        pass

    def remove_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Remove a dependency between tasks."""
        pass

    def get_dependencies(self, task_id: str) -> List[str]:
        """Get dependencies of a task."""
        pass

    def get_dependents(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task."""
        pass

    def has_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Check if dependency exists."""
        pass

    def get_all_upstream(self, task_id: str) -> Set[str]:
        """Get all upstream tasks (transitive dependencies)."""
        pass

    def get_all_downstream(self, task_id: str) -> Set[str]:
        """Get all downstream tasks (transitive dependents)."""
        pass

    # ==================== Graph Operations ====================

    def topological_sort(self) -> List[str]:
        """Return tasks in topological order."""
        pass

    def validate(self) -> Dict[str, Any]:
        """Validate the graph (check for cycles, missing deps)."""
        pass

    def has_cycle(self) -> bool:
        """Check if graph has a cycle."""
        pass

    def detect_cycles(self) -> List[List[str]]:
        """Detect and return all cycles in the graph."""
        pass

    def get_critical_path(self) -> List[str]:
        """Get the critical path through the graph."""
        pass

    def get_parallel_groups(self) -> List[List[str]]:
        """Get groups of tasks that can run in parallel."""
        pass

    # ==================== Execution Management ====================

    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks ready for execution (dependencies satisfied)."""
        pass

    def are_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all dependencies are completed."""
        pass

    def mark_task_started(self, task_id: str, agent_id: Optional[str] = None) -> None:
        """Mark task as started."""
        pass

    def mark_task_completed(self, task_id: str, result: Any = None) -> None:
        """Mark task as completed."""
        pass

    def mark_task_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        pass

    def mark_task_skipped(self, task_id: str, reason: str = "") -> None:
        """Mark task as skipped."""
        pass

    def mark_task_cancelled(self, task_id: str) -> None:
        """Mark task as cancelled."""
        pass

    def propagate_failure(self, task_id: str) -> List[str]:
        """Propagate failure to dependent tasks."""
        pass

    # ==================== Query Operations ====================

    def get_leaf_tasks(self) -> List[TaskNode]:
        """Get tasks with no dependencies."""
        pass

    def get_root_tasks(self) -> List[TaskNode]:
        """Get tasks with no dependents."""
        pass

    def get_pending_count(self) -> int:
        """Get count of pending tasks."""
        pass

    def get_completed_count(self) -> int:
        """Get count of completed tasks."""
        pass

    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress statistics."""
        pass

    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        pass

    def has_failures(self) -> bool:
        """Check if any tasks have failed."""
        pass

    # ==================== Serialization ====================

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        pass

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load graph from dictionary."""
        pass

    def to_json(self) -> str:
        """Convert graph to JSON string."""
        pass

    def from_json(self, json_str: str) -> None:
        """Load graph from JSON string."""
        pass

    # ==================== Visualization ====================

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax."""
        pass

    def to_dot(self) -> str:
        """Generate DOT/Graphviz syntax."""
        pass

    def get_ascii_representation(self) -> str:
        """Get ASCII representation of graph."""
        pass

    # ==================== Cleanup ====================

    def clear(self) -> None:
        """Clear all tasks from graph."""
        pass

    def reset_statuses(self) -> None:
        """Reset all task statuses to pending."""
        pass

    def remove_completed(self) -> int:
        """Remove completed tasks. Returns count removed."""
        pass
