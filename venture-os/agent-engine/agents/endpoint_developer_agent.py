from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class EndpointDeveloperAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "create_endpoint":
            return self._create_endpoint(task)
        elif task_type == "define_route":
            return self._define_route(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _create_endpoint(self, task: Dict[str, Any]) -> Dict[str, Any]:
        path = task.get("path")
        response = task.get("response")
        prompt = f"Create an endpoint at path '{path}' that returns the following JSON response: {response}"
        system_prompt = "You are a Flask endpoint developer. Write Python code to create the specified endpoint."
        try:
            self._invoke_llm(prompt, system_prompt)
            return {"status": "success", "message": f"Endpoint created at {path}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _define_route(self, task: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = task.get("endpoint")
        method = task.get("method")
        prompt = f"Define a route for endpoint '{endpoint}' using the '{method}' HTTP method."
        system_prompt = "You are a Flask route developer. Write Python code to define the specified route."
        try:
            self._invoke_llm(prompt, system_prompt)
            return {"status": "success", "message": f"Route defined for {endpoint} with method {method}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}