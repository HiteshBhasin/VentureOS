from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class CodeReviewerAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "review_code":
            return self._review_code(task.get("code"), task.get("constraints"))
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _review_code(self, code: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = "You are a code reviewer. Review the provided code for correctness, style, and adherence to constraints. Provide feedback and suggestions for improvement."
        prompt = f"Code to review:\n{code}\n\nConstraints:\n{constraints}"
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "review": response}