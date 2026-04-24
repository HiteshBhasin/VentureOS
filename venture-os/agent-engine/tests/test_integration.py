"""Integration tests: verify core/ and agents/ work together correctly.

Run from the agent-engine directory:
    pytest tests/test_integration.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# ── core ──────────────────────────────────────────────────────────────────────
from core.budget_manager import BudgetManager, BudgetType
from core.events import EventBus, EventEmitter, EventType, Event
from core.task_graph import TaskGraph
from core.state_machine import StateMachine, AgentState
from core.meta_agent import Meta_agent
from core.validator import Validator, ValidationLevel

# ── agents ────────────────────────────────────────────────────────────────────
from agents.coding_agent import CodingAgent

# ── Shared mock LLM fixture ───────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    """LLM that returns a predictable string so tests don't hit OpenAI."""
    llm = MagicMock()
    llm.invoke.return_value = "def hello(): pass"
    return llm


@pytest.fixture
def mock_llm_json():
    """LLM that returns valid JSON for meta-agent tests."""
    import json

    llm = MagicMock()
    llm.invoke.return_value = json.dumps(
        {
            "primary_goal": "Build a payment service",
            "domain": "FinTech",
            "constraints": ["PCI-DSS compliant"],
            "required_capabilities": ["API design", "database schema", "unit tests"],
            "complexity_level": "medium",
        }
    )
    return llm


# ══════════════════════════════════════════════════════════════════════════════
#  1. CodingAgent — execute_task dispatches correctly
# ══════════════════════════════════════════════════════════════════════════════


class TestCodingAgent:

    def test_generate_code_task(self, mock_llm):
        agent = CodingAgent("agent-1", mock_llm)
        result = agent.execute_task(
            {
                "type": "generate_code",
                "specification": "A function that adds two numbers",
                "language": "python",
            }
        )
        assert result["status"] == "success"
        assert result["type"] == "generate_code"
        assert "code" in result
        mock_llm.invoke.assert_called_once()

    def test_generate_function_task(self, mock_llm):
        agent = CodingAgent("agent-2", mock_llm)
        result = agent.execute_task(
            {
                "type": "generate_function",
                "name": "add",
                "description": "Returns sum of a and b",
                "language": "python",
            }
        )
        assert result["status"] == "success"
        assert result["type"] == "generate_function"

    def test_generate_tests_task(self, mock_llm):
        agent = CodingAgent("agent-3", mock_llm)
        result = agent.execute_task(
            {
                "type": "generate_tests",
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
            }
        )
        assert result["status"] == "success"
        assert result["type"] == "generate_tests"

    def test_debug_code_task(self, mock_llm):
        agent = CodingAgent("agent-4", mock_llm)
        result = agent.execute_task(
            {
                "type": "debug_code",
                "code": "print(x)",
                "error_message": "NameError: name 'x' is not defined",
            }
        )
        assert result["status"] == "success"
        assert "explanation" in result
        assert "suggested_fix" in result

    def test_refactor_code_task(self, mock_llm):
        agent = CodingAgent("agent-5", mock_llm)
        result = agent.execute_task(
            {
                "type": "refactor_code",
                "code": "x = x + 1",
                "refactor_type": "readability",
            }
        )
        assert result["status"] == "success"

    def test_unsupported_task_type(self, mock_llm):
        agent = CodingAgent("agent-6", mock_llm)
        result = agent.execute_task({"type": "fly_to_moon"})
        assert "error" in result

    def test_agent_lifecycle(self, mock_llm):
        agent = CodingAgent("agent-7", mock_llm)
        assert agent.status == "idle"
        agent.start()
        assert agent.status == "running"
        agent.pause()
        assert agent.status == "paused"
        agent.resume()
        assert agent.status == "running"
        agent.stop()
        assert agent.status == "stopped"

    def test_project_context_sets_languages(self, mock_llm):
        agent = CodingAgent("agent-8", mock_llm)
        agent.set_project_context(
            {
                "name": "VentureOS",
                "supported_languages": ["python", "typescript"],
            }
        )
        assert "python" in agent.supported_languages
        assert "typescript" in agent.supported_languages

    def test_llm_failure_returns_error_status(self):
        bad_llm = MagicMock()
        bad_llm.invoke.side_effect = RuntimeError("quota exceeded")
        agent = CodingAgent("agent-9", bad_llm)
        result = agent.execute_task(
            {
                "type": "generate_code",
                "specification": "anything",
                "language": "python",
            }
        )
        # LLM failure returns empty string; status stays but code is empty
        assert "code" in result or "error" in result


