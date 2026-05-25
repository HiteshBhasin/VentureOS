from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


class CicdExpertAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "generate_value_proposition":
            return self._generate_value_proposition(task)
        else:
            return {
                "status": "error",
                "error": f"Unknown task type: {task_type}",
            }

    def _generate_value_proposition(self, task: Dict[str, Any]) -> Dict[str, Any]:
        product_features = task.get("product_features", [])
        recipient_needs = task.get("recipient_needs", [])

        prompt = f"Generate a value proposition for CI/CD tools based on the following product features: {', '.join(product_features)}. Tailor the proposition to address these recipient needs: {', '.join(recipient_needs)}."
        system_prompt = "You are a CI/CD expert. Provide a concise and compelling value proposition that highlights how the CI/CD tool can meet the specified needs using the given features."

        value_proposition = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "value_proposition": value_proposition}