# Code generation agent
import re
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent
from tools.code_executor import CodeExecutor


class CodingAgent(BaseAgent):
    """Agent specialized for code generation, debugging, and refactoring."""

    def __init__(
        self,
        agent_id: str,
        llm,
        memory=None,
        tools: Optional[List] = None,
        config: Optional[Dict] = None,
    ):
        super().__init__(agent_id, llm, memory, tools, config)
        self.supported_languages: List[str] = []
        self.code_context: Dict[str, Any] = {}

    # ==================== Core Execution ====================

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a coding task (generation, debugging, refactoring)."""
        task_type = task.get("type")
        if task_type == "generate_code":

            result = self.generate_code(
                specification=task.get("specification", ""),
                language=task.get("language", "python"),
            )
            execution = CodeExecutor().execute(
                code=result, language=task.get("language", "python")
            )
            return {"status": "success", "type": "generate_code", "code": execution}
        elif task_type == "generate_function":
            result = self.generate_function(
                name=task.get("name", "generated_function"),
                description=task.get("description", ""),
                language=task.get("language", "python"),
            )
            return {
                "status": "success",
                "type": "generate_function",
                "code": CodeExecutor().execute(
                    code=result, language=task.get("language", "python")
                ),
            }
        elif task_type == "generate_tests":
            result = self.generate_tests(
                code=task.get("code", ""),
                framework=task.get("framework", "pytest"),
            )
            return {
                "status": "success",
                "type": "generate_tests",
                "code": CodeExecutor().execute(
                    code=result, language=task.get("language", "python")
                ),
            }
        elif task_type == "generate_documentation":
            result = self.generate_documentation(
                code=task.get("code", ""),
                style=task.get("style", "docstring"),
            )
            return {
                "status": "success",
                "type": "generate_documentation",
                "code": CodeExecutor().execute(
                    code=result, language=task.get("language", "python")
                ),
            }
        elif task_type == "debug_code":
            return self.debug_error(
                code=task.get("code", ""),
                error_message=task.get("error_message", ""),
            )
        elif task_type == "refactor_code":
            result = self.refactor_code(
                code=task.get("code", ""),
                refactor_type=task.get("refactor_type", "optimize"),
            )
            return {
                "status": "success",
                "type": "refactor_code",
                "code": CodeExecutor().execute(
                    code=result, language=task.get("language", "python")
                ),
            }
        elif task_type == "generate_agent":
            return self._generate_agent_task(
                use_case=task.get("use_case", ""),
                agent_name=task.get("agent_name", "custom"),
                capabilities=task.get("capabilities", []),
                save_path=task.get("save_path"),
            )
        else:
            return {"error": f"Unsupported task type: {task_type}"}

    # ==================== Agent Generation ====================

    def _generate_agent_task(
        self,
        use_case: str,
        agent_name: str,
        capabilities: List[str],
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a new agent class file for a given use case."""
        import os

        # Normalise class/file names
        class_name = (
            "".join(w.capitalize() for w in re.split(r"[\s_-]+", agent_name)) + "Agent"
        )
        file_name = re.sub(r"[^\w]+", "_", agent_name.lower()).strip("_") + "_agent.py"

        caps_text = (
            "\n".join(f"  - {c}" for c in capabilities)
            if capabilities
            else "  - general purpose task execution"
        )

        prompt = f"""Write a complete Python agent class for this use case:

        Use case: {use_case}

        Capabilities required:
        {caps_text}

        Rules you MUST follow:
        1. Class must be named `{class_name}` and inherit from `BaseAgent`.
        2. Start the file with: `from typing import Any, Dict, List, Optional`\n`from .base_agent import BaseAgent`
        3. Implement `execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]`.
        4. In `execute_task`, route using `task.get("type")` — NOT "action" or anything else.
        5. Each capability listed above becomes both a routing key in `execute_task` and a private method.
        6. Each private method must call `self._invoke_llm(prompt, system_prompt)` to do its work.
        7. On an unknown type, return `{{"status": "error", "error": f"Unknown task type: {{task.get('type')}}"}}`.
        8. Return ONLY raw Python code — no markdown fences, no explanation."""

        system_prompt = (
            "You are an expert Python engineer writing AI agent classes. "
            "Output only valid Python code. No markdown, no prose."
        )

        raw = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

        # Strip accidental markdown code fences
        code = re.sub(r"^```[\w]*\n?", "", raw.strip(), flags=re.MULTILINE)
        code = re.sub(r"```$", "", code.strip())

        # Determine save path (default: agents/ next to this file)
        if not save_path:
            agents_dir = os.path.dirname(os.path.abspath(__file__))
            save_path = os.path.join(agents_dir, file_name)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(code)

        return {
            "status": "success",
            "type": "generate_agent",
            "class_name": class_name,
            "file_path": save_path,
            "code": code,
        }

    # ==================== Code Generation ====================

    def generate_code(self, specification: str, language: str) -> str:
        """Generate code from a specification."""
        prompt = f"Generate {language} code for the following specification:\n{specification}"
        system_prompt = f"You are an expert {language} developer. Return only the code, no explanations."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def generate_function(self, name: str, description: str, language: str) -> str:
        """Generate a single function based on description."""
        prompt = (
            f"Generate one {language} function named '{name}' with this behavior:\n"
            f"{description}"
        )
        system_prompt = (
            f"You are an expert {language} developer. "
            "Return only the function code, no explanations."
        )
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def generate_tests(self, code: str, framework: str = "pytest") -> str:
        """Generate unit tests for given code."""
        prompt = (
            f"Generate comprehensive unit tests using {framework} for the code below:\n"
            f"{code}"
        )
        system_prompt = (
            "You are an expert test engineer. Return only test code with meaningful "
            "test cases and no explanation text."
        )
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def generate_documentation(self, code: str, style: str = "docstring") -> str:
        """Generate documentation for code."""
        prompt = (
            f"Generate {style} documentation for the following code. "
            "Preserve behavior and signatures:\n"
            f"{code}"
        )
        system_prompt = (
            "You are an expert technical writer for software projects. "
            "Return only documentation content, no explanations."
        )
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    # ==================== Code Analysis ====================

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code for structure, complexity, and patterns."""
        prompt = (
            "Analyze the following code for structure, potential patterns, risks, and "
            "maintainability concerns:\n"
            f"{code}"
        )
        system_prompt = (
            "You are a senior software architect. Provide concise technical analysis."
        )
        analysis = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"summary": analysis, "issues": [], "patterns": []}

    def find_bugs(self, code: str) -> List[Dict[str, Any]]:
        """Identify potential bugs in code."""
        prompt = (
            "Find likely bugs or failure points in this code. "
            "Focus on logic errors, edge cases, and unsafe assumptions:\n"
            f"{code}"
        )
        system_prompt = (
            "You are an expert debugger. Return concise findings in plain text."
        )
        findings = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not findings:
            return []
        return [{"severity": "medium", "description": findings}]

    def suggest_improvements(self, code: str) -> List[Dict[str, Any]]:
        """Suggest code improvements and optimizations."""
        prompt = (
            "Suggest concrete improvements for readability, maintainability, and "
            "performance for this code:\n"
            f"{code}"
        )
        system_prompt = (
            "You are a senior code reviewer. Return concise improvement suggestions."
        )
        suggestions = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not suggestions:
            return []
        return [{"category": "general", "suggestion": suggestions}]

    def check_code_style(
        self, code: str, style_guide: str = "pep8"
    ) -> List[Dict[str, Any]]:
        """Check code against style guidelines."""
        prompt = (
            f"Review the following code against {style_guide} style guidelines and list "
            "violations:\n"
            f"{code}"
        )
        system_prompt = (
            "You are a strict linter assistant. Return concise style findings only."
        )
        findings = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not findings:
            return []
        return [{"style_guide": style_guide, "finding": findings}]

    def estimate_complexity(self, code: str) -> Dict[str, Any]:
        """Estimate cyclomatic and cognitive complexity."""
        prompt = (
            "Estimate cyclomatic and cognitive complexity for this code and explain key "
            "drivers:\n"
            f"{code}"
        )
        system_prompt = "You are a software quality analyst."
        assessment = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {
            "cyclomatic": "unknown",
            "cognitive": "unknown",
            "assessment": assessment,
        }

    # ==================== Debugging ====================

    def debug_error(self, code: str, error_message: str) -> Dict[str, Any]:
        """Analyze and suggest fix for an error."""
        explanation = self.explain_error(error_message=error_message, stack_trace="")
        suggested_fix = self.suggest_fix(
            code=code,
            error={"message": error_message, "explanation": explanation},
        )
        return {
            "status": "success",
            "error_message": error_message,
            "explanation": explanation,
            "suggested_fix": suggested_fix,
        }

    def explain_error(self, error_message: str, stack_trace: str) -> str:
        """Explain an error in plain language."""
        prompt = (
            "Explain this programming error in plain language and mention likely root "
            f"causes.\nError: {error_message}\nStack trace:\n{stack_trace}"
        )
        system_prompt = "You are a debugging assistant for developers."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def suggest_fix(self, code: str, error: Dict[str, Any]) -> str:
        """Suggest a fix for identified bug."""
        prompt = (
            "Given the code and error details, provide a corrected code snippet. "
            "Return only code.\n"
            f"Error details: {error}\n"
            f"Code:\n{code}"
        )
        system_prompt = "You are an expert software engineer focused on bug fixing."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def trace_execution(
        self, code: str, inputs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Trace execution flow with given inputs."""
        prompt = (
            "Simulate a step-by-step execution trace for this code with the provided "
            f"inputs.\nInputs: {inputs}\nCode:\n{code}"
        )
        system_prompt = "You are a program tracing assistant."
        trace = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not trace:
            return []
        return [{"step": 1, "trace": trace}]

    # ==================== Refactoring ====================

    def refactor_code(self, code: str, refactor_type: str) -> str:
        """Refactor code based on specified type."""
        prompt = (
            f"Refactor this code with focus on: {refactor_type}. Return only refactored "
            f"code.\n{code}"
        )
        system_prompt = "You are an expert refactoring assistant."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def extract_function(self, code: str, selection: str, function_name: str) -> str:
        """Extract selected code into a new function."""
        prompt = (
            f"Extract the selected snippet into a function named {function_name}. Return "
            f"only updated code.\nSelected snippet:\n{selection}\nFull code:\n{code}"
        )
        system_prompt = "You are an expert code transformation assistant."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def rename_symbol(self, code: str, old_name: str, new_name: str) -> str:
        """Rename a symbol throughout code."""
        return code.replace(old_name, new_name)

    def optimize_code(self, code: str, optimization_goal: str) -> str:
        """Optimize code for specified goal (speed, memory, readability)."""
        prompt = (
            f"Optimize this code for {optimization_goal}. Return only optimized code.\n"
            f"{code}"
        )
        system_prompt = "You are a performance-focused software engineer."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    def convert_syntax(self, code: str, from_version: str, to_version: str) -> str:
        """Convert code between language versions."""
        prompt = (
            f"Convert this code syntax from {from_version} to {to_version}. "
            f"Return only converted code.\n{code}"
        )
        system_prompt = "You are an expert in language version migrations."
        return self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

    # ==================== Code Execution ====================

    def execute_code(
        self, code: str, language: str, inputs: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute code in sandboxed environment."""
        return {
            "status": "not_executed",
            "language": language,
            "inputs": inputs or {},
            "output": "",
            "error": "Sandbox execution is not configured for this agent.",
            "code": code,
        }

    def validate_syntax(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code syntax."""
        prompt = (
            f"Validate the syntax of this {language} code and report whether it is valid. "
            "If invalid, include likely syntax errors.\n"
            f"{code}"
        )
        system_prompt = "You are a static syntax validation assistant."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {
            "is_valid": bool(result),
            "language": language,
            "details": result,
        }

    # ==================== Context Management ====================

    def set_project_context(self, project_info: Dict[str, Any]) -> None:
        """Set project context for code generation."""
        self.code_context["project_info"] = project_info
        languages = project_info.get("supported_languages")
        if isinstance(languages, list):
            self.supported_languages = [str(lang) for lang in languages]

    def add_code_reference(self, name: str, code: str) -> None:
        """Add code reference for context."""
        self.code_context[name] = code

    def get_relevant_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant code context for task."""
        task_type = task.get("type")
        return {
            "task_type": task_type,
            "supported_languages": self.supported_languages,
            "context": self.code_context,
        }

    def clear_code_context(self) -> None:
        """Clear all code context."""
        self.code_context.clear()
