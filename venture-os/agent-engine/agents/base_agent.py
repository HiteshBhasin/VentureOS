# Abstract base agent class
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    def __init__(
        self,
        agent_id: str,
        llm,
        memory=None,
        tools: Optional[List] = None,
        config: Optional[Dict] = None,
    ):
        self.agent_id = agent_id
        self.llm = llm
        self.memory = memory
        self.tools = tools or []
        self.config = config or {}
        self.status = "idle"  # idle, running, paused, stopped, error
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

    # ==================== Lifecycle Methods ====================

    def start(self) -> None:
        """Start the agent and set status to running."""
        pass

    def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        pass

    def pause(self) -> None:
        """Pause the agent execution."""
        pass

    def resume(self) -> None:
        """Resume the agent from paused state."""
        pass

    def reset(self) -> None:
        """Reset the agent to initial state, clearing context and history."""
        pass

    # ==================== Core Execution ====================

    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the given task. Must be implemented by subclasses.

        Args:
            task: Task definition dictionary.

        Returns:
            Dict containing execution result and metadata.
        """
        raise NotImplementedError

    def _invoke_llm(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Invoke the LLM with error handling.

        Args:
            prompt: User prompt.
            system_prompt: System prompt for context.

        Returns:
            LLM response string or None on failure.
        """
        pass

    # ==================== Context & History ====================

    def add_to_context(self, key: str, value: Any) -> None:
        """Add data to agent's context."""
        pass

    def get_from_context(self, key: str) -> Optional[Any]:
        """Retrieve data from agent's context."""
        pass

    def clear_context(self) -> None:
        """Clear all context data."""
        pass

    def add_to_history(self, entry: Dict[str, Any]) -> None:
        """Add an entry to execution history."""
        pass

    def get_history(self) -> List[Dict[str, Any]]:
        """Get full execution history."""
        pass

    # ==================== Tool Management ====================

    def register_tool(self, tool) -> None:
        """Register a tool for the agent to use."""
        pass

    def get_available_tools(self) -> List:
        """Get list of available tools."""
        pass

    # ==================== Status & Info ====================

    def get_status(self) -> str:
        """Get current agent status."""
        pass

    def set_status(self, status: str) -> None:
        """Set agent status with validation."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get agent information and metadata."""
        pass
