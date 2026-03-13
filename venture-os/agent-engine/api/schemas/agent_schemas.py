# Agent Pydantic schemas
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ==================== Enums ====================


class AgentType(str, Enum):
    """Agent types."""

    CODING = "coding"
    RESEARCH = "research"
    REVIEW = "review"
    RUNTIME = "runtime"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent status."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


# ==================== Base Schemas ====================


class AgentBase(BaseModel):
    """Base agent schema."""

    name: str = Field(..., min_length=1, max_length=100)
    agent_type: AgentType
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    """Schema for creating an agent."""

    model: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)


class AgentResponse(AgentBase):
    """Schema for agent response."""

    id: str
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    model: Optional[str] = None
    tools: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== Execution Schemas ====================


class AgentExecuteRequest(BaseModel):
    """Schema for agent execution request."""

    input: str
    context: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    max_steps: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=300, ge=1)
    stream: bool = False


class AgentExecuteResponse(BaseModel):
    """Schema for agent execution response."""

    execution_id: str
    agent_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    cost: float = 0.0


class ExecutionStatus(BaseModel):
    """Schema for execution status."""

    execution_id: str
    status: str
    progress: float = Field(ge=0.0, le=1.0)
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    started_at: datetime
    estimated_completion: Optional[datetime] = None


# ==================== Tool Schemas ====================


class ToolConfig(BaseModel):
    """Tool configuration."""

    name: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentToolsUpdate(BaseModel):
    """Schema for updating agent tools."""

    tools: List[ToolConfig]


# ==================== Stats Schemas ====================


class AgentStats(BaseModel):
    """Agent statistics."""

    agent_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    last_execution_at: Optional[datetime] = None


class AgentHealthCheck(BaseModel):
    """Agent health check response."""

    agent_id: str
    healthy: bool
    status: AgentStatus
    last_heartbeat: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    uptime_seconds: float = 0.0
    error_message: Optional[str] = None


# ==================== List Schemas ====================


class AgentListResponse(BaseModel):
    """Schema for listing agents."""

    agents: List[AgentResponse]
    total: int
    skip: int
    limit: int


class ExecutionHistoryItem(BaseModel):
    """Schema for execution history item."""

    execution_id: str
    input_summary: str
    status: str
    duration_ms: float
    tokens_used: int
    cost: float
    completed_at: datetime


class AgentHistoryResponse(BaseModel):
    """Schema for agent history."""

    agent_id: str
    history: List[ExecutionHistoryItem]
    total: int
    skip: int
    limit: int


# ==================== Type Schemas ====================


class AgentTypeInfo(BaseModel):
    """Information about an agent type."""

    type: AgentType
    name: str
    description: str
    capabilities: List[str]
    default_tools: List[str]
    config_schema: Dict[str, Any]


class AgentTypesResponse(BaseModel):
    """Response listing agent types."""

    types: List[AgentTypeInfo]
