# Safe code execution
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Language(Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    SQL = "sql"


@dataclass
class ExecutionEnvironment:
    """Execution environment configuration."""

    language: Language
    version: str
    packages: List[str]
    environment_vars: Dict[str, str]
    working_directory: str
    timeout: int = 30
    memory_limit_mb: int = 512


@dataclass
class CodeExecutionResult:
    """Result of code execution."""

    success: bool
    output: str
    error: Optional[str] = None
    return_value: Any = None
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0


class CodeExecutor:
    """Safe code execution in sandboxed environment."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._environments: Dict[Language, ExecutionEnvironment] = {}
        self._execution_history: List[CodeExecutionResult] = []

    # ==================== Execution ====================

    def execute(
        self,
        code: str,
        language: Language,
        inputs: Optional[Dict] = None,
        timeout: int = 30,
    ) -> CodeExecutionResult:
        """Execute code in specified language."""
        if language not in Language:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Unsupported language: {language}",
            )
        if language == Language.PYTHON:
            return self.execute_python(code, inputs, timeout)
        elif language == Language.JAVASCRIPT:
            return self.execute_javascript(code, inputs, timeout)
        elif language == Language.BASH:
            return self.execute_bash(code, timeout)
        elif language == Language.SQL:
            connection_string = self.config.get("sql_connection_string", "")
            return self.execute_sql(code, connection_string)
        else:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Execution for language {language} not implemented",
            )

    def execute_python(
        self, code: str, inputs: Optional[Dict] = None, timeout: int = 30
    ) -> CodeExecutionResult:
        """Execute Python code safely in a restricted sandboxed environment."""
        import io
        import time
        import traceback
        import contextlib
        import threading

        inputs = inputs or {}

        # Allowlist of safe builtins — excludes __import__, open, eval, exec, compile, etc.
        _safe_builtin_names = [
            "abs",
            "all",
            "any",
            "bin",
            "bool",
            "bytes",
            "callable",
            "chr",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "hasattr",
            "hash",
            "hex",
            "id",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "object",
            "oct",
            "ord",
            "pow",
            "print",
            "property",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "setattr",
            "slice",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "vars",
            "zip",
            "True",
            "False",
            "None",
            "Exception",
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "AttributeError",
            "RuntimeError",
            "StopIteration",
            "NotImplementedError",
            "OverflowError",
            "ZeroDivisionError",
        ]
        import builtins as _builtins_module

        safe_builtins = {
            name: getattr(_builtins_module, name)
            for name in _safe_builtin_names
            if hasattr(_builtins_module, name)
        }

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        exec_globals: Dict[str, Any] = {
            "__builtins__": safe_builtins,
            "__name__": "__main__",
        }
        exec_locals: Dict[str, Any] = dict(inputs)
        container: Dict[str, Any] = {"return_value": None, "error": None, "tb": None}

        def _run() -> None:
            try:
                compiled = compile(code, "<ventureos_exec>", "exec")
                with contextlib.redirect_stdout(
                    stdout_capture
                ), contextlib.redirect_stderr(stderr_capture):
                    exec(compiled, exec_globals, exec_locals)  # noqa: S102
                container["return_value"] = exec_locals.get("result")
            except Exception as exc:
                container["error"] = exc
                container["tb"] = traceback.format_exc()

        start = time.perf_counter()
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if thread.is_alive():
            return CodeExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"Execution timed out after {timeout}s",
                execution_time_ms=elapsed_ms,
            )

        if container["error"] is not None:
            return CodeExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=container["tb"] or str(container["error"]),
                execution_time_ms=elapsed_ms,
            )

        err_output = stderr_capture.getvalue()
        execution_result = CodeExecutionResult(
            success=True,
            output=stdout_capture.getvalue(),
            error=err_output if err_output else None,
            return_value=container["return_value"],
            execution_time_ms=elapsed_ms,
        )
        self._execution_history.append(execution_result)
        return execution_result

    def execute_javascript(
        self, code: str, inputs: Optional[Dict] = None, timeout: int = 30
    ) -> CodeExecutionResult:
        """Execute JavaScript code via Node.js subprocess."""
        import json
        import subprocess
        import tempfile
        import time
        import os

        inputs = inputs or {}

        # Inject inputs as a JSON-parsed variable and wrap user code
        inputs_json = json.dumps(inputs)
        wrapped_code = (
            f"const inputs = {inputs_json};\n"
            "const _originalLog = console.log;\n"
            "const _output = [];\n"
            "console.log = (...args) => _output.push(args.map(String).join(' '));\n"
            f"{code}\n"
            "process.stdout.write(_output.join('\\n'));\n"
        )

        # Write to a temp file so Node gets a real script path
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        )
        try:
            tmp.write(wrapped_code)
            tmp.flush()
            tmp.close()

            start = time.perf_counter()
            try:
                proc = subprocess.run(  # noqa: S603
                    ["node", tmp.name],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except FileNotFoundError:
                return CodeExecutionResult(
                    success=False,
                    output="",
                    error="Node.js is not installed or not on PATH",
                )
            except subprocess.TimeoutExpired:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return CodeExecutionResult(
                    success=False,
                    output="",
                    error=f"Execution timed out after {timeout}s",
                    execution_time_ms=elapsed_ms,
                )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        finally:
            os.unlink(tmp.name)

        if proc.returncode != 0:
            return CodeExecutionResult(
                success=False,
                output=proc.stdout,
                error=proc.stderr,
                execution_time_ms=elapsed_ms,
            )

        execution_result = CodeExecutionResult(
            success=True,
            output=proc.stdout,
            error=proc.stderr if proc.stderr else None,
            execution_time_ms=elapsed_ms,
        )
        self._execution_history.append(execution_result)
        return execution_result

    def execute_bash(self, script: str, timeout: int = 30) -> CodeExecutionResult:
        """Execute Bash script via subprocess."""
        import subprocess
        import tempfile
        import time
        import os
        import shutil

        bash_bin = shutil.which("bash")
        if bash_bin is None:
            return CodeExecutionResult(
                success=False,
                output="",
                error="bash is not installed or not on PATH",
            )

        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, encoding="utf-8"
        )
        try:
            tmp.write(script)
            tmp.flush()
            tmp.close()
            os.chmod(tmp.name, 0o700)

            start = time.perf_counter()
            try:
                proc = subprocess.run(  # noqa: S603
                    [bash_bin, tmp.name],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return CodeExecutionResult(
                    success=False,
                    output="",
                    error=f"Execution timed out after {timeout}s",
                    execution_time_ms=elapsed_ms,
                )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        finally:
            os.unlink(tmp.name)

        if proc.returncode != 0:
            return CodeExecutionResult(
                success=False,
                output=proc.stdout,
                error=proc.stderr,
                execution_time_ms=elapsed_ms,
            )

        execution_result = CodeExecutionResult(
            success=True,
            output=proc.stdout,
            error=proc.stderr if proc.stderr else None,
            execution_time_ms=elapsed_ms,
        )
        self._execution_history.append(execution_result)
        return execution_result

    def execute_sql(self, query: str, connection_string: str) -> CodeExecutionResult:
        """Execute SQL query via SQLAlchemy (supports PostgreSQL, MySQL, SQLite, etc.)."""
        import time

        if not connection_string:
            return CodeExecutionResult(
                success=False,
                output="",
                error="connection_string is required",
            )

        try:
            from sqlalchemy import create_engine, text  # noqa: PLC0415
        except ImportError:
            return CodeExecutionResult(
                success=False,
                output="",
                error="sqlalchemy is not installed; run: pip install sqlalchemy",
            )

        try:
            engine = create_engine(connection_string)
            start = time.perf_counter()
            with engine.connect() as conn:
                result_proxy = conn.execute(text(query))
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                try:
                    rows = result_proxy.fetchall()
                    columns = list(result_proxy.keys())
                    return_value = [dict(zip(columns, row)) for row in rows]
                    output = "\n".join(str(dict(zip(columns, row))) for row in rows)
                except Exception:
                    # DML/DDL statements (INSERT, UPDATE, CREATE, …) return no rows
                    conn.commit()
                    return_value = None
                    output = f"Query executed successfully. Rows affected: {result_proxy.rowcount}"
        except Exception as exc:
            elapsed_ms = (
                (time.perf_counter() - start) * 1000.0 if "start" in dir() else 0.0
            )
            return CodeExecutionResult(
                success=False,
                output="",
                error=str(exc),
                execution_time_ms=elapsed_ms,
            )

        execution_result = CodeExecutionResult(
            success=True,
            output=output,
            return_value=return_value,
            execution_time_ms=elapsed_ms,
        )
        self._execution_history.append(execution_result)
        return execution_result

    def execute_file(
        self, filepath: str, language: Language, args: Optional[List[str]] = None
    ) -> CodeExecutionResult:
        """Execute code from file."""
        with open(filepath, "r") as f:
            code = f.read()
        return self.execute(code, language, inputs={"args": args or []})

    # ==================== Environment Management ====================

    def create_environment(
        self, language: Language, config: Dict[str, Any]
    ) -> ExecutionEnvironment:
        """Create execution environment."""
        pass

    def destroy_environment(self, language: Language) -> bool:
        """Destroy execution environment."""
        pass

    def get_environment(self, language: Language) -> Optional[ExecutionEnvironment]:
        """Get execution environment."""
        pass

    def install_package(
        self, language: Language, package: str, version: Optional[str] = None
    ) -> bool:
        """Install package in environment."""
        pass

    def install_packages(
        self, language: Language, packages: List[str]
    ) -> Dict[str, bool]:
        """Install multiple packages."""
        pass

    def list_installed_packages(self, language: Language) -> List[str]:
        """List installed packages."""
        pass

    def set_environment_variable(
        self, language: Language, key: str, value: str
    ) -> None:
        """Set environment variable."""
        pass

    # ==================== Sandboxing ====================

    def enable_sandbox(self) -> None:
        """Enable sandboxed execution."""
        pass

    def disable_sandbox(self) -> None:
        """Disable sandboxed execution."""
        pass

    def set_memory_limit(self, limit_mb: int) -> None:
        """Set memory limit for execution."""
        pass

    def set_cpu_limit(self, percent: int) -> None:
        """Set CPU limit for execution."""
        pass

    def set_network_access(self, enabled: bool) -> None:
        """Enable/disable network access in sandbox."""
        pass

    def set_filesystem_access(self, paths: List[str], readonly: bool = True) -> None:
        """Set filesystem access permissions."""
        pass

    # ==================== Validation ====================

    def validate_syntax(self, code: str, language: Language) -> Dict[str, Any]:
        """Validate code syntax."""
        pass

    def analyze_code(self, code: str, language: Language) -> Dict[str, Any]:
        """Analyze code for potential issues."""
        pass

    def detect_dangerous_patterns(
        self, code: str, language: Language
    ) -> List[Dict[str, Any]]:
        """Detect potentially dangerous code patterns."""
        pass

    def sanitize_code(self, code: str, language: Language) -> str:
        """Sanitize code by removing dangerous patterns."""
        pass

    # ==================== REPL Support ====================

    def start_repl(self, language: Language) -> str:
        """Start a REPL session. Returns session ID."""
        pass

    def execute_in_repl(self, session_id: str, code: str) -> CodeExecutionResult:
        """Execute code in REPL session."""
        pass

    def get_repl_history(self, session_id: str) -> List[str]:
        """Get REPL command history."""
        pass

    def close_repl(self, session_id: str) -> bool:
        """Close REPL session."""
        pass

    # ==================== Utility ====================

    def get_supported_languages(self) -> List[Language]:
        """Get list of supported languages."""
        pass

    def get_language_version(self, language: Language) -> str:
        """Get version of language runtime."""
        pass

    def format_code(self, code: str, language: Language) -> str:
        """Format code according to language standards."""
        pass

    def get_execution_history(self, limit: int = 100) -> List[CodeExecutionResult]:
        """Get execution history."""
        pass

    def clear_history(self) -> None:
        """Clear execution history."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        pass
