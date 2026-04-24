# Event system for agent communication
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class EventType(Enum):
    """Enumeration of event types in the system."""

    # Agent lifecycle events
    AGENT_CREATED = "agent_created"
    AGENT_STARTED = "agent_started"
    AGENT_PAUSED = "agent_paused"
    AGENT_RESUMED = "agent_resumed"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"

    # Task events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # LLM events
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"

    # Tool events
    TOOL_INVOKED = "tool_invoked"
    TOOL_COMPLETED = "tool_completed"
    TOOL_ERROR = "tool_error"

    # Memory events
    MEMORY_STORED = "memory_stored"
    MEMORY_RETRIEVED = "memory_retrieved"

    # Budget events
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass
class Event:
    """Represents an event in the system."""

    event_type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None


class EventBus:
    """Central event bus for publishing and subscribing to events."""

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: Callback function to invoke when event is published.
        """
        self._subscribers.setdefault(event_type, []).append(handler)
        logging.info(f"Subscribed handler to event type: {event_type}")

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event to unsubscribe from.
            handler: The handler to remove.
        """
        self._subscribers.get(event_type, []).remove(handler)
        logging.info(f"Unsubscribed handler from event type: {event_type}")

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish.
        """
        self._event_history.append(event)
        for handler in self._subscribers.get(event.event_type, []):
            handler(event)

    async def publish_async(self, event: Event) -> None:
        """Publish an event asynchronously.

        Args:
            event: The event to publish.
        """
        handlers = self._subscribers.get(event.event_type, [])
        await asyncio.gather(*[handler(event) for handler in handlers])

    def get_history(
        self, event_type: Optional[EventType] = None, limit: int = 100
    ) -> List[Event]:
        """Get event history, optionally filtered by type.

        Args:
            event_type: Optional filter for event type.
            limit: Maximum number of events to return.

        Returns:
            List of events.
        """

        return (
            self._event_history[-limit:]
            if event_type is None
            else [
                event for event in self._event_history if event.event_type == event_type
            ][:limit]
        )

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()


class EventEmitter:
    """Mixin class to add event emission capabilities to agents."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for this emitter."""
        self._event_bus = event_bus

    def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """Emit an event.

        Args:
            event_type: Type of event to emit.
            data: Event data payload.
            correlation_id: Optional correlation ID for tracing.
        """
        if self._event_bus is None:
            logging.warning(f"No event bus set, cannot emit {event_type}")
            return

        event = Event(
            event_type=event_type,
            source=self.__class__.__name__,
            timestamp=datetime.now(),
            data=data,
            correlation_id=correlation_id,
        )
        self._event_bus.publish(event)
