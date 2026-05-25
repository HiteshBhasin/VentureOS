from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class SalesStrategistAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "plan_follow_up_strategy":
            return self._plan_follow_up_strategy(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _plan_follow_up_strategy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        sales_cycle_stage = task.get("sales_cycle_stage")
        recipient_role = task.get("recipient_role")
        
        prompt = f"Plan a follow-up strategy for a B2B sales cycle at stage '{sales_cycle_stage}' targeting a recipient with role '{recipient_role}'."
        system_prompt = "You are a sales strategist specializing in B2B sales cycles. Provide a detailed follow-up plan including timing, communication channels, and messaging strategies."
        
        result = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "follow_up_strategy": result}