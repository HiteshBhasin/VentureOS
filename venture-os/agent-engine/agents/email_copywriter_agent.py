from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class EmailCopywriterAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "generate_email_copy":
            return self._generate_email_copy(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _generate_email_copy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        recipient_role = task.get("recipient_role")
        industry = task.get("industry")
        product_description = task.get("product_description")
        
        if not all([recipient_role, industry, product_description]):
            return {"status": "error", "error": "Missing required parameters"}
        
        prompt = f"Craft a compelling cold outreach email tailored to a {recipient_role} in the {industry} industry. The product is: {product_description}."
        system_prompt = "You are a professional email copywriter specializing in cold outreach. Your goal is to create engaging and personalized emails that capture the recipient's attention and encourage a response."
        
        email_copy = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "email_copy": email_copy}