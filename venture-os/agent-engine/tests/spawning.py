import os, sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from core.orchestrator import Orchestrator
from core.llm_class import LLM
from dotenv import load_dotenv




load_dotenv()
LLM_MODEL = "mistral-large-latest"

if LLM_MODEL:
    llm = LLM(model=LLM_MODEL)
    
print(llm.model)
print(llm.__dict__)    
orchestrator = Orchestrator(llm=llm)

print("="*25)
print(orchestrator)
print("="*25)

input = "what is your name?"

result = orchestrator.process_user_request(input)
print("="*25)
print(result)
print("="*25)


print("="*25)
print(orchestrator._active_agents.get)
print("="*25)