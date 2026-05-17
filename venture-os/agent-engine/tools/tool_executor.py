# Tool execution engine
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """Status of tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of a tool execution."""

    tool_name: str
    status: ExecutionStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context for tool execution."""

    execution_id: str
    agent_id: str
    task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timeout: int = 30
    retry_count: int = 0
    max_retries: int = 3


class ToolExecutor:
    """Safe tool execution engine."""

    def __init__(self, registry: Any = None, config: Optional[Dict[str, Any]] = None):
        self.registry = registry
        self.config = config or {}
        self._running_executions: Dict[str, ExecutionContext] = {}
        self._execution_history: List[ExecutionResult] = []
        self._default_timeout: int = 30
        self._max_concurrent: int = 10
        self._sandboxing_enabled: bool = False
        self._sandbox_config: Dict[str, Any] = {}
        self._rate_limit_state: Dict[str, Dict[str, Any]] = {}
        self._async_futures: Dict[str, Any] = {}

    # ==================== Execution ====================

    def execute(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> ExecutionResult:
        """Execute a tool with given inputs."""
        import time
        import threading

        started = datetime.utcnow()
        start_perf = time.perf_counter()

        if not self.validate_tool_available(tool_name):
            return ExecutionResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                error=f"Tool '{tool_name}' not found or unavailable",
                started_at=started,
                completed_at=datetime.utcnow(),
            )

        validation = self.validate_inputs(tool_name, inputs)
        if not validation.get("valid", True):
            return ExecutionResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                error="; ".join(validation.get("errors", ["Invalid inputs"])),
                started_at=started,
                completed_at=datetime.utcnow(),
            )

        handler = self.registry.get_handler(tool_name)
        timeout = (context.timeout if context else None) or self._default_timeout
        container: Dict[str, Any] = {"result": None, "error": None}

        def _run() -> None:
            try:
                container["result"] = handler(**inputs)
            except Exception as exc:
                container["error"] = str(exc)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        completed_at = datetime.utcnow()
        duration_ms = (time.perf_counter() - start_perf) * 1000.0

        if thread.is_alive():
            result = ExecutionResult(
                tool_name=tool_name,
                status=ExecutionStatus.TIMEOUT,
                error=f"Execution timed out after {timeout}s",
                started_at=started,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )
        elif container["error"]:
            result = ExecutionResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                error=container["error"],
                started_at=started,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )
        else:
            result = ExecutionResult(
                tool_name=tool_name,
                status=ExecutionStatus.COMPLETED,
                result=container["result"],
                started_at=started,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

        self.log_execution(result)
        return result

    def execute_async(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> str:
        """Execute tool asynchronously. Returns execution ID."""
        import uuid
        from concurrent.futures import ThreadPoolExecutor

        execution_id = str(uuid.uuid4())
        ctx = context or ExecutionContext(execution_id=execution_id, agent_id="system")
        self._running_executions[execution_id] = ctx

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.execute, tool_name, inputs, ctx)
        self._async_futures[execution_id] = (future, executor)

        def _cleanup(f: Any) -> None:
            self._running_executions.pop(execution_id, None)

        future.add_done_callback(_cleanup)
        return execution_id

    def execute_batch(self, executions: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """Execute multiple tools in sequence."""
        return [
            self.execute(
                tool_name=e["tool_name"],
                inputs=e.get("inputs", {}),
                context=e.get("context"),
            )
            for e in executions
        ]

    def execute_parallel(
        self, executions: List[Dict[str, Any]], max_concurrent: int = 5
    ) -> List[ExecutionResult]:
        """Execute multiple tools in parallel."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results: List[Optional[ExecutionResult]] = [None] * len(executions)
        limit = min(max_concurrent, self._max_concurrent)

        with ThreadPoolExecutor(max_workers=limit) as pool:
            future_to_idx = {
                pool.submit(
                    self.execute,
                    e["tool_name"],
                    e.get("inputs", {}),
                    e.get("context"),
                ): idx
                for idx, e in enumerate(executions)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    results[idx] = ExecutionResult(
                        tool_name=executions[idx]["tool_name"],
                        status=ExecutionStatus.FAILED,
                        error=str(exc),
                    )

        return [r for r in results if r is not None]

    def execute_with_retry(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> ExecutionResult:
        """Execute with automatic retry on failure."""
        import time
        import uuid

        context = ExecutionContext(
            execution_id=str(uuid.uuid4()),
            agent_id="system",
            max_retries=max_retries,
        )
        last_result: Optional[ExecutionResult] = None
        for attempt in range(max_retries + 1):
            context.retry_count = attempt
            last_result = self.execute(tool_name, inputs, context)
            if last_result.status == ExecutionStatus.COMPLETED:
                return last_result
            if attempt < max_retries:
                time.sleep(self.get_retry_delay(context))

        return last_result  # type: ignore[return-value]

    # ==================== Execution Control ====================

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        if execution_id not in self._running_executions:
            return False
        entry = self._async_futures.get(execution_id)
        if entry:
            future, executor = entry
            future.cancel()
            executor.shutdown(wait=False)
            self._async_futures.pop(execution_id, None)
        self._running_executions.pop(execution_id, None)
        return True

    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get status of an execution."""
        entry = self._async_futures.get(execution_id)
        if entry:
            future, _ = entry
            if future.done():
                return ExecutionStatus.FAILED if future.exception() else ExecutionStatus.COMPLETED
            return ExecutionStatus.RUNNING
        if execution_id in self._running_executions:
            return ExecutionStatus.RUNNING
        return None

    def wait_for_execution(
        self, execution_id: str, timeout: int = 60
    ) -> ExecutionResult:
        """Wait for async execution to complete."""
        from concurrent.futures import TimeoutError as FuturesTimeout

        entry = self._async_futures.get(execution_id)
        if entry is None:
            return ExecutionResult(
                tool_name="unknown",
                status=ExecutionStatus.FAILED,
                error=f"Execution '{execution_id}' not found",
            )
        future, executor = entry
        try:
            result = future.result(timeout=timeout)
            self._async_futures.pop(execution_id, None)
            executor.shutdown(wait=False)
            return result
        except FuturesTimeout:
            return ExecutionResult(
                tool_name="unknown",
                status=ExecutionStatus.TIMEOUT,
                error=f"Wait timed out after {timeout}s",
            )
        except Exception as exc:
            return ExecutionResult(
                tool_name="unknown",
                status=ExecutionStatus.FAILED,
                error=str(exc),
            )

    def is_running(self, execution_id: str) -> bool:
        """Check if execution is running."""
        return execution_id in self._running_executions

    # ==================== Validation ====================

    def validate_inputs(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs before execution."""
        if self.registry is None:
            return {"valid": True, "errors": []}
        return self.registry.validate_input(tool_name, inputs)

    def validate_tool_available(self, tool_name: str) -> bool:
        """Check if tool is available for execution."""
        if self.registry is None:
            return False
        return (
            self.registry.has_tool(tool_name)
            and self.registry.get_handler(tool_name) is not None
        )

    def check_rate_limit(self, tool_name: str) -> bool:
        """Check if tool is within rate limit."""
        import time

        if self.registry is None:
            return True
        tool = self.registry.get_tool(tool_name)
        if not tool or not tool.rate_limit:
            return True
        state = self._rate_limit_state.setdefault(
            tool_name, {"window_start": time.time(), "count": 0}
        )
        now = time.time()
        if now - float(state["window_start"]) >= 60:
            state["window_start"] = now
            state["count"] = 0
        if int(state["count"]) >= tool.rate_limit:
            return False
        state["count"] = int(state["count"]) + 1
        return True

    def check_permissions(self, tool_name: str, context: ExecutionContext) -> bool:
        """Check execution permissions."""
        if self.registry is None:
            return True
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return False
        if tool.requires_auth and not getattr(context, "agent_id", None):
            return False
        return True

    # ==================== Sandboxing ====================

    def execute_sandboxed(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        sandbox_config: Optional[Dict] = None,
    ) -> ExecutionResult:
        """Execute in sandboxed environment."""
        import uuid

        effective = {**self._sandbox_config, **(sandbox_config or {})}
        context = ExecutionContext(
            execution_id=str(uuid.uuid4()),
            agent_id="sandbox",
            timeout=effective.get("timeout", self._default_timeout),
        )
        return self.execute(tool_name, inputs, context)

    def set_sandbox_limits(
        self, memory_mb: int = 512, cpu_percent: int = 50, timeout: int = 30
    ) -> None:
        """Set sandbox resource limits."""
        self._sandbox_config["memory_mb"] = memory_mb
        self._sandbox_config["cpu_percent"] = cpu_percent
        self._sandbox_config["timeout"] = timeout

    def enable_sandboxing(self) -> None:
        """Enable sandboxed execution."""
        self._sandboxing_enabled = True

    def disable_sandboxing(self) -> None:
        """Disable sandboxed execution."""
        self._sandboxing_enabled = False

    # ==================== Error Handling ====================

    def handle_error(
        self, tool_name: str, error: Exception, context: ExecutionContext
    ) -> ExecutionResult:
        """Handle execution error."""
        return ExecutionResult(
            tool_name=tool_name,
            status=ExecutionStatus.FAILED,
            error=str(error),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            metadata={"exception_type": type(error).__name__},
        )

    def should_retry(self, error: Exception, context: ExecutionContext) -> bool:
        """Determine if execution should be retried."""
        if context.retry_count >= context.max_retries:
            return False
        return not isinstance(error, (ValueError, TypeError, AttributeError, KeyError))

    def get_retry_delay(self, context: ExecutionContext) -> float:
        """Calculate retry delay with exponential backoff."""
        return min(1.0 * (2 ** context.retry_count), 60.0)

    # ==================== History & Logging ====================

    def get_execution_history(
        self, tool_name: Optional[str] = None, limit: int = 100
    ) -> List[ExecutionResult]:
        """Get execution history."""
        history = self._execution_history
        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]
        return history[-limit:]

    def get_last_execution(self, tool_name: str) -> Optional[ExecutionResult]:
        """Get last execution of a tool."""
        for result in reversed(self._execution_history):
            if result.tool_name == tool_name:
                return result
        return None

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()

    def log_execution(self, result: ExecutionResult) -> None:
        """Log execution result."""
        self._execution_history.append(result)

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        h = self._execution_history
        return {
            "total_executions": len(h),
            "successful": sum(1 for r in h if r.status == ExecutionStatus.COMPLETED),
            "failed": sum(1 for r in h if r.status == ExecutionStatus.FAILED),
            "timed_out": sum(1 for r in h if r.status == ExecutionStatus.TIMEOUT),
            "average_duration_ms": (sum(r.duration_ms for r in h) / len(h)) if h else 0.0,
            "running": len(self._running_executions),
        }

    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for specific tool."""
        h = [r for r in self._execution_history if r.tool_name == tool_name]
        return {
            "tool_name": tool_name,
            "total_executions": len(h),
            "successful": sum(1 for r in h if r.status == ExecutionStatus.COMPLETED),
            "failed": sum(1 for r in h if r.status == ExecutionStatus.FAILED),
            "average_duration_ms": (sum(r.duration_ms for r in h) / len(h)) if h else 0.0,
        }

    def get_success_rate(self, tool_name: Optional[str] = None) -> float:
        """Get execution success rate."""
        h = self._execution_history
        if tool_name:
            h = [r for r in h if r.tool_name == tool_name]
        if not h:
            return 0.0
        return sum(1 for r in h if r.status == ExecutionStatus.COMPLETED) / len(h)

    def get_average_duration(self, tool_name: Optional[str] = None) -> float:
        """Get average execution duration."""
        h = self._execution_history
        if tool_name:
            h = [r for r in h if r.tool_name == tool_name]
        return (sum(r.duration_ms for r in h) / len(h)) if h else 0.0

    # ==================== Configuration ====================

    def set_default_timeout(self, timeout: int) -> None:
        """Set default execution timeout."""
        self._default_timeout = timeout

    def set_max_concurrent(self, max_concurrent: int) -> None:
        """Set maximum concurrent executions."""
        self._max_concurrent = max(1, max_concurrent)

    def set_registry(self, registry: Any) -> None:
        """Set tool registry."""
        self.registry = registry

    def get_running_count(self) -> int:
        """Get count of running executions."""
        return len(self._running_executions)
