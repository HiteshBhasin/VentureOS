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
        self.tool_registry = None
        self.config = config or {}
        self.status = "idle"  # idle, running, paused, stopped, error
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.code_context: Dict[str, Any] = {}

    def load_document_to_context(self, path: str, doc_id: Optional[str] = None) -> bool:
        """Load file content into code_context under doc_id (or path if not provided). Returns True if successful."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            key = doc_id if doc_id is not None else path
            self.code_context[key] = content
            return True
        except Exception as e:
            logging.error(f"Failed to load document '{path}': {e}")
            return False

    # ==================== Lifecycle Methods ====================

    def start(self) -> None:
        """Start the agent and set status to running."""
        self.status = "running"

    def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        self.status = "stopped"

    def complete(self) -> None:
        """Mark the agent as completed after all tasks finish."""
        self.status = "completed"

    def pause(self) -> None:
        """Pause the agent execution."""
        if self.status == "running" or self.status == "error":
            self.status = "paused"

    def resume(self) -> None:
        """Resume the agent from paused state."""
        if self.status == "paused":
            self.status = "running"

    def reset(self) -> None:
        """Reset the agent to initial state, clearing context and history."""
        self.context.clear()
        self.history.clear()

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
        try:
            response = self.llm.invoke(prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            self.status = "error"
            return None

    def use_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Call a real tool the orchestrator wired in (e.g. ``web_search``),
        as opposed to ``_invoke_llm`` which only ever produces text from the
        model's training data. Raises if no tool registry was injected, or
        if the tool isn't registered — callers should fall back to
        ``_invoke_llm`` in that case rather than fabricate a result."""
        if not self.tool_registry:
            raise RuntimeError(
                f"No tool registry available on this agent — cannot call '{tool_name}'"
            )
        return self.tool_registry.execute(tool_name, args)

    # ==================== Context & History ====================

    def add_to_context(self, key: str, value: Any) -> None:
        """Add data to agent's context."""
        self.context[key] = value

    def get_from_context(self, key: str) -> Optional[Any]:
        """Retrieve data from agent's context."""
        return self.context.get(key)

    def clear_context(self) -> None:
        """Clear all context data."""
        self.context.clear()

    def add_to_history(self, entry: Dict[str, Any]) -> None:
        """Add an entry to execution history."""
        self.history.append(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get full execution history."""
        return self.history

    # ==================== Tool Management ====================

    def register_tool(self, tool) -> None:
        """Register a tool for the agent to use."""
        self.tools.append(tool)

    def get_available_tools(self) -> List:
        """Get list of available tools."""
        return self.tools

    # ==================== Status & Info ====================

    def get_status(self) -> str:
        """Get current agent status."""
        return self.status

    def set_status(self, status: str) -> None:
        """Set agent status with validation."""
        self.status = status

    def get_info(self) -> Dict[str, Any]:
        """Get agent information and metadata."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "context": self.context,
            "history": self.history,
            "tools": self.tools,
            "config": self.config,
        }
