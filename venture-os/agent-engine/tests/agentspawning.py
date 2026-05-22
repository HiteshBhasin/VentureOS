import sys
import os

# Allow imports from the agent-engine root regardless of where this script is run from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from core.llm_class import LLM
    from core.agent_factory import AgentFactory
    from agents.coding_agent import CodingAgent
    from agents.research_agent import ResearchAgent
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you have the correct directory structure and that all dependencies are installed.")
    sys.exit(1)

llm = LLM(model="mistral-large-latest", temperature=0.4)
factory = AgentFactory(llm=llm)
factory.register_agent_type("coding",   CodingAgent)
factory.register_agent_type("research", ResearchAgent)


print("\n" + "="*55)
print("Generating: SalesOutreachAgent  (use Mistral to write it)")
print("="*55)

agent = factory.spawn_dynamic_agent(
    use_case="Draft personalised cold-outreach emails for B2B SaaS sales, "
             "score lead quality, and suggest follow-up timing.",
    agent_name="sales_outreach",
    capabilities=[
        "draft_cold_email(lead_info)",
        "score_lead_quality(lead_info)",
        "suggest_followup_timing(lead_info)",
    ],
)

print(f"\nSpawned: {type(agent).__name__}  id={agent.agent_id}  status={agent.status}")

# Quick smoke-test: ask the new agent to do something
print("\n--- Running draft_cold_email task on new agent ---")
result = agent.execute_task({
    "type": "draft_cold_email",
    "lead_info": "Company: Acme Corp, role: VP Engineering, pain: slow CI/CD pipelines",
})

print(f"status : {result.get('status')}")
output = result.get('email') or result.get('result') or result.get('output') or str(result)
print(f"output : {output[:400]}")

print("\n" + "="*55)
print("Generating: InvestorAnalysisAgent")
print("="*55)

agent2 = factory.spawn_dynamic_agent(
    use_case="Analyse startup pitch decks and financial metrics to produce "
             "investment memos and risk assessments.",
    agent_name="investor_analysis",
    capabilities=[
        "analyse_pitch_deck(text)",
        "assess_market_size(description)",
        "generate_investment_memo(data)",
        "identify_risks(data)",
    ],
)

print(f"\nSpawned: {type(agent2).__name__}  id={agent2.agent_id}  status={agent2.status}")

result2 = agent2.execute_task({
    "type": "assess_market_size",
    "description": "AI-powered legal document review for SMEs in the US",
})

print(f"status : {result2.get('status')}")
output2 = result2.get('market_size') or result2.get('result') or result2.get('output') or str(result2)
print(f"output : {output2[:400]}")

print("\nAll active agents:", list(factory.get_all_agents().keys()))