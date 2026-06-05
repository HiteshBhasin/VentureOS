from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class PrivacyEnforcerAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "filter_pii":
            return self._filter_pii(task)
        elif task_type == "validate_response_safety":
            return self._validate_response_safety(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task.get('type')}"}

    def _filter_pii(self, task: Dict[str, Any]) -> Dict[str, Any]:
        response_text = task.get("response_text", "")
        prompt = f"""
        Analyze the following text and remove any personal or identifiable information while maintaining professionalism.
        Return only the sanitized text with no additional commentary.

        Text:
        {response_text}
        """
        system_prompt = "You are a privacy enforcement assistant. Your task is to ensure no personal or identifiable information is present in responses."
        try:
            sanitized_text = self._invoke_llm(prompt, system_prompt)
            return {"status": "success", "sanitized_text": sanitized_text.strip()}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _validate_response_safety(self, task: Dict[str, Any]) -> Dict[str, Any]:
        response_text = task.get("response_text", "")
        prompt = f"""
        Analyze the following text for any personal or identifiable information.
        Return a JSON object with two keys:
        - "is_safe": boolean indicating if the text is safe (true) or contains PII (false)
        - "issues": list of strings describing any issues found (empty if none)

        Text:
        {response_text}
        """
        system_prompt = "You are a privacy validation assistant. Your task is to detect personal or identifiable information in responses."
        try:
            validation_result = self._invoke_llm(prompt, system_prompt)
            return {"status": "success", "validation_result": validation_result.strip()}
        except Exception as e:
            return {"status": "error", "error": str(e)}