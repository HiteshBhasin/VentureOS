# Distributed tracing for debugging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import threading


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
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        self.events.append(SpanEvent(
            name=name,
            timestamp=datetime.utcnow(),
            attributes=attributes or {},
        ))

    def set_status(self, status: SpanStatus, error: Optional[str] = None) -> None:
        """Set span status."""
        self.status = status
        if error:
            self.error = error

    def end(self) -> None:
        """End the span."""
        self.end_time = datetime.utcnow()

    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000


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
        self._thread_local = threading.local()

    def _new_id(self) -> str:
        return uuid.uuid4().hex

    def start_trace(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Trace:
        """Start a new trace."""
        trace_id = self._new_id()
        root_span = self.start_span(name, attributes=attributes)
        root_span.context = SpanContext(trace_id=trace_id, span_id=root_span.context.span_id)
        trace = Trace(
            trace_id=trace_id,
            spans=[root_span],
            root_span=root_span,
            start_time=root_span.start_time,
            metadata={"service": self.service_name},
        )
        self._traces[trace_id] = trace
        return trace

    def start_span(
        self,
        name: str,
        parent_context: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span."""
        trace_id = parent_context.trace_id if parent_context else self._new_id()
        span_id = self._new_id()
        parent_id = parent_context.span_id if parent_context else None
        ctx = SpanContext(trace_id=trace_id, span_id=span_id, parent_span_id=parent_id)
        span = Span(
            name=name,
            context=ctx,
            start_time=datetime.utcnow(),
            attributes=attributes or {},
        )
        self._active_spans[span_id] = span
        # Track in trace if one exists
        trace = self._traces.get(trace_id)
        if trace and span is not trace.root_span:
            trace.spans.append(span)
        # Store current span on thread-local
        self._thread_local.current_span = span
        return span

    @contextmanager
    def span(
        self,
        name: str,
        parent_context: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for creating a span."""
        s = self.start_span(name, parent_context=parent_context, attributes=attributes)
        try:
            yield s
        except Exception as exc:
            s.set_status(SpanStatus.ERROR, str(exc))
            raise
        finally:
            s.end()
            self._active_spans.pop(s.context.span_id, None)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)

    def get_active_span(self) -> Optional[Span]:
        """Get the currently active span."""
        return getattr(self._thread_local, "current_span", None)

    def end_trace(self, trace_id: str) -> None:
        """End a trace."""
        trace = self._traces.get(trace_id)
        if trace is None:
            return
        trace.end_time = datetime.utcnow()
        if trace.root_span and trace.root_span.end_time is None:
            trace.root_span.end()


class AgentTracer:
    """Specialized tracer for agent operations."""

    def __init__(self, agent_id: str, tracer: Optional[Tracer] = None):
        self.agent_id = agent_id
        self._tracer = tracer or Tracer()

    @contextmanager
    def trace_task(self, task_id: str, task_name: str):
        """Trace a task execution."""
        with self._tracer.span(
            f"task.{task_name}",
            attributes={"agent.id": self.agent_id, "task.id": task_id, "task.name": task_name},
        ) as s:
            yield s

    @contextmanager
    def trace_llm_call(self, model: str, prompt_preview: str = ""):
        """Trace an LLM call."""
        with self._tracer.span(
            f"llm.{model}",
            attributes={"agent.id": self.agent_id, "llm.model": model, "llm.prompt_preview": prompt_preview[:200]},
        ) as s:
            yield s

    @contextmanager
    def trace_tool_call(self, tool_name: str, tool_input: Optional[Dict] = None):
        """Trace a tool invocation."""
        attrs: Dict[str, Any] = {"agent.id": self.agent_id, "tool.name": tool_name}
        if tool_input:
            attrs["tool.input_keys"] = list(tool_input.keys())
        with self._tracer.span(f"tool.{tool_name}", attributes=attrs) as s:
            yield s

    @contextmanager
    def trace_memory_op(self, operation: str, key: Optional[str] = None):
        """Trace a memory operation."""
        attrs: Dict[str, Any] = {"agent.id": self.agent_id, "memory.operation": operation}
        if key:
            attrs["memory.key"] = key
        with self._tracer.span(f"memory.{operation}", attributes=attrs) as s:
            yield s


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def create_agent_tracer(agent_id: str) -> AgentTracer:
    """Create a tracer for an agent."""
    return AgentTracer(agent_id=agent_id, tracer=get_tracer())
