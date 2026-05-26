# Tools tests
<<<<<<< HEAD
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from core.orchestrator import Orchestrator
    from core.llm_class import LLM
except:
    print("Failed to import Orchestrator. Current sys.path:", sys.path)

llm = LLM(model="mistral-large-latest", temperature=0.4)

orchestrator = Orchestrator(llm)

# Option 1 — full pipeline (recommended)
result = orchestrator.process_user_request("Build a payment API")

print("Final result:", json.dumps(result, indent=2))
# Option 2 — spawn a specific agent manually
# from core.task_graph import TaskNode  # ← only needed for manual spawning

# task = TaskNode(
#     task_id="t1",
#     name="write payment code",
#     description="Implement Stripe integration",
#     dependencies=[],
#     metadata={"agent_type": "coding"},
# )
# agent = orchestrator.spawn_and_configure_agent(task)
# agent.execute_task({"type": "generate_code", "specification": "Stripe integration", "language": "python"})
=======
import sys
import os

# Allow imports from the agent-engine root regardless of where this script is run from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from core.llm_class import LLM
    from core.orchestrator import Orchestrator
    # from core.agent_factory import AgentFactory
    # from agents.coding_agent import CodingAgent
    # from agents.research_agent import ResearchAgent
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you have the correct directory structure and that all dependencies are installed.")
    sys.exit(1)
    
llm = LLM(model="command-a-03-2025", temperature=0.4)
orchestrator = Orchestrator(llm=llm)
result = orchestrator.process_user_request(
    "Draft a cold outreach email for Acme Corp's VP of Engineering about our CI/CD automation tool, "
    "and suggest a follow-up timing based on typical B2B sales cycles.")

print("\n" + "=" * 70)
print(f"Status      : {result.get('status')}")
print(f"Correlation : {result.get('correlation_id')}")
print(f"Goal        : {result.get('goal', '')[:80]}")

agents_spawned = result.get("agents_spawned", [])
print(f"Agents spawned ({len(agents_spawned)}): {agents_spawned}")

# ── Per-agent work ───────────────────────────────────────────────────────
print("\n" + "-" * 70)
print("SPECIALIST AGENT OUTPUTS")
print("-" * 70)
agent_results = result.get("agent_results", {})
for agent_name, agent_data in agent_results.items():
    if agent_data.get("status") == "error":
        print(f"\n[{agent_name}] ERROR: {agent_data.get('error')}")
        continue
    print(f"\n[{agent_name}]  class={agent_data.get('agent_class')}  status={agent_data.get('status')}")
    for i, tr in enumerate(agent_data.get("task_results", []), 1):
        task_type = tr.get("task", {}).get("type", "?")
        res = tr.get("result") or {}
        output = (
            res.get("output")
            or res.get("result")
            or res.get("report")
            or res.get("code")
            or str(res)
        )
        print(f"  Task {i} [{task_type}]:")
        print(f"    {str(output)[:600]}")

# ── Final CEO report ─────────────────────────────────────────────────────
report = result.get("report", "")
if report:
    print("\n" + "=" * 70)
    print("FINAL REPORT (CEO / Meta-Agent)")
    print("=" * 70)
    print(report)

print("=" * 70)
>>>>>>> 99e2fd0a2d849f5db8e49d8f7637651f72924b01
