from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class TestEngineerAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "write_pytest_test":
            return self._write_pytest_test(task)
        elif task_type == "validate_test_coverage":
            return self._validate_test_coverage(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _write_pytest_test(self, task: Dict[str, Any]) -> Dict[str, Any]:
        function_name = task.get("function_name")
        test_cases = task.get("test_cases")
        prompt = f"Write pytest unit tests for the function '{function_name}' with the following test cases: {test_cases}"
        system_prompt = "You are a test engineer. Write pytest tests to verify function correctness."
        test_code = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "test_code": test_code}

    def _validate_test_coverage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        test_code = task.get("test_code")
        function_code = task.get("function_code")
        prompt = f"Validate the test coverage of the following test code:\n{test_code}\nFor the function:\n{function_code}"
        system_prompt = "You are a test engineer. Analyze the test coverage and identify any missing test cases."
        coverage_report = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "coverage_report": coverage_report}