# Tools tests
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
