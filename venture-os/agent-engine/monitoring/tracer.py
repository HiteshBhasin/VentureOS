# Distributed tracing for debugging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager


class SpanStatus(Enum):
    """Status of a trace span."""

    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class SpanContext:
    """Context for trace propagation."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None


@dataclass
class SpanEvent:
    """Event within a span."""

    name: str
    timestamp: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """A single span in a trace."""

    name: str
    context: SpanContext
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.OK
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    error: Optional[str] = None

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        pass

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        pass

    def set_status(self, status: SpanStatus, error: Optional[str] = None) -> None:
        """Set span status."""
        pass

    def end(self) -> None:
        """End the span."""
        pass

    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        pass


@dataclass
class Trace:
    """A complete trace containing multiple spans."""

    trace_id: str
    spans: List[Span] = field(default_factory=list)
    root_span: Optional[Span] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Tracer:
    """Tracer for creating and managing spans."""

    def __init__(self, service_name: str = "agent-engine"):
        self.service_name = service_name
        self._traces: Dict[str, Trace] = {}
        self._active_spans: Dict[str, Span] = {}

    def start_trace(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Trace:
        """Start a new trace.

        Args:
            name: Name of the root span.
            attributes: Optional attributes for the root span.

        Returns:
            New Trace object.
        """
        pass

    def start_span(
        self,
        name: str,
        parent_context: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span.

        Args:
            name: Span name.
            parent_context: Optional parent span context.
            attributes: Optional span attributes.

        Returns:
            New Span object.
        """
        pass

    @contextmanager
    def span(
        self,
        name: str,
        parent_context: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for creating a span.

        Args:
            name: Span name.
            parent_context: Optional parent span context.
            attributes: Optional span attributes.

        Yields:
            Active Span object.
        """
        pass

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID.

        Args:
            trace_id: Trace identifier.

        Returns:
            Trace object or None.
        """
        pass

    def get_active_span(self) -> Optional[Span]:
        """Get the currently active span."""
        pass

    def end_trace(self, trace_id: str) -> None:
        """End a trace.

        Args:
            trace_id: Trace identifier.
        """
        pass


class AgentTracer:
    """Specialized tracer for agent operations."""

    def __init__(self, agent_id: str, tracer: Optional[Tracer] = None):
        self.agent_id = agent_id
        self._tracer = tracer or Tracer()

    @contextmanager
    def trace_task(self, task_id: str, task_name: str):
        """Trace a task execution.

        Args:
            task_id: Task identifier.
            task_name: Task name.

        Yields:
            Active Span.
        """
        pass

    @contextmanager
    def trace_llm_call(self, model: str, prompt_preview: str = ""):
        """Trace an LLM call.

        Args:
            model: Model name.
            prompt_preview: Preview of the prompt.

        Yields:
            Active Span.
        """
        pass

    @contextmanager
    def trace_tool_call(self, tool_name: str, tool_input: Optional[Dict] = None):
        """Trace a tool invocation.

        Args:
            tool_name: Name of the tool.
            tool_input: Optional tool input.

        Yields:
            Active Span.
        """
        pass

    @contextmanager
    def trace_memory_op(self, operation: str, key: Optional[str] = None):
        """Trace a memory operation.

        Args:
            operation: Operation type (store, retrieve, etc.).
            key: Optional memory key.

        Yields:
            Active Span.
        """
        pass


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    pass


def create_agent_tracer(agent_id: str) -> AgentTracer:
    """Create a tracer for an agent.

    Args:
        agent_id: Agent identifier.

    Returns:
        AgentTracer instance.
    """
    pass
