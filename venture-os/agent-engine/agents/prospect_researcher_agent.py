from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class ProspectResearcherAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "research_prospect":
            return self._research_prospect(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _research_prospect(self, task: Dict[str, Any]) -> Dict[str, Any]:
        company_name = task.get("company_name")
        target_role = task.get("target_role")
        
        if not company_name or not target_role:
            return {"status": "error", "error": "Missing required parameters: company_name and target_role"}
        
        prompt = f"Gather and analyze information about {company_name} and the role of {target_role} to inform personalized outreach."
        system_prompt = "You are a prospect researcher. Provide detailed insights about the company, the target role, and any relevant information that could be used for personalized outreach."
        
        result = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": result}