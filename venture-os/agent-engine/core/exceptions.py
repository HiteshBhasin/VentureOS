# Custom exceptions for the agent engine
from typing import Any, Optional


class AgentEngineError(Exception):
    """Base exception for all agent engine errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


# ==================== Agent Errors ====================


class AgentError(AgentEngineError):
    """Base exception for agent-related errors."""

    pass


class AgentNotFoundError(AgentError):
    """Raised when an agent cannot be found."""

    pass


class AgentCreationError(AgentError):
    """Raised when agent creation fails."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class AgentStateError(AgentError):
    """Raised when an invalid state transition is attempted."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    pass


# ==================== Task Errors ====================


class TaskError(AgentEngineError):
    """Base exception for task-related errors."""

    pass


class TaskNotFoundError(TaskError):
    """Raised when a task cannot be found."""

    pass


class TaskValidationError(TaskError):
    """Raised when task validation fails."""

    pass


class TaskExecutionError(TaskError):
    """Raised when task execution fails."""

    pass


class TaskDependencyError(TaskError):
    """Raised when task dependencies cannot be resolved."""

    pass


# ==================== LLM Errors ====================


class LLMError(AgentEngineError):
    """Base exception for LLM-related errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM fails."""

    pass


class LLMResponseError(LLMError):
    """Raised when LLM returns an invalid response."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""

    pass


# ==================== Budget Errors ====================


class BudgetError(AgentEngineError):
    """Base exception for budget-related errors."""

    pass


class BudgetExceededError(BudgetError):
    """Raised when budget limit is exceeded."""

    pass


class TokenLimitExceededError(BudgetError):
    """Raised when token limit is exceeded."""

    pass


# ==================== Tool Errors ====================


class ToolError(AgentEngineError):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Raised when a tool cannot be found."""

    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    pass


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    pass


# ==================== Memory Errors ====================


class MemoryError(AgentEngineError):
    """Base exception for memory-related errors."""

    pass


class MemoryStoreError(MemoryError):
    """Raised when memory storage fails."""

    pass


class MemoryRetrievalError(MemoryError):
    """Raised when memory retrieval fails."""

    pass


# ==================== Configuration Errors ====================


class ConfigurationError(AgentEngineError):
    """Base exception for configuration-related errors."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    pass
