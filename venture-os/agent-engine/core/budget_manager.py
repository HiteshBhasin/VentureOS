# Token/cost budget tracking
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from logging import Logger


class BudgetType(Enum):
    """Types of budget constraints."""

    TOKENS = "tokens"
    COST = "cost"
    REQUESTS = "requests"
    TIME = "time"


@dataclass
class BudgetLimit:
    """Represents a budget limit."""

    budget_type: BudgetType
    limit: float
    current_usage: float = 0.0
    reset_period: Optional[str] = None  # hourly, daily, weekly, monthly
    last_reset: datetime = field(default_factory=datetime.now)


@dataclass
class BudgetAlert:
    """Budget alert configuration."""

    budget_type: BudgetType
    threshold_percent: float
    callback: Optional[str] = None
    triggered: bool = False


class BudgetManager:
    """Manages token, cost, and resource budgets."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._limits: Dict[BudgetType, BudgetLimit] = {}
        self._alerts: List[BudgetAlert] = []
        self._usage_history: List[Dict[str, Any]] = []
        self._model_pricing: Dict[str, Dict[str, float]] = {}
        self._reservations: Dict[str, Dict[str, Any]] = {}

    # ==================== Budget Configuration ====================

    def set_budget_limit(
        self, budget_type: BudgetType, limit: float, reset_period: Optional[str] = None
    ) -> None:
        """Set a budget limit."""
        if limit < 0:
            raise ValueError("Limit must be non-negative.")

        self._limits[budget_type] = BudgetLimit(
            budget_type=budget_type,
            limit=limit,
            current_usage=0.0,
            reset_period=reset_period,
            last_reset=datetime.now(),
        )

    def get_budget_limit(self, budget_type: BudgetType) -> Optional[BudgetLimit]:
        """Get a budget limit."""
        budget_limit = self._limits.get(budget_type)
        return budget_limit

    def remove_budget_limit(self, budget_type: BudgetType) -> bool:
        """Remove a budget limit."""
        removed_budget = self._limits.pop(budget_type)
        if removed_budget:
            return True
        return False

    def set_all_limits(self, limits: Dict[str, float]) -> None:
        """Set multiple budget limits at once."""
        limits["budget_type"] = limits.get("budget_type", BudgetLimit.limit)
        for key, value in limits.items():
            if not isinstance(value, float) and key == "budget_type":
                raise ValueError(f"{key} is not a valid budget type. must be Numeric")

        # self._limits = limits <- @ TODO this needs to be looked at still

    def get_all_limits(self) -> Dict[BudgetType, BudgetLimit]:
        """Get all budget limits."""
        return self._limits

    # ==================== Usage Tracking ====================

    def record_token_usage(
        self, prompt_tokens: int, completion_tokens: int, model: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Record token usage."""
        tokens = prompt_tokens + completion_tokens

        if not hasattr(self, "token_usage"):
            self.token_usage = []
        self.token_usage.append(
            {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "model": model,
            }
        )
        # update budget limits if they exist.
        if BudgetType.TOKENS in self._limits:
            self._limits[BudgetType.TOKENS].current_usage += tokens
        return {"recorded_usage": self.token_usage}

    def record_cost(self, amount: float, source: str, description: str = "") -> None:
        """Record cost expenditure."""
        if not hasattr(self, "cost"):
            self.cost = {}

        self.cost["amount"] = amount
        self.cost["source"] = source
        self.cost["description"] = description

        self._usage_history.extend(self.cost)

    def record_request(
        self, request_type: str, metadata: Optional[Dict] = None
    ) -> None:
        """Record an API request."""
        records = [
            {
                "type": request_type,
                "metadata": metadata,
            }
        ]
        self._usage_history.extend(records)

    def record_time_usage(
        self, duration_seconds: float, task_id: Optional[str] = None
    ) -> None:
        """Record time usage."""
        if not hasattr(self, "time_records"):
            self.time_records = []

            # Store the time usage
        self.time_records.append(
            {
                "duration_seconds": duration_seconds,
                "task_id": task_id,
                "timestamp": datetime.now(),  # or use time.time()
            }
        )

    def get_current_usage(self, budget_type: BudgetType) -> float:
        """Get current usage for a budget type."""
        current_usage = self._usage_history[-1].get("budget_type", budget_type)
        return current_usage

    def get_usage_history(
        self, budget_type: Optional[BudgetType] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get usage history."""
        return self._usage_history

    # ==================== Budget Checking ====================

    def check_budget(self, budget_type: BudgetType, amount: float) -> bool:
        """Check if amount is within budget."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        usage_amount = self._limits[budget_type].current_usage
        return usage_amount >= amount

    def check_all_budgets(self) -> Dict[BudgetType, Any]:
        """Check all budgets."""
        return self._limits

    def has_budget_for_tokens(self, estimated_tokens: int) -> bool:
        """Check if token budget allows estimated usage."""
        return self._limits[BudgetType.TOKENS].current_usage >= estimated_tokens

    def has_budget_for_cost(self, estimated_cost: float) -> bool:
        """Check if cost budget allows estimated expense."""
        return self._limits[BudgetType.COST].current_usage >= estimated_cost

    def has_budget_for_request(self) -> bool:
        """Check if request budget allows another request."""
        limits = self._limits
        for key, value in limits.items():
            if key == BudgetType.REQUESTS:
                if value.current_usage <= value.limit:
                    return True
        return False

    def has_budget_for_time(self, estimated_seconds: float) -> bool:
        """Check if time budget allows estimated duration."""
        used_time = self._limits[BudgetType.TIME].current_usage
        return used_time + estimated_seconds <= self._limits[BudgetType.TIME].limit

    def estimate_remaining(self, budget_type: BudgetType) -> float:
        """Estimate remaining budget."""
        budget = self._limits[budget_type]
        remaining = budget.limit - budget.current_usage
        return remaining

    # ==================== Budget Enforcement ====================

    def enforce_budget(self, budget_type: BudgetType, amount: float) -> None:
        """Enforce budget, raise exception if exceeded."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        self._limits[budget_type].current_usage += amount

    def enforce_all_budgets(self) -> None:
        """Enforce all budgets."""
        if self._limits:
            self._limits = self._limits

    def reserve_budget(self, budget_type: BudgetType, amount: float) -> str:
        """Reserve budget for upcoming operation."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        reserved_budget = {}
        reserved_budget["budget_type"] = budget_type
        reserved_budget["amount"] = amount
        time_stamp = datetime.now().isoformat()
        reservation_id = f"{budget_type.value}_{time_stamp}"
        return reservation_id

    def release_reservation(self, reservation_id: str) -> None:
        """Release a budget reservation."""
        value = reservation_id.split("_")
        budget_type = value[0]
        amount = value[1]
        if self._limits[BudgetType(budget_type)].current_usage >= float(amount):
            self._limits[BudgetType(budget_type)].current_usage -= float(amount)
            logging.info(
                f"Released reservation {reservation_id}, amount: {amount} from {budget_type} budget."
            )

    def commit_reservation(self, reservation_id: str, actual_amount: float) -> None:
        """Commit a reservation with actual usage."""
        value = reservation_id.split("_")
        budget_type = value[0]
        if self._limits[BudgetType(budget_type)].current_usage >= actual_amount:
            self._limits[BudgetType(budget_type)].current_usage += actual_amount
            logging.info(
                f"Committed reservation {reservation_id}, actual amount: {actual_amount} to {budget_type} budget."
            )

    # ==================== Alerts ====================

    def add_alert(
        self,
        budget_type: BudgetType,
        threshold_percent: float,
        callback: Optional[str] = None,
    ) -> None:
        """Add a budget alert."""
        self._alerts.append(
            BudgetAlert(
                budget_type=budget_type,
                threshold_percent=threshold_percent,
                callback=callback,
            )
        )

    def remove_alert(self, budget_type: BudgetType, threshold_percent: float) -> bool:
        """Remove a budget alert."""
        if threshold_percent <= 0 or threshold_percent > 100:
            raise ValueError("Threshold percent must be between 0 and 100.")

        for alert in self._alerts:
            if (
                alert.budget_type == budget_type
                and alert.threshold_percent == threshold_percent
            ):
                self._alerts.remove(alert)
                return True
        return False

    def check_alerts(self) -> List[BudgetAlert]:
        """Check and trigger alerts."""
        if self._alerts:
            budget_list = []
            for alert in self._alerts:
                budget = self._limits.get(alert.budget_type)
                budget_list.append(budget)
                if budget and budget.limit > 0:
                    usage_percent = (budget.current_usage / budget.limit) * 100
                    if usage_percent >= alert.threshold_percent and not alert.triggered:
                        alert.triggered = True
                        logging.warning(
                            f"Budget alert triggered: {alert.budget_type.value} usage at {usage_percent:.2f}%"
                        )
        return budget_list

    def get_alerts(self) -> List[BudgetAlert]:
        """Get all configured alerts."""
        for alerts in self._alerts:
            logging.info(
                f"Alert: {alerts.budget_type.value} at {alerts.threshold_percent}%"
            )
        return self._alerts

    def reset_alert(self, budget_type: BudgetType, threshold_percent: float) -> None:
        """Reset a triggered alert."""
        for alerts in self._alerts:
            if (
                alerts.budget_type == budget_type
                and alerts.threshold_percent == threshold_percent
            ):
                alerts.triggered = False
                logging.info(
                    f"Reset alert for {budget_type.value} at {threshold_percent}%"
                )

    # ==================== Reset & Cleanup ====================

    def reset_usage(self, budget_type: Optional[BudgetType] = None) -> None:
        """Reset usage counters."""
        if budget_type is None:
            self.reset_all_usage()
        elif budget_type in self._limits:
            self._limits[budget_type].current_usage = 0.0
            self._limits[budget_type].last_reset = datetime.now()
            logging.info(f"Reset usage for {budget_type.value}")

    def reset_all_usage(self) -> None:
        """Reset all usage counters."""
        for budget_type, budget_limit in self._limits.items():
            budget_limit.current_usage = 0.0
            budget_limit.last_reset = datetime.now()
        logging.info("Reset all usage counters")

    def check_reset_periods(self) -> None:
        """Check and perform periodic resets."""
        now = datetime.now()
        for budget_type, budget_limit in self._limits.items():
            if budget_limit.reset_period is None:
                continue

            elapsed = now - budget_limit.last_reset
            should_reset = False

            if (
                budget_limit.reset_period == "hourly"
                and elapsed.total_seconds() >= 3600
            ):
                should_reset = True
            elif budget_limit.reset_period == "daily" and elapsed.days >= 1:
                should_reset = True
            elif budget_limit.reset_period == "weekly" and elapsed.days >= 7:
                should_reset = True
            elif budget_limit.reset_period == "monthly" and elapsed.days >= 30:
                should_reset = True

            if should_reset:
                budget_limit.current_usage = 0.0
                budget_limit.last_reset = now
                # Reset any alerts for this budget type
                for alert in self._alerts:
                    if alert.budget_type == budget_type:
                        alert.triggered = False
                logging.info(f"Periodic reset performed for {budget_type.value}")

    def clear_history(self) -> None:
        """Clear usage history."""
        self._usage_history.clear()
        if hasattr(self, "token_usage"):
            self.token_usage.clear()
        if hasattr(self, "time_records"):
            self.time_records.clear()
        if hasattr(self, "cost"):
            self.cost.clear()
        logging.info("Cleared all usage history")

    # ==================== Reporting ====================

    def get_budget_status(self) -> Dict[str, Any]:
        """Get comprehensive budget status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "budgets": {},
            "alerts": [],
            "overall_health": "healthy",
        }

        for budget_type, budget_limit in self._limits.items():
            usage_percent = (
                (budget_limit.current_usage / budget_limit.limit * 100)
                if budget_limit.limit > 0
                else 0
            )
            remaining = budget_limit.limit - budget_limit.current_usage

            status["budgets"][budget_type.value] = {
                "limit": budget_limit.limit,
                "current_usage": budget_limit.current_usage,
                "remaining": remaining,
                "usage_percent": round(usage_percent, 2),
                "reset_period": budget_limit.reset_period,
                "last_reset": budget_limit.last_reset.isoformat(),
            }

            if usage_percent >= 90:
                status["overall_health"] = "critical"
            elif usage_percent >= 75 and status["overall_health"] != "critical":
                status["overall_health"] = "warning"

        for alert in self._alerts:
            status["alerts"].append(
                {
                    "budget_type": alert.budget_type.value,
                    "threshold_percent": alert.threshold_percent,
                    "triggered": alert.triggered,
                    "callback": alert.callback,
                }
            )

        return status

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(self._usage_history),
            "by_type": {},
        }

        for budget_type, budget_limit in self._limits.items():
            summary["by_type"][budget_type.value] = {
                "current_usage": budget_limit.current_usage,
                "limit": budget_limit.limit,
                "remaining": budget_limit.limit - budget_limit.current_usage,
            }

        if hasattr(self, "token_usage"):
            total_prompt = sum(t.get("prompt_tokens", 0) for t in self.token_usage)
            total_completion = sum(
                t.get("completion_tokens", 0) for t in self.token_usage
            )
            summary["tokens"] = {
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_completion,
                "total_tokens": total_prompt + total_completion,
            }

        return summary

    def generate_budget_report(self, period: str = "daily") -> Dict[str, Any]:
        """Generate budget report for period."""
        report = {
            "report_type": "budget_report",
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "status": self.get_budget_status(),
            "summary": self.get_usage_summary(),
            "alerts_triggered": [a for a in self._alerts if a.triggered],
            "recommendations": [],
        }

        # Add recommendations based on usage patterns
        for budget_type, budget_limit in self._limits.items():
            if budget_limit.limit > 0:
                usage_percent = (budget_limit.current_usage / budget_limit.limit) * 100
                if usage_percent >= 90:
                    report["recommendations"].append(
                        f"Critical: {budget_type.value} budget is at {usage_percent:.1f}%. Consider increasing limit or reducing usage."
                    )
                elif usage_percent >= 75:
                    report["recommendations"].append(
                        f"Warning: {budget_type.value} budget is at {usage_percent:.1f}%. Monitor closely."
                    )

        return report

    def export_usage_data(self, format: str = "json") -> Any:
        """Export usage data."""
        import json

        data = {
            "exported_at": datetime.now().isoformat(),
            "limits": {
                bt.value: {
                    "limit": bl.limit,
                    "current_usage": bl.current_usage,
                    "reset_period": bl.reset_period,
                    "last_reset": bl.last_reset.isoformat(),
                }
                for bt, bl in self._limits.items()
            },
            "alerts": [
                {
                    "budget_type": a.budget_type.value,
                    "threshold_percent": a.threshold_percent,
                    "triggered": a.triggered,
                }
                for a in self._alerts
            ],
            "usage_history": self._usage_history,
        }

        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "dict":
            return data
        else:
            raise ValueError(f"Unsupported export format: {format}")

    # ==================== Cost Estimation ====================

    def estimate_token_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for token usage."""
        if model not in self._model_pricing:
            logging.warning(f"No pricing set for model {model}, returning 0.0")
            return 0.0

        pricing = self._model_pricing[model]
        # Assume tokens are split evenly between input/output if not specified
        input_cost = pricing.get("input_per_1k", 0.0) * (tokens / 1000)
        output_cost = pricing.get("output_per_1k", 0.0) * (tokens / 1000)

        return (input_cost + output_cost) / 2  # Average since we don't know split

    def estimate_task_cost(self, task: Dict[str, Any]) -> float:
        """Estimate cost for a task."""
        estimated_cost = 0.0

        # Estimate based on task type and complexity
        estimated_tokens = task.get("estimated_tokens", 1000)
        model = task.get("model", "default")

        # Token cost
        token_cost = self.estimate_token_cost(estimated_tokens, model)
        estimated_cost += token_cost

        # Time cost if applicable
        estimated_time = task.get("estimated_time_seconds", 0)
        if estimated_time > 0 and BudgetType.TIME in self._limits:
            time_limit = self._limits[BudgetType.TIME]
            if time_limit.limit > 0:
                time_cost = (estimated_time / time_limit.limit) * time_limit.limit
                estimated_cost += time_cost * 0.001  # Nominal time cost

        return estimated_cost

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for a model."""
        return self._model_pricing.get(model, {})

    def set_model_pricing(self, model: str, pricing: Dict[str, float]) -> None:
        """Set pricing for a model."""
        if not isinstance(pricing, dict):
            raise ValueError("Pricing must be a dictionary")

        # Validate pricing keys
        valid_keys = {"input_per_1k", "output_per_1k", "per_request", "per_minute"}
        for key in pricing.keys():
            if key not in valid_keys:
                logging.warning(f"Unknown pricing key: {key}")

        self._model_pricing[model] = pricing
        logging.info(f"Set pricing for model {model}: {pricing}")
        pass
