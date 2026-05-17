# Performance tracking and token usage metrics
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MetricType(Enum):
    """Types of metrics tracked."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostRecord:
    """Cost record for tracking expenses."""

    amount: float = 0.0
    currency: str = "USD"
    source: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TaskMetric:
    """Metrics for a single task execution."""

    task_id: str = ""
    agent_id: str = ""
    duration_seconds: float = 0.0
    token_usage: Optional[TokenUsage] = None
    cost: float = 0.0
    success: bool = False
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """Collects and aggregates metrics."""

    def __init__(self):
        self._token_usage: List[TokenUsage] = []
        self._costs: List[CostRecord] = []
        self._task_metrics: List[TaskMetric] = []
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}

    # ==================== Token Tracking ====================

    def record_token_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> TokenUsage:
        """Record token usage for an LLM call.

        Args:
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
            model: Model name.

        Returns:
            TokenUsage record.
        """
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
        )
        self._token_usage.append(usage)
        return usage

    def get_total_tokens(self) -> int:
        """Get total tokens used across all calls."""
        return sum(u.total_tokens for u in self._token_usage)

    def get_token_usage_by_model(self) -> Dict[str, int]:
        """Get token usage breakdown by model."""
        result: Dict[str, int] = {}
        for u in self._token_usage:
            result[u.model] = result.get(u.model, 0) + u.total_tokens
        return result

    # ==================== Cost Tracking ====================

    def record_cost(
        self,
        amount: float,
        source: str,
        description: str = "",
    ) -> CostRecord:
        """Record a cost.

        Args:
            amount: Cost amount.
            source: Source of the cost (e.g., "openai", "anthropic").
            description: Optional description.

        Returns:
            CostRecord.
        """
        record = CostRecord(amount=amount, source=source, description=description)
        self._costs.append(record)
        return record

    def get_total_cost(self) -> float:
        """Get total cost incurred."""
        return round(sum(c.amount for c in self._costs), 6)

    def get_cost_by_source(self) -> Dict[str, float]:
        """Get cost breakdown by source."""
        result: Dict[str, float] = {}
        for c in self._costs:
            result[c.source] = round(result.get(c.source, 0.0) + c.amount, 6)
        return result

    # ==================== Task Metrics ====================

    def record_task_metric(self, metric: TaskMetric) -> None:
        """Record metrics for a task execution.

        Args:
            metric: Task metric to record.
        """
        self._task_metrics.append(metric)

    def get_task_metrics(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[TaskMetric]:
        """Get task metrics, optionally filtered by agent.

        Args:
            agent_id: Optional agent ID to filter by.
            limit: Maximum number of records.

        Returns:
            List of task metrics.
        """
        metrics = self._task_metrics
        if agent_id:
            metrics = [m for m in metrics if m.agent_id == agent_id]
        return metrics[-limit:]

    def get_success_rate(self, agent_id: Optional[str] = None) -> float:
        """Get task success rate.

        Args:
            agent_id: Optional agent ID to filter by.

        Returns:
            Success rate as a float between 0 and 1.
        """
        metrics = self.get_task_metrics(agent_id=agent_id, limit=len(self._task_metrics))
        if not metrics:
            return 0.0
        return sum(1 for m in metrics if m.success) / len(metrics)

    def get_avg_task_duration(self, agent_id: Optional[str] = None) -> float:
        """Get average task duration in seconds.

        Args:
            agent_id: Optional agent ID to filter by.

        Returns:
            Average duration in seconds.
        """
        metrics = self.get_task_metrics(agent_id=agent_id, limit=len(self._task_metrics))
        if not metrics:
            return 0.0
        return sum(m.duration_seconds for m in metrics) / len(metrics)

    # ==================== Generic Counters & Gauges ====================

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name.
            value: Value to increment by.
        """
        self._counters[name] = self._counters.get(name, 0) + value

    def get_counter(self, name: str) -> int:
        """Get counter value.

        Args:
            name: Counter name.

        Returns:
            Counter value.
        """
        return self._counters.get(name, 0)

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric.

        Args:
            name: Gauge name.
            value: Gauge value.
        """
        self._gauges[name] = value

    def get_gauge(self, name: str) -> float:
        """Get gauge value.

        Args:
            name: Gauge name.

        Returns:
            Gauge value.
        """
        return self._gauges.get(name, 0.0)

    # ==================== Reporting ====================

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics.

        Returns:
            Dictionary with metric summaries.
        """
        return {
            "total_tokens": self.get_total_tokens(),
            "tokens_by_model": self.get_token_usage_by_model(),
            "total_cost_usd": self.get_total_cost(),
            "cost_by_source": self.get_cost_by_source(),
            "total_tasks": len(self._task_metrics),
            "success_rate": self.get_success_rate(),
            "avg_task_duration_s": self.get_avg_task_duration(),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._token_usage.clear()
        self._costs.clear()
        self._task_metrics.clear()
        self._counters.clear()
        self._gauges.clear()

    def export(self, format: str = "json") -> str:
        """Export metrics in specified format.

        Args:
            format: Export format (json, prometheus, etc.).

        Returns:
            Formatted metrics string.
        """
        summary = self.get_summary()
        if format == "prometheus":
            lines = []
            lines.append(f'agent_total_tokens {{}} {summary["total_tokens"]}')
            lines.append(f'agent_total_cost_usd {{}} {summary["total_cost_usd"]}')
            lines.append(f'agent_total_tasks {{}} {summary["total_tasks"]}')
            lines.append(f'agent_success_rate {{}} {summary["success_rate"]}')
            lines.append(f'agent_avg_duration_seconds {{}} {summary["avg_task_duration_s"]}')
            for name, val in summary["counters"].items():
                safe = name.replace(".", "_").replace("-", "_")
                lines.append(f'agent_counter_{safe} {{}} {val}')
            for name, val in summary["gauges"].items():
                safe = name.replace(".", "_").replace("-", "_")
                lines.append(f'agent_gauge_{safe} {{}} {val}')
            return "\n".join(lines)
        return json.dumps(summary, indent=2, default=str)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_llm_call(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
    cost: Optional[float] = None,
) -> None:
    """Convenience function to record an LLM call.

    Args:
        prompt_tokens: Number of prompt tokens.
        completion_tokens: Number of completion tokens.
        model: Model name.
        cost: Optional cost for the call.
    """
    collector = get_metrics_collector()
    collector.record_token_usage(prompt_tokens, completion_tokens, model)
    if cost is not None:
        collector.record_cost(cost, source=model, description="LLM call")
