# Pydantic models for task definitions
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of tasks."""

    CODING = "coding"
    RESEARCH = "research"
    REVIEW = "review"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    EXECUTION = "execution"
    CUSTOM = "custom"


class TaskInput(BaseModel):
    """Input data for a task."""

    content: str = Field(..., description="Main input content")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context"
    )
    files: Optional[List[str]] = Field(default=None, description="List of file paths")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Input metadata"
    )


class TaskOutput(BaseModel):
    """Output data from a task."""

    result: Any = Field(..., description="Task result")
    artifacts: Optional[List[str]] = Field(
        default=None, description="Generated artifacts"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Output metadata"
    )


class TaskDependency(BaseModel):
    """Task dependency definition."""

    task_id: str = Field(..., description="ID of dependent task")
    required: bool = Field(default=True, description="Whether dependency is required")
    condition: Optional[str] = Field(
        default=None, description="Condition for dependency"
    )


class TaskConfig(BaseModel):
    """Configuration for task execution."""

    timeout: Optional[int] = Field(default=None, description="Timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    allow_parallel: bool = Field(default=False, description="Allow parallel execution")
    require_approval: bool = Field(default=False, description="Require human approval")


class TaskDefinition(BaseModel):
    """Complete task definition."""

    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    description: Optional[str] = Field(default=None, description="Task description")
    type: TaskType = Field(default=TaskType.CUSTOM, description="Task type")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Task priority"
    )
    input: TaskInput = Field(..., description="Task input data")
    config: Optional[TaskConfig] = Field(default=None, description="Task configuration")
    dependencies: Optional[List[TaskDependency]] = Field(
        default=None, description="Task dependencies"
    )
    tags: Optional[List[str]] = Field(default=None, description="Task tags")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Task metadata"
    )


class TaskResult(BaseModel):
    """Result of task execution."""

    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Final task status")
    output: Optional[TaskOutput] = Field(default=None, description="Task output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    start_time: Optional[datetime] = Field(
        default=None, description="Execution start time"
    )
    end_time: Optional[datetime] = Field(default=None, description="Execution end time")
    duration_seconds: Optional[float] = Field(
        default=None, description="Execution duration"
    )
    token_usage: Optional[Dict[str, int]] = Field(
        default=None, description="Token usage stats"
    )
    cost: Optional[float] = Field(default=None, description="Execution cost")


class TaskBatch(BaseModel):
    """Batch of tasks for execution."""

    batch_id: str = Field(..., description="Batch identifier")
    tasks: List[TaskDefinition] = Field(..., description="List of tasks")
    parallel: bool = Field(default=False, description="Execute tasks in parallel")
    stop_on_failure: bool = Field(
        default=True, description="Stop batch on first failure"
    )
