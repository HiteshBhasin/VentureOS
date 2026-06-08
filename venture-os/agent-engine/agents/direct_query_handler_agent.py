from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class DirectQueryHandlerAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "request_name_directly":
            return self._request_name_directly(task.get("prompt_context", ""))
        elif task_type == "handle_name_response":
            return self._handle_name_response(task.get("response_data", {}))
        else:
            return {"status": "error", "error": f"Unknown task type: {task.get('type')}"}

    def _request_name_directly(self, prompt_context: str) -> Dict[str, Any]:
        prompt = f"""
        You are a polite assistant. The current context is: {prompt_context}.
        Politely ask the user for their name. Keep it concise and friendly.
        """
        system_prompt = "You are a helpful assistant that asks for the user's name in a polite manner."
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "response": response}

    def _handle_name_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        The user provided the following response regarding their name: {response_data}.
        Determine if the name is clear and valid. If it is, confirm it. If not, politely ask for clarification.
        """
        system_prompt = "You are a helpful assistant that processes user-provided names and ensures clarity."
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "response": response}