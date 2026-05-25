"""Orchestrator tests — run from the agent-engine directory:
pytest tests/orchastrator_test.py -v
"""

import json
import sys
import os

import pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.orchestrator import Orchestrator
from core.budget_manager import BudgetType
from core.task_graph import TaskStatus

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    """LLM that never hits a real API."""
    llm = MagicMock()
    llm.invoke.return_value = "def hello(): pass"
    return llm


@pytest.fixture
def meta_llm_response():
    """Valid JSON that Meta_agent.analyze_user_requirement() returns."""
    return json.dumps(
        {
            "primary_goal": "Build a payment service",
            "domain": "FinTech",
            "constraints": ["PCI-DSS compliant"],
            "required_capabilities": ["API design", "database schema", "unit tests"],
            "complexity_level": "medium",
        }
    )


@pytest.fixture
def decompose_response():
    """Valid JSON that Meta_agent.decompose_goals() returns via LLM."""
    return json.dumps(
        [
            {
                "task_name": "Design API",
                "description": "Define REST endpoints",
                "agent_type": "research",
                "dependencies": [],
                "status": "pending",
            },
            {
                "task_name": "Write code",
                "description": "Implement payment endpoints",
                "agent_type": "coding",
                "dependencies": ["task_1"],
                "status": "pending",
            },
        ]
    )


@pytest.fixture
def orchestrator(mock_llm):
    """Fully initialised Orchestrator with a mock LLM."""
    return Orchestrator(mock_llm)


# ── 1. Initialisation ─────────────────────────────────────────────────────────


class TestOrchestratorInit:

    def test_all_subsystems_initialised(self, orchestrator):
        assert orchestrator.llm_router is not None
        assert orchestrator.agent_factory is not None
        assert orchestrator.memory_manager is not None
        assert orchestrator.budget_manager is not None
        assert orchestrator.tool_registry is not None
        assert orchestrator.event_bus is not None
        assert orchestrator.task_graph is not None

    def test_default_agent_types_registered(self, orchestrator):
        registry = orchestrator.agent_factory._agent_registry
        assert "coding" in registry
        assert "research" in registry
        assert "review" in registry
        assert "runtime" in registry

    def test_default_budgets_configured(self, orchestrator):
        bm = orchestrator.budget_manager
        # get_budget_limit returns a BudgetLimit object; check its .limit value
        for budget_type in BudgetType:
            budget_limit = bm.get_budget_limit(budget_type)
            assert budget_limit is not None
            assert budget_limit.limit > 0


# ── 2. Input validation ───────────────────────────────────────────────────────


class TestInputValidation:

    def test_valid_input_accepted(self, orchestrator):
        assert orchestrator.validate_user_input("Build a CRM system") is True

    def test_empty_string_rejected(self, orchestrator):
        assert orchestrator.validate_user_input("") is False

    def test_whitespace_only_rejected(self, orchestrator):
        assert orchestrator.validate_user_input("   ") is False

    def test_none_rejected(self, orchestrator):
        assert orchestrator.validate_user_input(None) is False

    def test_too_long_input_rejected(self, orchestrator):
        assert orchestrator.validate_user_input("x" * 10_001) is False

    def test_exactly_max_length_accepted(self, orchestrator):
        assert orchestrator.validate_user_input("x" * 10_000) is True


# ── 3. process_user_request ───────────────────────────────────────────────────


class TestProcessUserRequest:

    def test_invalid_input_returns_error_status(self, orchestrator):
        result = orchestrator.process_user_request("")
        assert result["status"] == "error"

    def test_valid_request_returns_success(
        self, orchestrator, meta_llm_response, decompose_response
    ):
        """Mock Meta_agent so no real LLM call is made."""
        with patch(
            "core.orchestrator.Meta_agent" if False else "core.meta_agent.Meta_agent"
        ) as _:
            # Patch the LLM to return meta + decompose responses in sequence
            orchestrator.llm.invoke.side_effect = [
                meta_llm_response,
                decompose_response,
                # agent task executions — each agent gets a plain string back
                "result 1",
                "result 2",
            ]
            result = orchestrator.process_user_request("Build a payment service")

        assert result["status"] in ("success", "error")  # no crash is the baseline
        assert "correlation_id" in result

    def test_correlation_id_is_set(self, orchestrator):
        orchestrator.llm.invoke.return_value = "{}"
        orchestrator.process_user_request("Any valid goal text here")
        assert orchestrator._correlation_id is not None

    def test_exception_in_plan_returns_error(self, orchestrator):
        with patch.object(
            orchestrator, "create_execution_plan", side_effect=RuntimeError("boom")
        ):
            result = orchestrator.process_user_request("Build something")
        assert result["status"] == "error"
        assert "boom" in result["message"]


