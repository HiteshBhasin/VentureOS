from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class ContextAnalyzerAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "extract_name_from_context":
            context_data = task.get("context_data", {})
            return self._extract_name_from_context(context_data)
        elif task_type == "validate_name_candidate":
            name_candidate = task.get("name_candidate", "")
            return self._validate_name_candidate(name_candidate)
        else:
            return {"status": "error", "error": f"Unknown task type: {task.get('type')}"}

    def _extract_name_from_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Extract the user's name from the following conversation context or metadata.
        Do not make assumptions or guesses. If the name is not explicitly mentioned, return None.
        Context: {context_data}
        """
        system_prompt = """
        You are an expert at analyzing conversation context to extract user names.
        Only return a name if it is explicitly mentioned in the provided data.
        """
        response = self._invoke_llm(prompt, system_prompt)
        name = response.strip() if response else None
        return {"status": "success", "name": name}

    def _validate_name_candidate(self, name_candidate: str) -> Dict[str, Any]:
        prompt = f"""
        Validate whether the following name candidate is a plausible human name.
        Consider common naming conventions but do not make assumptions about gender, culture, or ethnicity.
        Return True if it is a plausible name, False otherwise.
        Name candidate: {name_candidate}
        """
        system_prompt = """
        You are an expert at validating human names.
        Only return True if the name candidate is a plausible human name based on common conventions.
        """
        response = self._invoke_llm(prompt, system_prompt)
        is_valid = response.strip().lower() == "true"
        return {"status": "success", "is_valid": is_valid}