# ══════════════════════════════════════════════════════════════════════════════
#  2. BudgetManager — token/cost tracking and enforcement
# ══════════════════════════════════════════════════════════════════════════════


class TestBudgetManager:

    def test_set_and_check_token_budget(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 1000.0)
        assert bm.check_budget(BudgetType.TOKENS, 500.0) is True  # 500 fits in 1000
        assert bm.check_budget(BudgetType.TOKENS, 1001.0) is False  # exceeds limit

    def test_token_usage_reduces_remaining(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 1000.0)
        bm.record_token_usage(300, 100, "gpt-4o")
        assert bm.get_current_usage(BudgetType.TOKENS) == 400.0
        assert bm.check_budget(BudgetType.TOKENS, 601.0) is False
        assert bm.check_budget(BudgetType.TOKENS, 600.0) is True

    def test_cost_recording_updates_limit(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.COST, 10.0)
        bm.record_cost(3.0, "openai", "gpt-4o call")
        assert bm.get_current_usage(BudgetType.COST) == 3.0
        assert bm.has_budget_for_cost(7.0) is True
        assert bm.has_budget_for_cost(7.01) is False

    def test_enforce_budget_raises_on_exceed(self):
        from core.exceptions import BudgetExceededError

        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 100.0)
        bm.enforce_budget(BudgetType.TOKENS, 80.0)  # OK
        with pytest.raises(BudgetExceededError):
            bm.enforce_budget(BudgetType.TOKENS, 30.0)  # 80 + 30 > 100

    def test_reserve_and_commit(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 500.0)
        rid = bm.reserve_budget(BudgetType.TOKENS, 200.0)
        assert bm.get_current_usage(BudgetType.TOKENS) == 200.0
        bm.commit_reservation(rid, 150.0)  # actual was less than reserved
        assert bm.get_current_usage(BudgetType.TOKENS) == 150.0

    def test_reserve_and_release(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 500.0)
        rid = bm.reserve_budget(BudgetType.TOKENS, 200.0)
        bm.release_reservation(rid)
        assert bm.get_current_usage(BudgetType.TOKENS) == 0.0

    def test_alerts_triggered(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 100.0)
        bm.add_alert(BudgetType.TOKENS, threshold_percent=80.0)
        bm.record_token_usage(80, 5, "gpt-4o")  # 85 tokens = 85%
        triggered = bm.check_alerts()
        assert len(triggered) == 1
        assert triggered[0].budget_type == BudgetType.TOKENS

    def test_set_all_limits(self):
        bm = BudgetManager()
        bm.set_all_limits({"tokens": 5000.0, "cost": 20.0})
        assert bm.get_current_usage(BudgetType.TOKENS) == 0.0
        assert bm.check_budget(BudgetType.COST, 15.0) is True

    def test_reset_usage(self):
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 1000.0)
        bm.record_token_usage(400, 100, "gpt-4o")
        bm.reset_usage(BudgetType.TOKENS)
        assert bm.get_current_usage(BudgetType.TOKENS) == 0.0


# ══════════════════════════════════════════════════════════════════════════════
#  3. EventBus — subscribe, publish, history
# ══════════════════════════════════════════════════════════════════════════════


