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

    _DOCKER_IMAGES = {
        "python": "python:3.11-slim",
        "javascript": "node:20-slim",
        "typescript": "node:20-slim",
        "bash": "bash:5",
    }

    _DANGEROUS_PATTERNS = {
        "python": [
            (r"\b__import__\s*\(", "Dynamic import via __import__"),
            (r"\beval\s*\(", "Use of eval()"),
            (r"\bexec\s*\(", "Use of exec()"),
            (r"\bos\.system\s*\(", "Shell command via os.system()"),
            (r"\bsubprocess\b", "Use of subprocess module"),
            (r"\bopen\s*\(", "File system access via open()"),
            (r"\bsocket\b", "Network access via socket"),
            (r"\burllib\b", "Network access via urllib"),
            (r"\brequests\b", "Network access via requests"),
            (r"\bpickle\b", "Unsafe deserialization via pickle"),
            (r"\bshutil\b", "File system operations via shutil"),
            (r"globals\s*\(\s*\)", "Access to globals()"),
            (r"locals\s*\(\s*\)", "Access to locals()"),
        ],
        "javascript": [
            (r"require\s*\(\s*['\"]child_process['\"]", "Use of child_process module"),
            (r"require\s*\(\s*['\"]fs['\"]", "File system access via fs module"),
            (r"\beval\s*\(", "Use of eval()"),
            (r"\bnew\s+Function\s*\(", "Dynamic code via new Function()"),
            (r"\bprocess\.env\b", "Access to process.env"),
            (r"\bprocess\.exit\b", "Process termination"),
        ],
        "bash": [
            (r"\brm\s+-[rRfF]{1,3}\b", "Destructive rm command"),
            (r"\bcurl\b|\bwget\b", "Network access via curl/wget"),
            (r"\bnc\b|\bnetcat\b", "Network access via netcat"),
            (r"\bsudo\b", "Privilege escalation via sudo"),
            (r"\bchmod\b", "Permission modification via chmod"),
        ],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._environments: Dict[Language, ExecutionEnvironment] = {}
        self._execution_history: List[CodeExecutionResult] = []
        self._sandbox_limits: Dict[str, Any] = {}
        self._network_access: bool = True
        self._filesystem_access: Dict[str, Any] = {"paths": [], "readonly": True}
        self._repl_sessions: Dict[str, Any] = {}
        self._sandbox_dir: Optional[str] = None

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
        if self.config.get("sandbox") == "docker":
            return self._execute_in_docker(code, Language.PYTHON, timeout, inputs)

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
        if self.config.get("sandbox") == "docker":
            return self._execute_in_docker(code, Language.JAVASCRIPT, timeout, inputs)

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
            _preexec = self._get_preexec_fn()
            _js_kwargs: Dict[str, Any] = {
                "capture_output": True,
                "text": True,
                "timeout": timeout,
            }
            if _preexec is not None:
                _js_kwargs["preexec_fn"] = _preexec
            try:
                proc = subprocess.run(  # noqa: S603
                    ["node", tmp.name],
                    **_js_kwargs,
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
        if self.config.get("sandbox") == "docker":
            return self._execute_in_docker(script, Language.BASH, timeout)

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
            _preexec = self._get_preexec_fn()
            _bash_kwargs: Dict[str, Any] = {
                "capture_output": True,
                "text": True,
                "timeout": timeout,
            }
            if _preexec is not None:
                _bash_kwargs["preexec_fn"] = _preexec
            try:
                proc = subprocess.run(  # noqa: S603
                    [bash_bin, tmp.name],
                    **_bash_kwargs,
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
            from sqlalchemy import create_engine, text  # noqa: PLC0415, F401 # type: ignore
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

    def _get_preexec_fn(self):
        """Return a preexec_fn that applies POSIX resource limits, or None on Windows."""
        import os

        if os.name != "posix":
            return None
        memory_mb = self._sandbox_limits.get("memory_mb", 0)
        if not memory_mb:
            return None

        def _apply_limits() -> None:
            import resource

            limit_bytes = memory_mb * 1024 * 1024
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            except ValueError:
                pass  # limit exceeds current hard limit; ignore silently

        return _apply_limits

    def _execute_in_docker(
        self,
        code: str,
        language: Language,
        timeout: int,
        inputs: Optional[Dict] = None,
    ) -> CodeExecutionResult:
        """Execute code inside a Docker container with resource and network constraints."""
        import json
        import os
        import tempfile
        import time

        _SUFFIX_CMD: Dict[Language, tuple] = {
            Language.PYTHON: (".py", ["python3", "/sandbox/code.py"]),
            Language.JAVASCRIPT: (".js", ["node", "/sandbox/code.js"]),
            Language.TYPESCRIPT: (".ts", ["npx", "ts-node", "/sandbox/code.ts"]),
            Language.BASH: (".sh", ["bash", "/sandbox/code.sh"]),
        }

        if language not in _SUFFIX_CMD:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Docker execution not supported for {language.value}",
            )

        suffix, cmd = _SUFFIX_CMD[language]
        sandbox_dir = self._sandbox_dir or tempfile.mkdtemp(prefix="ventureos_sandbox_")
        os.makedirs(sandbox_dir, exist_ok=True)

        full_code = (
            f"_inputs = {json.dumps(inputs)}\n{code}"
            if (language == Language.PYTHON and inputs)
            else code
        )
        code_path = os.path.join(sandbox_dir, f"code{suffix}")
        with open(code_path, "w", encoding="utf-8") as fh:
            fh.write(full_code)

        memory_mb = self._sandbox_limits.get("memory_mb", 512)
        cpu_percent = self._sandbox_limits.get("cpu_percent", 100)
        cpu_period = 100_000
        cpu_quota = max(1_000, int(cpu_period * cpu_percent / 100))

        try:
            import docker  # type: ignore
        except ImportError:
            return CodeExecutionResult(
                success=False,
                output="",
                error="docker package not installed; run: pip install docker",
            )

        start = time.perf_counter()
        container = None
        try:
            client = docker.from_env()
            image = self._DOCKER_IMAGES.get(language.value, "python:3.11-slim")
            container = client.containers.run(
                image=image,
                command=cmd,
                volumes={sandbox_dir: {"bind": "/sandbox", "mode": "ro"}},
                mem_limit=f"{memory_mb}m",
                cpu_period=cpu_period,
                cpu_quota=cpu_quota,
                network_disabled=not self._network_access,
                remove=False,
                detach=True,
                stdout=True,
                stderr=True,
            )
            try:
                exit_info = container.wait(timeout=timeout)
            except Exception:
                container.kill()
                container.remove(force=True)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return CodeExecutionResult(
                    success=False,
                    output="",
                    error=f"Execution timed out after {timeout}s",
                    execution_time_ms=elapsed_ms,
                )

            elapsed_ms = (time.perf_counter() - start) * 1000.0
            stdout_out = container.logs(stdout=True, stderr=False).decode(
                "utf-8", errors="replace"
            )
            stderr_out = container.logs(stdout=False, stderr=True).decode(
                "utf-8", errors="replace"
            )
            container.remove()

            if exit_info.get("StatusCode", -1) != 0:
                return CodeExecutionResult(
                    success=False,
                    output=stdout_out,
                    error=stderr_out or f"Process exited with code {exit_info.get('StatusCode')}",
                    execution_time_ms=elapsed_ms,
                )

            result = CodeExecutionResult(
                success=True,
                output=stdout_out,
                error=stderr_out if stderr_out else None,
                execution_time_ms=elapsed_ms,
            )
            self._execution_history.append(result)
            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            return CodeExecutionResult(
                success=False,
                output="",
                error=str(exc),
                execution_time_ms=elapsed_ms,
            )

    # ==================== Environment Management ====================

    def create_environment(
        self, language: Language, config: Dict[str, Any]
    ) -> ExecutionEnvironment:
        """Create execution environment."""
        if language in self._environments:
            return self._environments[language]
        env = ExecutionEnvironment(
            language=language,
            version=config.get("version", "latest"),
            packages=config.get("packages", []),
            environment_vars=config.get("environment_vars", {}),
            working_directory=config.get("working_directory", "/tmp"),
            timeout=config.get("timeout", 30),
            memory_limit_mb=config.get("memory_limit_mb", 512),
        )
        self._environments[language] = env       
        return env

    def destroy_environment(self, language: Language) -> bool:
        """Destroy execution environment."""
        if language in self._environments:
            del self._environments[language]
            return True
        return False

    def get_environment(self, language: Language) -> Optional[ExecutionEnvironment]:
        """Get execution environment."""
        return self._environments.get(language)
        

    def install_package(
        self, language: Language, package: str, version: Optional[str] = None
    ) -> bool:
        """Install package in environment."""
        if language not in self._environments:
            return False
        env = self._environments[language]
        pkg_str = f"{package}=={version}" if version else package
        for i , existing_pkg in enumerate(env.packages):
            if existing_pkg.startswith(package + "==") or existing_pkg == package:
                env.packages[i] = pkg_str
                break
        env.packages.append(pkg_str)
        return True

        

    def install_packages(
        self, language: Language, packages: List[str]
    ) -> Dict[str, bool]:
        """Install multiple packages."""
        results = {}
        for pkg in packages:
            if "==" in pkg:
                package, version = pkg.split("==", 1)
            else:
                package, version = pkg, None
            result = self.install_package(language, package, version)
            results[pkg] = result
        return results
        

    def list_installed_packages(self, language: Language) -> List[str]:
        """List installed packages."""
        if language not in self._environments:
            return []
        return self._environments[language].packages
        

    def set_environment_variable(
        self, language: Language, key: str, value: str
    ) -> None:
        """Set environment variable."""
        if language not in self._environments:
            return
        env = self._environments[language]
        env.environment_vars[key] = value
    

    # ==================== Sandboxing ====================

    def enable_sandbox(self) -> None:
        """Enable sandboxed execution."""
        import tempfile 
        import os
        self._sandbox_dir = tempfile.mkdtemp(prefix="ventureos_sandbox_")
        
        self.set_memory_limit(self.config.get("memory_limit_mb", 512))
        self.set_cpu_limit(self.config.get("cpu_limit_percent", 100))
        
        self.set_network_access(self.config.get("network_access", False))
        
        self.set_filesystem_access(
            paths=self.config.get("filesystem_access_paths", []),
            readonly=self.config.get("filesystem_access_readonly", True),
        )
        

        if os.name == "posix":
            # Check if Docker is available
            try:
                import docker
                client = docker.from_env()
                client.ping()
                self.config["sandbox"] = "docker"
            except Exception:
                self.config["sandbox"] = "process"
        else:
            # Windows (nt) and other platforms fall back to process isolation
            self.config["sandbox"] = "process"

    def disable_sandbox(self) -> None:
        """Disable sandboxed execution."""
        import os
        import shutil

        self.config.pop("sandbox", None)
        if self._sandbox_dir and os.path.isdir(self._sandbox_dir):
            shutil.rmtree(self._sandbox_dir, ignore_errors=True)
        self._sandbox_dir = None

    def set_memory_limit(self, limit_mb: int) -> None:
        """Set memory limit for execution."""
        self._sandbox_limits["memory_mb"] = max(1, limit_mb)

    def set_cpu_limit(self, percent: int) -> None:
        """Set CPU limit for execution."""
        self._sandbox_limits["cpu_percent"] = max(1, min(percent, 100))

    def set_network_access(self, enabled: bool) -> None:
        """Enable/disable network access in sandbox."""
        self._network_access = enabled

    def set_filesystem_access(self, paths: List[str], readonly: bool = True) -> None:
        """Set filesystem access permissions."""
        self._filesystem_access = {"paths": paths, "readonly": readonly}

    # ==================== Validation ====================

    def validate_syntax(self, code: str, language: Language) -> Dict[str, Any]:
        """Validate code syntax."""
        if language == Language.PYTHON:
            try:
                compile(code, "<validate>", "exec")
                return {"valid": True, "errors": []}
            except SyntaxError as e:
                return {
                    "valid": False,
                    "errors": [{"line": e.lineno, "message": e.msg, "text": e.text}],
                }

        if language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            import os
            import shutil
            import subprocess
            import tempfile

            node = shutil.which("node")
            if not node:
                return {"valid": False, "errors": [{"message": "Node.js not found on PATH"}]}
            suffix = ".ts" if language == Language.TYPESCRIPT else ".js"
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, encoding="utf-8"
            )
            try:
                tmp.write(code)
                tmp.flush()
                tmp.close()
                proc = subprocess.run(  # noqa: S603
                    [node, "--check", tmp.name], capture_output=True, text=True
                )
            finally:
                os.unlink(tmp.name)
            if proc.returncode == 0:
                return {"valid": True, "errors": []}
            return {"valid": False, "errors": [{"message": proc.stderr.strip()}]}

        if language == Language.BASH:
            import os
            import shutil
            import subprocess
            import tempfile

            bash = shutil.which("bash")
            if not bash:
                return {"valid": False, "errors": [{"message": "bash not found on PATH"}]}
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".sh", delete=False, encoding="utf-8"
            )
            try:
                tmp.write(code)
                tmp.flush()
                tmp.close()
                proc = subprocess.run(  # noqa: S603
                    [bash, "-n", tmp.name], capture_output=True, text=True
                )
            finally:
                os.unlink(tmp.name)
            if proc.returncode == 0:
                return {"valid": True, "errors": []}
            return {"valid": False, "errors": [{"message": proc.stderr.strip()}]}

        return {
            "valid": True,
            "errors": [],
            "note": f"Syntax validation not supported for {language.value}",
        }

    def analyze_code(self, code: str, language: Language) -> Dict[str, Any]:
        """Analyze code for potential issues."""
        lines = code.splitlines()
        result: Dict[str, Any] = {
            "lines": len(lines),
            "non_empty_lines": sum(1 for ln in lines if ln.strip()),
            "dangerous_patterns": self.detect_dangerous_patterns(code, language),
        }
        if language == Language.PYTHON:
            import ast

            try:
                tree = ast.parse(code)
                result["functions"] = [
                    n.name
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                result["classes"] = [
                    n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
                ]
                imports: List[str] = []
                for n in ast.walk(tree):
                    if isinstance(n, ast.Import):
                        imports.extend(alias.name for alias in n.names)
                    elif isinstance(n, ast.ImportFrom) and n.module:
                        imports.append(n.module)
                result["imports"] = imports
                result["parse_error"] = None
            except SyntaxError as e:
                result["parse_error"] = str(e)
        return result

    def detect_dangerous_patterns(
        self, code: str, language: Language
    ) -> List[Dict[str, Any]]:
        """Detect potentially dangerous code patterns."""
        import re

        patterns = self._DANGEROUS_PATTERNS.get(language.value, [])
        found: List[Dict[str, Any]] = []
        for line_no, line in enumerate(code.splitlines(), start=1):
            for pattern, description in patterns:
                if re.search(pattern, line):
                    found.append(
                        {
                            "line": line_no,
                            "pattern": pattern,
                            "description": description,
                            "text": line.strip(),
                        }
                    )
        return found

    def sanitize_code(self, code: str, language: Language) -> str:
        """Sanitize code by commenting out lines with dangerous patterns."""
        import re

        patterns = self._DANGEROUS_PATTERNS.get(language.value, [])
        if not patterns:
            return code
        comment_prefix = (
            "//" if language in (Language.JAVASCRIPT, Language.TYPESCRIPT) else "#"
        )
        sanitized_lines: List[str] = []
        for line in code.splitlines(keepends=True):
            matched_description: Optional[str] = None
            for pattern, description in patterns:
                if re.search(pattern, line):
                    matched_description = description
                    break
            if matched_description:
                sanitized_lines.append(
                    f"{comment_prefix} [SANITIZED: {matched_description}] {line.rstrip()}\n"
                )
            else:
                sanitized_lines.append(line)
        return "".join(sanitized_lines)

    # ==================== REPL Support ====================

    def start_repl(self, language: Language) -> str:
        """Start a REPL session. Returns session ID."""
        import queue
        import threading
        import uuid

        session_id = str(uuid.uuid4())

        if language == Language.PYTHON:
            import code as _code_module
            import contextlib
            import io

            input_q: queue.Queue = queue.Queue()
            output_q: queue.Queue = queue.Queue()

            def _run_python_repl() -> None:
                console = _code_module.InteractiveConsole()
                while True:
                    cmd = input_q.get()
                    if cmd is None:
                        break
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                        console.push(cmd)
                    output_q.put(buf.getvalue())

            thread = threading.Thread(target=_run_python_repl, daemon=True)
            thread.start()
            self._repl_sessions[session_id] = {
                "language": language,
                "input_queue": input_q,
                "output_queue": output_q,
                "thread": thread,
                "history": [],
            }
        else:
            import shutil
            import subprocess

            _CMD_MAP = {
                Language.JAVASCRIPT: (shutil.which("node"), ["-i"]),
                Language.BASH: (shutil.which("bash"), ["-s"]),
            }
            entry = _CMD_MAP.get(language)
            if entry is None or entry[0] is None:
                return ""

            exe: str = entry[0]  # narrowed: not None after guard above
            flags = entry[1]
            proc = subprocess.Popen(  # noqa: S603
                [exe] + flags,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            out_q: queue.Queue = queue.Queue()

            def _read_output(p: Any, q: queue.Queue) -> None:
                for line in p.stdout:
                    q.put(line)
                q.put(None)  # sentinel when process exits

            reader = threading.Thread(target=_read_output, args=(proc, out_q), daemon=True)
            reader.start()
            self._repl_sessions[session_id] = {
                "language": language,
                "process": proc,
                "output_queue": out_q,
                "reader": reader,
                "history": [],
            }

        return session_id

    def execute_in_repl(self, session_id: str, code: str) -> CodeExecutionResult:
        """Execute code in REPL session."""
        import queue

        if session_id not in self._repl_sessions:
            return CodeExecutionResult(
                success=False, output="", error="Session not found"
            )

        session = self._repl_sessions[session_id]
        language: Language = session["language"]
        session["history"].append(code)

        if language == Language.PYTHON:
            session["input_queue"].put(code)
            try:
                output = session["output_queue"].get(timeout=5.0)
            except queue.Empty:
                output = ""
            return CodeExecutionResult(success=True, output=output)

        proc = session["process"]
        if proc.poll() is not None:
            return CodeExecutionResult(
                success=False, output="", error="REPL process has terminated"
            )
        try:
            proc.stdin.write(code + "\n")
            proc.stdin.flush()
        except OSError as exc:
            return CodeExecutionResult(success=False, output="", error=str(exc))

        output_parts: List[str] = []
        out_q = session["output_queue"]
        while True:
            try:
                line = out_q.get(timeout=0.3)
                if line is None:
                    break
                output_parts.append(line)
            except queue.Empty:
                break

        return CodeExecutionResult(success=True, output="".join(output_parts))

    def get_repl_history(self, session_id: str) -> List[str]:
        """Get REPL command history."""
        if session_id not in self._repl_sessions:
            return []
        return list(self._repl_sessions[session_id]["history"])

    def close_repl(self, session_id: str) -> bool:
        """Close REPL session."""
        if session_id not in self._repl_sessions:
            return False
        session = self._repl_sessions.pop(session_id)
        language: Language = session["language"]
        if language == Language.PYTHON:
            session["input_queue"].put(None)  # signal thread to exit
        else:
            proc = session["process"]
            try:
                proc.stdin.close()
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        return True

    # ==================== Utility ====================

    def get_supported_languages(self) -> List[Language]:
        """Get list of supported languages."""
        return list(Language)

    def get_language_version(self, language: Language) -> str:
        """Get version of language runtime."""
        if language == Language.PYTHON:
            import sys

            return sys.version

        if language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            import shutil
            import subprocess

            node = shutil.which("node")
            if not node:
                return "unknown"
            proc = subprocess.run(  # noqa: S603
                [node, "--version"], capture_output=True, text=True
            )
            return proc.stdout.strip()

        if language == Language.BASH:
            import shutil
            import subprocess

            bash = shutil.which("bash")
            if not bash:
                return "unknown"
            proc = subprocess.run(  # noqa: S603
                [bash, "--version"], capture_output=True, text=True
            )
            return proc.stdout.splitlines()[0] if proc.stdout else "unknown"

        return "unknown"

    def format_code(self, code: str, language: Language) -> str:
        """Format code according to language standards."""
        if language == Language.PYTHON:
            try:
                import black  # type: ignore

                return black.format_str(code, mode=black.Mode())
            except (ImportError, Exception):
                return code

        if language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            import os
            import shutil
            import subprocess
            import tempfile

            prettier = shutil.which("prettier")
            if not prettier:
                return code
            suffix = ".ts" if language == Language.TYPESCRIPT else ".js"
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, encoding="utf-8"
            )
            try:
                tmp.write(code)
                tmp.flush()
                tmp.close()
                result = subprocess.run(  # noqa: S603
                    [prettier, "--write", tmp.name], capture_output=True, text=True
                )
                if result.returncode == 0:
                    with open(tmp.name, "r", encoding="utf-8") as fh:
                        return fh.read()
            finally:
                os.unlink(tmp.name)

        return code

    def get_execution_history(self, limit: int = 100) -> List[CodeExecutionResult]:
        """Get execution history."""
        return self._execution_history[-limit:]

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        history = self._execution_history
        if not history:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "average_time_ms": 0.0,
                "total_time_ms": 0.0,
            }
        successful = sum(1 for r in history if r.success)
        times = [r.execution_time_ms for r in history]
        return {
            "total_executions": len(history),
            "successful": successful,
            "failed": len(history) - successful,
            "average_time_ms": sum(times) / len(times),
            "total_time_ms": sum(times),
        }