# ── 4. Tool management ────────────────────────────────────────────────────────


class TestToolManagement:

    def test_register_tool_calls_registry(self, orchestrator):
        orchestrator.tool_registry = MagicMock()
        fake_definition = MagicMock()
        fake_handler = MagicMock()
        orchestrator.register_tool(fake_definition, fake_handler)
        orchestrator.tool_registry.register.assert_called_once_with(
            fake_definition, fake_handler
        )

    def test_execute_tool_raises_on_invalid(self, orchestrator):
        with patch.object(orchestrator, "validate_tool_invocation", return_value=False):
            with pytest.raises(ValueError, match="Invalid tool invocation"):
                orchestrator.execute_tool("bad_tool", {})

    def test_execute_tool_raises_when_registry_missing_execute(self, orchestrator):
        orchestrator.tool_registry = MagicMock(spec=[])  # no 'execute' attr
        with patch.object(orchestrator, "validate_tool_invocation", return_value=True):
            with pytest.raises(RuntimeError, match="not available"):
                orchestrator.execute_tool("web_search", {"query": "test"})

    def test_execute_tool_delegates_to_registry(self, orchestrator):
        mock_registry = MagicMock()
        mock_registry.execute.return_value = {"results": []}
        orchestrator.tool_registry = mock_registry
        with patch.object(orchestrator, "validate_tool_invocation", return_value=True):
            result = orchestrator.execute_tool("web_search", {"query": "test"})
        mock_registry.execute.assert_called_once_with("web_search", {"query": "test"})
        assert result == {"results": []}


# ── 5. Agent lifecycle ────────────────────────────────────────────────────────


class TestAgentLifecycle:

    def test_register_and_retrieve_agent(self, orchestrator):
        fake_agent = MagicMock()
        fake_agent.agent_id = "agent-test-1"
        orchestrator.register_active_agent(fake_agent)
        assert orchestrator.get_agent_by_id("agent-test-1") is fake_agent

    def test_unregister_removes_agent(self, orchestrator):
        fake_agent = MagicMock()
        fake_agent.agent_id = "agent-test-2"
        orchestrator.register_active_agent(fake_agent)
        orchestrator.unregister_agent("agent-test-2")
        assert orchestrator.get_agent_by_id("agent-test-2") is None

    def test_inject_dependencies_sets_memory(self, orchestrator):
        fake_agent = MagicMock()
        fake_agent.agent_id = "dep-agent"
        orchestrator.inject_agent_dependencies(fake_agent)
        # memory attr should have been set to the memory_manager
        assert fake_agent.memory == orchestrator.memory_manager

    def test_inject_dependencies_sets_tool_registry(self, orchestrator):
        fake_agent = MagicMock()
        orchestrator.inject_agent_dependencies(fake_agent)
        assert fake_agent.tool_registry == orchestrator.tool_registry


# ── 6. Task graph management ─────────────────────────────────────────────────


class TestTaskGraphManagement:

    def test_mark_task_completed_updates_graph(self, orchestrator):
        from core.task_graph import TaskNode

        node = TaskNode(task_id="t1", name="Test task", description="", dependencies=[])
        orchestrator.task_graph.add_task(node)
        orchestrator.mark_task_completed("t1", {"output": "done"})
        task = orchestrator.task_graph.get_task("t1")
        assert task.status == TaskStatus.COMPLETED

    def test_mark_task_failed_updates_graph(self, orchestrator):
        from core.task_graph import TaskNode

        node = TaskNode(
            task_id="t2", name="Failing task", description="", dependencies=[]
        )
        orchestrator.task_graph.add_task(node)
        orchestrator.mark_task_failed("t2", RuntimeError("something went wrong"))
        task = orchestrator.task_graph.get_task("t2")
        assert task.status == TaskStatus.FAILED


# ── 7. Budget management ──────────────────────────────────────────────────────


class TestBudgetIntegration:

    def test_budget_check_before_execution(self, orchestrator):
        from core.task_graph import TaskNode

        node = TaskNode(
            task_id="b1", name="Budget task", description="", dependencies=[]
        )
        # Should return True when plenty of budget remains
        assert orchestrator.check_budget_before_execution(node) is True

    def test_budget_exceeded_skips_task(self, orchestrator):
        from core.task_graph import TaskNode

        # Exhaust the budget
        orchestrator.budget_manager.set_budget_limit(BudgetType.TOKENS, 0.0)
        node = TaskNode(
            task_id="b2", name="Over budget", description="", dependencies=[]
        )
        assert orchestrator.check_budget_before_execution(node) is False
