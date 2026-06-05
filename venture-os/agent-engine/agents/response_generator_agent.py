from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class ResponseGeneratorAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "generate_name_response":
            return self._generate_name_response(task.get("intent"), task.get("context", {}))
        elif task_type == "ensure_tone_compliance":
            return self._ensure_tone_compliance(task.get("response_text"))
        else:
            return {"status": "error", "error": f"Unknown task type: {task.get('type')}"}

    def _generate_name_response(self, intent: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Generate a professional and friendly response to the user's inquiry about the assistant's name.
        User intent: {intent}
        Context: {context}
        """
        system_prompt = """
        You are a helpful AI assistant. Your task is to generate a warm, professional, and concise response
        when a user asks about your name or identity. Keep the tone friendly and approachable while maintaining
        professionalism. Do not reveal any personal or sensitive information.
        """
        try:
            response = self._invoke_llm(prompt, system_prompt)
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _ensure_tone_compliance(self, response_text: str) -> Dict[str, Any]:
        prompt = f"""
        Review the following response for tone compliance:
        Response: {response_text}

        Ensure the response is professional, friendly, and appropriate for a user interacting with an AI assistant.
        If the tone is not compliant, rewrite it to meet these standards.
        """
        system_prompt = """
        You are a tone compliance reviewer for an AI assistant. Your task is to ensure all responses are:
        - Professional: Clear, respectful, and free of slang or overly casual language.
        - Friendly: Warm, approachable, and helpful.
        - Appropriate: Free of any offensive, discriminatory, or sensitive content.

        If the provided response does not meet these standards, rewrite it to comply.
        """
        try:
            compliant_response = self._invoke_llm(prompt, system_prompt)
            return {"status": "success", "compliant_response": compliant_response}
        except Exception as e:
            return {"status": "error", "error": str(e)}