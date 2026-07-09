# Tests for AgentFactory's dynamic-agent dedup, reuse, and cleanup behavior
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from core import agent_factory
from core.agent_factory import AgentFactory, cleanup_stale_spawned_agents, _capability_key


def _agent_code(class_name: str) -> str:
    return (
        "from agents.base_agent import BaseAgent\n\n"
        f"class {class_name}(BaseAgent):\n"
        "    def execute_task(self, task):\n"
        "        return {'status': 'success', 'type': task.get('type')}\n"
    )


def _fake_generate_agent(task):
    """Stands in for CodingAgent.execute_task({'type': 'generate_agent', ...}) —
    writes a minimal valid agent to save_path instead of calling a real LLM."""
    class_name = (
        "".join(w.capitalize() for w in task["agent_name"].split("_")) + "Agent"
    )
    code = _agent_code(class_name)
    with open(task["save_path"], "w", encoding="utf-8") as f:
        f.write(code)
    return {"status": "success", "code": code}


@pytest.fixture
def spawned_dir(tmp_path, monkeypatch):
    d = tmp_path / "spawned_agents"
    d.mkdir()
    monkeypatch.setattr(agent_factory, "_SPAWNED_AGENTS_DIR", str(d))
    return d


class TestCapabilityKey:
    def test_order_and_case_insensitive(self):
        assert _capability_key(["Send_Email", "draft_copy"]) == _capability_key(
            ["draft_copy", "send_email"]
        )

    def test_none_without_capabilities(self):
        assert _capability_key(None) is None
        assert _capability_key([]) is None
        assert _capability_key(["  "]) is None

    def test_distinct_for_different_capabilities(self):
        assert _capability_key(["draft_email"]) != _capability_key(["review_code"])


class TestSpawnDynamicAgentDedup:
    def test_reuses_generated_file_across_different_agent_names(self, spawned_dir):
        factory = AgentFactory(llm=MagicMock())
        capabilities = ["draft_email"]

        with patch(
            "agents.coding_agent.CodingAgent.execute_task",
            side_effect=_fake_generate_agent,
        ) as mocked:
            agent1 = factory.spawn_dynamic_agent(
                use_case="draft cold emails",
                agent_name="email_writer",
                capabilities=capabilities,
            )
            assert mocked.call_count == 1

            agent2 = factory.spawn_dynamic_agent(
                use_case="write outreach emails",  # different wording, same skill
                agent_name="outreach_drafter",
                capabilities=capabilities,
            )
            # Same capability fingerprint — must reuse, not regenerate
            assert mocked.call_count == 1

        assert agent1 is not agent2  # distinct instances...
        # ...loaded from the same generated class (each spawn re-execs the module,
        # so the class objects themselves differ even when the file is reused)
        assert type(agent1).__name__ == type(agent2).__name__ == "EmailWriterAgent"

        py_files = [f for f in os.listdir(spawned_dir) if f.endswith(".py")]
        assert len(py_files) == 1

    def test_distinct_capabilities_produce_distinct_files(self, spawned_dir):
        factory = AgentFactory(llm=MagicMock())

        with patch(
            "agents.coding_agent.CodingAgent.execute_task",
            side_effect=_fake_generate_agent,
        ) as mocked:
            factory.spawn_dynamic_agent(
                use_case="draft emails", agent_name="email_writer", capabilities=["draft_email"]
            )
            factory.spawn_dynamic_agent(
                use_case="review code", agent_name="code_reviewer", capabilities=["review_code"]
            )
            assert mocked.call_count == 2

        py_files = [f for f in os.listdir(spawned_dir) if f.endswith(".py")]
        assert len(py_files) == 2

    def test_registry_persists_to_disk(self, spawned_dir):
        factory = AgentFactory(llm=MagicMock())
        with patch(
            "agents.coding_agent.CodingAgent.execute_task",
            side_effect=_fake_generate_agent,
        ):
            factory.spawn_dynamic_agent(
                use_case="draft emails", agent_name="email_writer", capabilities=["draft_email"]
            )
        assert os.path.exists(os.path.join(spawned_dir, "_registry.json"))

    def test_no_capabilities_falls_back_to_name_based_reuse(self, spawned_dir):
        """Without capabilities there's no fingerprint to key on — same agent_name
        should still reuse its own file (pre-existing behavior), just not be
        shared across different names."""
        factory = AgentFactory(llm=MagicMock())
        with patch(
            "agents.coding_agent.CodingAgent.execute_task",
            side_effect=_fake_generate_agent,
        ) as mocked:
            factory.spawn_dynamic_agent(use_case="x", agent_name="solo_agent", capabilities=None)
            factory.spawn_dynamic_agent(use_case="x", agent_name="solo_agent", capabilities=None)
            assert mocked.call_count == 1  # reused by name on the second call


class TestCleanupStaleSpawnedAgents:
    def test_removes_files_older_than_ttl(self, spawned_dir):
        old_file = spawned_dir / "old_agent.py"
        old_file.write_text(_agent_code("OldAgent"), encoding="utf-8")
        old_time = time.time() - 40 * 86400  # 40 days ago
        os.utime(old_file, (old_time, old_time))

        removed = cleanup_stale_spawned_agents(ttl_days=30)

        assert removed == 1
        assert not old_file.exists()

    def test_keeps_recently_touched_files(self, spawned_dir):
        fresh_file = spawned_dir / "fresh_agent.py"
        fresh_file.write_text(_agent_code("FreshAgent"), encoding="utf-8")

        removed = cleanup_stale_spawned_agents(ttl_days=30)

        assert removed == 0
        assert fresh_file.exists()

    def test_no_directory_is_a_noop(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            agent_factory, "_SPAWNED_AGENTS_DIR", str(tmp_path / "does_not_exist")
        )
        assert cleanup_stale_spawned_agents(ttl_days=30) == 0

    def test_reuse_bumps_mtime_so_janitor_spares_it(self, spawned_dir):
        factory = AgentFactory(llm=MagicMock())
        capabilities = ["draft_email"]

        with patch(
            "agents.coding_agent.CodingAgent.execute_task",
            side_effect=_fake_generate_agent,
        ):
            factory.spawn_dynamic_agent(
                use_case="draft emails", agent_name="email_writer", capabilities=capabilities
            )

        # Simulate the file having aged out, then being reused before cleanup runs
        generated = next(f for f in spawned_dir.iterdir() if f.suffix == ".py")
        old_time = time.time() - 40 * 86400
        os.utime(generated, (old_time, old_time))

        with patch(
            "agents.coding_agent.CodingAgent.execute_task",
            side_effect=_fake_generate_agent,
        ) as mocked:
            factory.spawn_dynamic_agent(
                use_case="draft outreach emails",
                agent_name="outreach_drafter",
                capabilities=capabilities,
            )
            assert mocked.call_count == 0  # reused via registry, mtime bumped

        assert cleanup_stale_spawned_agents(ttl_days=30) == 0
        assert generated.exists()