class TestEventBus:

    def _make_event(self, event_type: EventType) -> Event:
        return Event(
            event_type=event_type,
            source="test",
            timestamp=datetime.now(),
            data={"key": "value"},
        )

    def test_single_subscriber_receives_event(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TASK_COMPLETED, lambda e: received.append(e))
        event = self._make_event(EventType.TASK_COMPLETED)
        bus.publish(event)
        assert len(received) == 1
        assert received[0] is event

    def test_multiple_subscribers_all_notified(self):
        bus = EventBus()
        calls = []
        bus.subscribe(EventType.AGENT_STARTED, lambda e: calls.append("h1"))
        bus.subscribe(EventType.AGENT_STARTED, lambda e: calls.append("h2"))
        bus.publish(self._make_event(EventType.AGENT_STARTED))
        assert calls == ["h1", "h2"]

    def test_unrelated_event_type_not_received(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TASK_FAILED, lambda e: received.append(e))
        bus.publish(self._make_event(EventType.TASK_COMPLETED))
        assert received == []

    def test_event_stored_in_history(self):
        bus = EventBus()
        bus.publish(self._make_event(EventType.LLM_REQUEST))
        history = bus.get_history()
        assert len(history) == 1

    def test_get_history_filtered_by_type(self):
        bus = EventBus()
        bus.publish(self._make_event(EventType.TASK_COMPLETED))
        bus.publish(self._make_event(EventType.TASK_FAILED))
        bus.publish(self._make_event(EventType.TASK_COMPLETED))
        completed = bus.get_history(EventType.TASK_COMPLETED)
        assert len(completed) == 2

    def test_clear_history(self):
        bus = EventBus()
        bus.publish(self._make_event(EventType.AGENT_STOPPED))
        bus.clear_history()
        assert bus.get_history() == []

    def test_unsubscribe(self):
        bus = EventBus()
        calls = []
        handler = lambda e: calls.append(e)
        bus.subscribe(EventType.TOOL_INVOKED, handler)
        bus.unsubscribe(EventType.TOOL_INVOKED, handler)
        bus.publish(self._make_event(EventType.TOOL_INVOKED))
        assert calls == []

    def test_event_emitter_publishes_to_bus(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TASK_STARTED, lambda e: received.append(e))
        emitter = EventEmitter(event_bus=bus)
        emitter.emit(EventType.TASK_STARTED, {"task_id": "t1"})
        assert len(received) == 1
        assert received[0].data["task_id"] == "t1"


# ══════════════════════════════════════════════════════════════════════════════
#  4. TaskGraph — dependency management and scheduling
# ══════════════════════════════════════════════════════════════════════════════


class TestTaskGraph:

    def test_add_and_retrieve_tasks(self):
        tg = TaskGraph()
        tg.add_task("t1", {"name": "Design API"})
        tg.add_task("t2", {"name": "Implement API"})
        assert tg.get_task("t1") is not None
        assert len(tg.get_all_tasks()) == 2

    def test_dependency_ordering(self):
        tg = TaskGraph()
        tg.add_task("t1", {"name": "Design"})
        tg.add_task("t2", {"name": "Implement"})
        tg.add_task("t3", {"name": "Test"})
        tg.add_dependency("t2", "t1")  # t2 depends on t1
        tg.add_dependency("t3", "t2")  # t3 depends on t2
        order = tg.topological_sort()
        assert order.index("t1") < order.index("t2") < order.index("t3")

    def test_ready_tasks_with_no_deps(self):
        tg = TaskGraph()
        tg.add_task("t1", {})
        tg.add_task("t2", {})
        tg.add_dependency("t2", "t1")
        ready = [t.task_id for t in tg.get_ready_tasks()]
        assert "t1" in ready
        assert "t2" not in ready

    def test_completing_task_unlocks_dependent(self):
        tg = TaskGraph()
        tg.add_task("t1", {})
        tg.add_task("t2", {})
        tg.add_dependency("t2", "t1")
        tg.mark_task_started("t1")
        tg.mark_task_completed("t1")
        ready = [t.task_id for t in tg.get_ready_tasks()]
        assert "t2" in ready

    def test_cycle_detection(self):
        tg = TaskGraph()
        tg.add_task("t1", {})
        tg.add_task("t2", {})
        tg.add_dependency("t2", "t1")
        with pytest.raises(ValueError):
            tg.add_dependency("t1", "t2")  # would create a cycle

    def test_is_complete_all_done(self):
        tg = TaskGraph()
        tg.add_task("t1", {})
        tg.mark_task_started("t1")
        tg.mark_task_completed("t1")
        assert tg.is_complete() is True

    def test_progress_tracking(self):
        tg = TaskGraph()
        tg.add_task("t1", {})
        tg.add_task("t2", {})
        tg.mark_task_started("t1")
        tg.mark_task_completed("t1")
        progress = tg.get_progress()
        assert progress["total"] == 2
        assert progress["completed"] == 1


