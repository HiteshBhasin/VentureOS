# Performance tracking and token usage metrics
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
        pass

    def get_total_tokens(self) -> int:
        """Get total tokens used across all calls."""
        pass

    def get_token_usage_by_model(self) -> Dict[str, int]:
        """Get token usage breakdown by model."""
        pass

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
        pass

    def get_total_cost(self) -> float:
        """Get total cost incurred."""
        pass

    def get_cost_by_source(self) -> Dict[str, float]:
        """Get cost breakdown by source."""
        pass

    # ==================== Task Metrics ====================

    def record_task_metric(self, metric: TaskMetric) -> None:
        """Record metrics for a task execution.

        Args:
            metric: Task metric to record.
        """
        pass

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
        pass

    def get_success_rate(self, agent_id: Optional[str] = None) -> float:
        """Get task success rate.

        Args:
            agent_id: Optional agent ID to filter by.

        Returns:
            Success rate as a float between 0 and 1.
        """
        pass

    def get_avg_task_duration(self, agent_id: Optional[str] = None) -> float:
        """Get average task duration in seconds.

        Args:
            agent_id: Optional agent ID to filter by.

        Returns:
            Average duration in seconds.
        """
        pass

    # ==================== Generic Counters & Gauges ====================

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name.
            value: Value to increment by.
        """
        pass

    def get_counter(self, name: str) -> int:
        """Get counter value.

        Args:
            name: Counter name.

        Returns:
            Counter value.
        """
        pass

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric.

        Args:
            name: Gauge name.
            value: Gauge value.
        """
        pass

    def get_gauge(self, name: str) -> float:
        """Get gauge value.

        Args:
            name: Gauge name.

        Returns:
            Gauge value.
        """
        pass

    # ==================== Reporting ====================

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics.

        Returns:
            Dictionary with metric summaries.
        """
        pass

    def reset(self) -> None:
        """Reset all metrics."""
        pass

    def export(self, format: str = "json") -> str:
        """Export metrics in specified format.

        Args:
            format: Export format (json, prometheus, etc.).

        Returns:
            Formatted metrics string.
        """
        pass


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    pass


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
    pass
