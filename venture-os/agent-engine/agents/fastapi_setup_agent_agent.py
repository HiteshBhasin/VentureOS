from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class FastapiSetupAgentAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "setup_fastapi_environment":
            return self._setup_fastapi_environment(task.get("project_name"))
        elif task_type == "configure_dependencies":
            return self._configure_dependencies(task.get("requirements"))
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    def _setup_fastapi_environment(self, project_name: str) -> Dict[str, Any]:
        prompt = f"Set up a new FastAPI project named '{project_name}'."
        system_prompt = "You are a Python developer setting up a FastAPI project. Ensure the project structure is created and necessary files are initialized."
        result = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": result}

    def _configure_dependencies(self, requirements: List[str]) -> Dict[str, Any]:
        prompt = f"Configure dependencies for a FastAPI project with the following requirements: {', '.join(requirements)}."
        system_prompt = "You are a Python developer configuring dependencies for a FastAPI project. Ensure all required packages are installed and configured correctly."
        result = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": result}