# Pydantic models for agent configuration
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents."""

    BASE = "base"
    CODING = "coding"
    RESEARCH = "research"
    REVIEW = "review"
    RUNTIME = "runtime"
    META = "meta"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent status states."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class LLMConfig(BaseModel):
    """Configuration for LLM used by agent."""

    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens in response"
    )
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class MemoryConfig(BaseModel):
    """Configuration for agent memory."""

    enable_short_term: bool = Field(
        default=True, description="Enable short-term memory"
    )
    enable_long_term: bool = Field(default=True, description="Enable long-term memory")
    max_history: int = Field(default=100, description="Maximum history entries")
    vector_store_enabled: bool = Field(default=False, description="Enable vector store")


class ToolConfig(BaseModel):
    """Configuration for a single tool."""

    name: str = Field(..., description="Tool name")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool-specific config"
    )


class BudgetConfig(BaseModel):
    """Budget configuration for agent."""

    max_tokens: Optional[int] = Field(default=None, description="Maximum total tokens")
    max_cost: Optional[float] = Field(default=None, description="Maximum cost in USD")
    max_requests: Optional[int] = Field(
        default=None, description="Maximum LLM requests"
    )
    max_duration_seconds: Optional[int] = Field(
        default=None, description="Maximum execution time"
    )


class AgentConfig(BaseModel):
    """Complete agent configuration."""

    agent_type: AgentType = Field(default=AgentType.BASE, description="Type of agent")
    name: Optional[str] = Field(default=None, description="Agent name")
    description: Optional[str] = Field(default=None, description="Agent description")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig, description="Memory configuration"
    )
    tools: Optional[List[ToolConfig]] = Field(
        default=None, description="Tool configurations"
    )
    budget: Optional[BudgetConfig] = Field(default=None, description="Budget limits")
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt override"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class AgentInfo(BaseModel):
    """Runtime information about an agent."""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: AgentStatus = Field(..., description="Current status")
    name: Optional[str] = Field(default=None, description="Agent name")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    task_count: int = Field(default=0, description="Number of tasks executed")
    token_usage: int = Field(default=0, description="Total tokens used")
    cost: float = Field(default=0.0, description="Total cost incurred")


class AgentMetrics(BaseModel):
    """Metrics for agent performance."""

    agent_id: str = Field(..., description="Agent identifier")
    tasks_completed: int = Field(default=0, description="Completed task count")
    tasks_failed: int = Field(default=0, description="Failed task count")
    total_tokens: int = Field(default=0, description="Total tokens used")
    prompt_tokens: int = Field(default=0, description="Prompt tokens used")
    completion_tokens: int = Field(default=0, description="Completion tokens used")
    total_cost: float = Field(default=0.0, description="Total cost incurred")
    avg_task_duration: float = Field(
        default=0.0, description="Average task duration in seconds"
    )
    success_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Task success rate"
    )


class AgentSpawnRequest(BaseModel):
    """Request to spawn a new agent."""

    config: AgentConfig = Field(..., description="Agent configuration")
    task_id: Optional[str] = Field(default=None, description="Initial task to assign")
    auto_start: bool = Field(default=True, description="Start agent immediately")


class AgentSpawnResponse(BaseModel):
    """Response from agent spawn request."""

    agent_id: str = Field(..., description="Created agent ID")
    status: AgentStatus = Field(..., description="Initial status")
    info: AgentInfo = Field(..., description="Agent information")