# ══════════════════════════════════════════════════════════════════════════════
#  5. StateMachine — agent lifecycle transitions
# ══════════════════════════════════════════════════════════════════════════════


class TestStateMachine:

    def test_initial_state_is_idle(self):
        sm = StateMachine()
        assert sm.current_state == AgentState.IDLE

    def test_valid_transition_idle_to_running(self):
        sm = StateMachine()
        result = sm.transition_to(AgentState.RUNNING)
        assert result is True
        assert sm.current_state == AgentState.RUNNING

    def test_invalid_transition_raises_or_returns_false(self):
        sm = StateMachine()
        # IDLE → COMPLETED is not a valid transition
        result = sm.transition_to(AgentState.COMPLETED)
        assert result is False
        assert sm.current_state == AgentState.IDLE

    def test_history_records_transitions(self):
        sm = StateMachine()
        sm.transition_to(AgentState.RUNNING)
        sm.transition_to(AgentState.PAUSED)
        history = sm.get_history()
        assert len(history) >= 2

    def test_reset_returns_to_idle(self):
        sm = StateMachine()
        sm.transition_to(AgentState.RUNNING)
        sm.reset()
        assert sm.current_state == AgentState.IDLE

    def test_terminal_states(self):
        sm = StateMachine()
        sm.transition_to(AgentState.RUNNING)
        sm.transition_to(AgentState.COMPLETED)
        assert sm.is_terminal() is True


# ══════════════════════════════════════════════════════════════════════════════
#  6. Meta_agent — goal decomposition and task supervision
# ══════════════════════════════════════════════════════════════════════════════


class TestMetaAgent:

    def test_decompose_goals_returns_tasks(self, mock_llm_json):
        meta = Meta_agent(mock_llm_json)
        response = meta.analyze_user_requirement("Build a payment service")
        tasks = meta.decompose_goals(response)
        assert len(tasks) == 3
        assert all(t["status"] == "pending" for t in tasks)
        assert all("task_name" in t for t in tasks)

    def test_decompose_goals_wrong_shape_returns_empty(self, mock_llm):
        meta = Meta_agent(mock_llm)
        # Response that is a list (wrong shape)
        tasks = meta.decompose_goals(["not", "a", "dict"])
        assert tasks == []

    def test_create_task_graph_respects_order(self, mock_llm_json):
        meta = Meta_agent(mock_llm_json)
        response = meta.analyze_user_requirement("Build something")
        tasks = meta.decompose_goals(response)
        ordered = meta.create_task_graph(tasks)
        assert isinstance(ordered, list)
        assert len(ordered) == len(tasks)

    def test_supervise_spawns_agents_for_pending(self, mock_llm_json):
        meta = Meta_agent(mock_llm_json)
        response = meta.analyze_user_requirement("Build something")
        tasks = meta.decompose_goals(response)
        with patch.object(
            meta, "spawn_base_agent", return_value=MagicMock()
        ) as mock_spawn:
            meta.supervise(tasks)
            assert mock_spawn.call_count == len(tasks)

    def test_supervise_no_typo_in_status_check(self, mock_llm):
        meta = Meta_agent(mock_llm)
        tasks = [
            {
                "task_name": "t1",
                "status": "pending",
                "assigned_agent": None,
                "dependencies": [],
            }
        ]
        with patch.object(meta, "spawn_base_agent", return_value=MagicMock()):
            meta.supervise(tasks)
        # "pending" must be matched — if the old "peneding" typo were present, status would never change
        assert tasks[0]["status"] == "in progress"

    def test_refine_strategy_resets_failed_tasks(self, mock_llm):
        meta = Meta_agent(mock_llm)
        meta._tasks = [
            {
                "task_name": "t1",
                "status": "failed",
                "assigned_agent": "a1",
                "dependencies": [],
            },
            {
                "task_name": "t2",
                "status": "pending",
                "assigned_agent": None,
                "dependencies": [],
            },
        ]
        meta.refine_strategy()
        assert meta._tasks[0]["status"] == "pending"
        assert meta._tasks[0]["assigned_agent"] is None


