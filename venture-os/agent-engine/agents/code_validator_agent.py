from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class CodeValidatorAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "validate_python_syntax":
            return self._validate_python_syntax(task.get("code"))
        elif task_type == "debug_code":
            return self._debug_code(task.get("code"), task.get("error_logs"))
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _validate_python_syntax(self, code: str) -> Dict[str, Any]:
        prompt = f"Validate the following Python code for syntax errors:\n{code}"
        system_prompt = "You are a Python syntax validator. Check the code for syntax errors and return a report."
        result = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": result}

    def _debug_code(self, code: str, error_logs: str) -> Dict[str, Any]:
        prompt = f"Debug the following Python code with the provided error logs:\nCode:\n{code}\nError Logs:\n{error_logs}"
        system_prompt = "You are a Python debugger. Analyze the code and error logs to identify and fix issues. Return a detailed debugging report."
        result = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": result}