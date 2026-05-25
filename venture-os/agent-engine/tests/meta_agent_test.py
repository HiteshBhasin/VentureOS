import sys
import os
import logging

# Allow imports from the agent-engine root regardless of where this script is run from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s  %(name)s  %(message)s",
)

from core.llm_class import LLM
from core.agent_factory import AgentFactory
from core.meta_agent import Meta_agent
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent

# ─── Setup ────────────────────────────────────────────────────────────────────

llm = LLM(model="mistral-large-latest", temperature=0.4)

factory = AgentFactory(llm=llm)
factory.register_agent_type("coding",   CodingAgent)
factory.register_agent_type("research", ResearchAgent)

meta = Meta_agent(llm=llm, factory=factory)

# ─── Run ──────────────────────────────────────────────────────────────────────

GOAL = (
    "Build a go-to-market strategy for a B2B SaaS startup that automates "
    "legal contract review for small law firms."
)

print("\n" + "=" * 65)
print(f"GOAL: {GOAL}")
print("=" * 65 + "\n")

output = meta.run(GOAL)

# ─── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 65)
print("ANALYSIS")
print("=" * 65)
analysis = output["analysis"]
print(f"  Primary goal : {analysis.get('primary_goal')}")
print(f"  Domain       : {analysis.get('domain')}")
print(f"  Complexity   : {analysis.get('complexity_level')}")
print(f"  Capabilities : {analysis.get('required_capabilities')}")

print("\n" + "=" * 65)
print(f"AGENTS SPAWNED  ({len(output['agents_spawned'])})")
print("=" * 65)
for aid in output["agents_spawned"]:
    print(f"  {aid}")

print("\n" + "=" * 65)
print("TASK RESULTS")
print("=" * 65)
for agent_name, info in output["results"].items():
    if info.get("status") == "error":
        print(f"\n[{agent_name}]  ERROR: {info['error']}")
        continue
    print(f"\n[{agent_name}]  class={info['agent_class']}  status={info['status']}")
    for i, tr in enumerate(info.get("task_results", []), 1):
        task_type = tr["task"].get("type", "?")
        result = tr["result"]
        status = result.get("status", "?")
        # grab the most meaningful output key
        output_text = (
            result.get("output")
            or result.get("result")
            or result.get("email")
            or result.get("analysis")
            or result.get("research")
            or str(result)
        )
        print(f"  Task {i}: {task_type}  → {status}")
        print(f"    {str(output_text)[:300]}")

print("\n" + "=" * 65)
print("Active agents via get_active_agents():")
for aid, cls in meta.get_active_agents().items():
    print(f"  {cls}  ({aid})")
print("=" * 65 + "\n")