# ══════════════════════════════════════════════════════════════════════════════
#  7. Integration: Meta_agent → TaskGraph → CodingAgent end-to-end
# ══════════════════════════════════════════════════════════════════════════════


class TestCoreAgentsIntegration:

    def test_full_pipeline(self, mock_llm_json, mock_llm):
        """
        Meta_agent decomposes a goal → tasks are added to TaskGraph →
        ready tasks are dispatched to CodingAgent → results collected.
        """
        # 1. Meta-agent decomposes the user goal
        meta = Meta_agent(mock_llm_json)
        analysis = meta.analyze_user_requirement("Build a payment service")
        tasks = meta.decompose_goals(analysis)
        assert len(tasks) > 0

        # 2. Load tasks into a TaskGraph
        tg = TaskGraph()
        for t in tasks:
            tg.add_task(t["task_name"], t)

        # 3. Wire a BudgetManager and EventBus
        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 10_000.0)
        bus = EventBus()
        completed_events = []
        bus.subscribe(EventType.TASK_COMPLETED, lambda e: completed_events.append(e))

        # 4. CodingAgent processes ready tasks
        agent = CodingAgent("integration-agent", mock_llm)
        agent.start()

        for _ in range(len(tasks)):
            ready = tg.get_ready_tasks()
            if not ready:
                break
            for node in ready:
                task_def = {
                    "type": "generate_code",
                    "specification": node.task_id,
                    "language": "python",
                }
                result = agent.execute_task(task_def)
                assert result["status"] == "success"

                # Simulate token budget tracking
                bm.record_token_usage(50, 50, "gpt-4o")

                # Mark task done in graph and emit event
                tg.mark_task_started(node.task_id)
                tg.mark_task_completed(node.task_id)
                bus.publish(
                    Event(
                        event_type=EventType.TASK_COMPLETED,
                        source="integration-agent",
                        timestamp=datetime.now(),
                        data={"task_id": node.task_id, "result": result},
                    )
                )

        assert tg.is_complete()
        assert len(completed_events) == len(tasks)
        total_tokens = bm.get_current_usage(BudgetType.TOKENS)
        assert total_tokens == len(tasks) * 100.0

    def test_budget_stops_agent_when_exceeded(self, mock_llm):
        """Enforce budget raises an error before the agent can run a task."""
        from core.exceptions import BudgetExceededError

        bm = BudgetManager()
        bm.set_budget_limit(BudgetType.TOKENS, 50.0)
        bm.record_token_usage(50, 0, "gpt-4o")  # exhaust budget

        agent = CodingAgent("budget-agent", mock_llm)
        agent.start()

        with pytest.raises(BudgetExceededError):
            bm.enforce_budget(BudgetType.TOKENS, 1.0)  # should raise

    def test_event_bus_wires_state_machine(self):
        """EventBus can observe StateMachine state changes via callbacks."""
        bus = EventBus()
        state_events = []
        bus.subscribe(
            EventType.AGENT_STARTED, lambda e: state_events.append(e.data.get("state"))
        )

        sm = StateMachine()
        sm.on_enter(
            AgentState.RUNNING,
            lambda: bus.publish(
                Event(
                    event_type=EventType.AGENT_STARTED,
                    source="state_machine",
                    timestamp=datetime.now(),
                    data={"state": AgentState.RUNNING.value},
                )
            ),
        )
        sm.transition_to(AgentState.RUNNING)

        assert AgentState.RUNNING.value in state_events
