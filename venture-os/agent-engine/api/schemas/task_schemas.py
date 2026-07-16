# Task Pydantic schemas
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ==================== Enums ====================


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(str, Enum):
    """Task types."""

    SIMPLE = "simple"
    COMPOSITE = "composite"
    RECURRING = "recurring"
    SCHEDULED = "scheduled"


# ==================== Base Schemas ====================


class TaskBase(BaseModel):
    """Base task schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: TaskType = TaskType.SIMPLE
    priority: TaskPriority = TaskPriority.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    input: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    timeout: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0, le=10)
    scheduled_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    agent_id: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=1)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: str
    status: TaskStatus
    agent_id: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: int
    max_retries: int
    retry_count: int = 0
    tags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== Execution Schemas ====================


class TaskResult(BaseModel):
    """Task execution result."""

    task_id: str
    status: TaskStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    retry_count: int = 0
    agent_id: Optional[str] = None


class TaskProgress(BaseModel):
    """Task progress information."""

    task_id: str
    status: TaskStatus
    progress_percent: float = Field(ge=0.0, le=100.0)
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    messages: List[str] = Field(default_factory=list)


class TaskLog(BaseModel):
    """Task log entry."""

    timestamp: datetime
    level: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskLogsResponse(BaseModel):
    """Response for task logs."""

    task_id: str
    logs: List[TaskLog]
    total: int
    skip: int
    limit: int


# ==================== Dependency Schemas ====================


class TaskDependency(BaseModel):
    """Task dependency information."""

    task_id: str
    dependency_id: str
    dependency_name: str
    dependency_status: TaskStatus


class TaskDependenciesResponse(BaseModel):
    """Response for task dependencies."""

    task_id: str
    dependencies: List[TaskDependency]
    dependents: List[TaskDependency]


# ==================== Graph Schemas ====================


class TaskGraphNode(BaseModel):
    """Node in task graph."""

    id: str
    name: str
    status: TaskStatus
    dependencies: List[str]


class TaskGraphResponse(BaseModel):
    """Task graph representation."""

    nodes: List[TaskGraphNode]
    edges: List[Dict[str, str]]
    has_cycles: bool = False
    execution_order: List[str] = Field(default_factory=list)


class TaskGraphStatus(BaseModel):
    """Task graph execution status."""

    total_tasks: int
    pending: int
    queued: int
    running: int
    completed: int
    failed: int
    progress_percent: float


# ==================== Bulk Schemas ====================


class TaskBulkCreate(BaseModel):
    """Schema for bulk task creation."""

    tasks: List[TaskCreate]


class TaskBulkResponse(BaseModel):
    """Response for bulk operations."""

    successful: List[str]
    failed: List[Dict[str, Any]]
    total: int
    success_count: int
    failure_count: int


class TaskBulkStatusUpdate(BaseModel):
    """Schema for bulk status update."""

    task_ids: List[str]
    status: TaskStatus


# ==================== List Schemas ====================


class TaskListResponse(BaseModel):
    """Schema for listing tasks."""

    tasks: List[TaskResponse]
    total: int
    skip: int
    limit: int


class TasksByAgentResponse(BaseModel):
    """Tasks assigned to an agent."""

    agent_id: str
    tasks: List[TaskResponse]
    total: int


# ==================== Stats Schemas ====================


class TaskStats(BaseModel):
    """Task statistics."""

    total_tasks: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    average_duration_ms: float = 0.0
    success_rate: float = 0.0
    tasks_today: int = 0
    tasks_this_week: int = 0


class TaskMetrics(BaseModel):
    """Task metrics for time range."""

    start_time: datetime
    end_time: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_wait_time_ms: float
    average_execution_time_ms: float
    throughput_per_hour: float
