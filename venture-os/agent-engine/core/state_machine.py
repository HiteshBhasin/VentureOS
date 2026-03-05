# State machine for agent lifecycle management
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass


class AgentState(Enum):
    """Possible states for an agent."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class StateTransition:
    """Represents a state transition."""

    from_state: AgentState
    to_state: AgentState
    trigger: str
    condition: Optional[Callable[[], bool]] = None
    on_transition: Optional[Callable[[], None]] = None


class StateMachine:
    """Manages agent state transitions."""

    # Valid state transitions
    VALID_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
        AgentState.IDLE: {AgentState.INITIALIZING, AgentState.STOPPED},
        AgentState.INITIALIZING: {
            AgentState.RUNNING,
            AgentState.FAILED,
            AgentState.STOPPED,
        },
        AgentState.RUNNING: {
            AgentState.PAUSED,
            AgentState.WAITING,
            AgentState.COMPLETED,
            AgentState.FAILED,
            AgentState.STOPPED,
        },
        AgentState.PAUSED: {AgentState.RUNNING, AgentState.STOPPED},
        AgentState.WAITING: {AgentState.RUNNING, AgentState.FAILED, AgentState.STOPPED},
        AgentState.COMPLETED: {AgentState.IDLE},
        AgentState.FAILED: {AgentState.IDLE, AgentState.STOPPED},
        AgentState.STOPPED: set(),
    }

    def __init__(self, initial_state: AgentState = AgentState.IDLE):
        self._current_state = initial_state
        self._state_history: List[AgentState] = [initial_state]
        self._transitions: List[StateTransition] = []
        self._on_enter_callbacks: Dict[AgentState, List[Callable]] = {}
        self._on_exit_callbacks: Dict[AgentState, List[Callable]] = {}

    @property
    def current_state(self) -> AgentState:
        """Get the current state."""
        pass

    def can_transition_to(self, target_state: AgentState) -> bool:
        """Check if transition to target state is valid.

        Args:
            target_state: The state to transition to.

        Returns:
            True if transition is valid, False otherwise.
        """
        pass

    def transition_to(self, target_state: AgentState) -> bool:
        """Attempt to transition to target state.

        Args:
            target_state: The state to transition to.

        Returns:
            True if transition succeeded, False otherwise.
        """
        pass

    def on_enter(self, state: AgentState, callback: Callable) -> None:
        """Register a callback for entering a state.

        Args:
            state: The state to register the callback for.
            callback: Function to call when entering the state.
        """
        pass

    def on_exit(self, state: AgentState, callback: Callable) -> None:
        """Register a callback for exiting a state.

        Args:
            state: The state to register the callback for.
            callback: Function to call when exiting the state.
        """
        pass

    def get_history(self) -> List[AgentState]:
        """Get the state transition history."""
        pass

    def reset(self) -> None:
        """Reset the state machine to initial state."""
        pass

    def is_terminal(self) -> bool:
        """Check if current state is a terminal state."""
        pass

    def get_available_transitions(self) -> Set[AgentState]:
        """Get states that can be transitioned to from current state."""
        pass


class AgentStateMixin:
    """Mixin class to add state machine capabilities to agents."""

    def __init__(self):
        self._state_machine = StateMachine()

    def get_state(self) -> AgentState:
        """Get current agent state."""
        pass

    def set_state(self, state: AgentState) -> bool:
        """Set agent state with validation.

        Args:
            state: Target state.

        Returns:
            True if state change succeeded.
        """
        pass

    def is_running(self) -> bool:
        """Check if agent is currently running."""
        pass

    def is_idle(self) -> bool:
        """Check if agent is idle."""
        pass

    def is_finished(self) -> bool:
        """Check if agent has finished (completed, failed, or stopped)."""
        pass
