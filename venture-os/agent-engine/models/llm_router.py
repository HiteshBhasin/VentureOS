# Multi-model routing (GPT/Claude/Local)
import random
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class RoutingStrategy(Enum):
    """Strategies for routing requests."""

    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    FALLBACK = "fallback"
    CAPABILITY_BASED = "capability_based"


class ModelCapability(Enum):
    """Model capabilities."""

    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    CREATIVE_WRITING = "creative_writing"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    VISION = "vision"
    TOOL_USE = "tool_use"
    LONG_CONTEXT = "long_context"


@dataclass
class ModelEndpoint:
    """Configuration for a model endpoint."""

    name: str
    provider: str
    model_id: str
    base_url: str
    api_key: str
    capabilities: List[ModelCapability] = field(default_factory=list)
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    latency_ms: float = 0.0
    weight: float = 1.0
    max_context_length: int = 4096
    enabled: bool = True
    rate_limit: Optional[int] = None


@dataclass
class RoutingDecision:
    """Result of routing decision."""

    endpoint: ModelEndpoint
    reason: str
    fallback_endpoints: List[ModelEndpoint] = field(default_factory=list)


class LLMRouter:
    """Routes LLM requests to appropriate models."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._endpoints: Dict[str, ModelEndpoint] = {}
        self._strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED
        self._fallback_chain: List[str] = []
        self._round_robin_index: int = 0

    # ==================== Endpoint Management ====================

    def register_endpoint(self, endpoint: ModelEndpoint) -> bool:
        """Register a model endpoint."""
        if endpoint.name in self._endpoints:
            return False  # Endpoint with this name already exists
        self._endpoints[endpoint.name] = endpoint
        return True

    def unregister_endpoint(self, name: str) -> bool:
        """Unregister an endpoint."""
        if name in self._endpoints:
            del self._endpoints[name]
            return True
        return False

    def update_endpoint(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update endpoint configuration."""
        if name not in self._endpoints:
            return False
        for key, value in updates.items():
            if hasattr(self._endpoints[name], key):
                setattr(self._endpoints[name], key, value)
        return True

    def get_endpoint(self, name: str) -> Optional[ModelEndpoint]:
        """Get endpoint by name."""
        return self._endpoints.get(name)

    def list_endpoints(self, enabled_only: bool = True) -> List[ModelEndpoint]:
        """List all endpoints."""
        if enabled_only:
            return [ep for ep in self._endpoints.values() if ep.enabled]
        return list(self._endpoints.values())

    def enable_endpoint(self, name: str) -> bool:
        """Enable an endpoint."""
        if name in self._endpoints:
            self._endpoints[name].enabled = True
            return True
        return False

    def disable_endpoint(self, name: str) -> bool:
        """Disable an endpoint."""
        if name in self._endpoints:
            self._endpoints[name].enabled = False
            return True
        return False

    # ==================== Routing ====================

    def route(self, request: Dict[str, Any]) -> RoutingDecision:
        """Route request to appropriate endpoint."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        strategy = self._strategy

        # For capability-based routing, pre-filter by the requested capability
        if strategy == RoutingStrategy.CAPABILITY_BASED:
            capability = request.get("capability")
            if capability:
                capable = [ep for ep in available if capability in ep.capabilities]
                if capable:
                    available = capable

        if strategy == RoutingStrategy.COST_OPTIMIZED:
            endpoint = min(
                available, key=lambda ep: ep.cost_per_1k_input + ep.cost_per_1k_output
            )
            reason = "cost_optimized"

        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            # Use number of capabilities as a quality proxy; higher cost as tiebreaker
            endpoint = max(
                available, key=lambda ep: (len(ep.capabilities), ep.cost_per_1k_input)
            )
            reason = "quality_optimized"

        elif strategy == RoutingStrategy.SPEED_OPTIMIZED:
            endpoint = min(available, key=lambda ep: ep.latency_ms)
            reason = "speed_optimized"

        elif strategy == RoutingStrategy.ROUND_ROBIN:
            endpoint = available[self._round_robin_index % len(available)]
            self._round_robin_index += 1
            reason = "round_robin"

        elif strategy == RoutingStrategy.WEIGHTED:
            weights = [ep.weight for ep in available]
            endpoint = random.choices(available, weights=weights, k=1)[0]
            reason = "weighted"

        elif strategy == RoutingStrategy.FALLBACK:
            endpoint = next(
                (
                    self._endpoints[name]
                    for name in self._fallback_chain
                    if name in self._endpoints and self._endpoints[name].enabled
                ),
                available[0],
            )
            reason = "fallback"

        else:  # CAPABILITY_BASED after pre-filter, or unknown strategy
            endpoint = available[0]
            reason = strategy.value

        fallbacks = [ep for ep in available if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint, reason=reason, fallback_endpoints=fallbacks
        )

    def route_by_capability(self, capability: ModelCapability) -> RoutingDecision:
        """Route by required capability."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        capable = [ep for ep in available if capability in ep.capabilities]
        if not capable:
            raise ValueError(f"No endpoints available with capability: {capability}")

        endpoint = capable[0]
        fallbacks = [ep for ep in capable if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint, reason="capability_based", fallback_endpoints=fallbacks
        )

    def route_by_cost(self, max_cost: float) -> RoutingDecision:
        """Route to cheapest endpoint under cost limit."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        affordable = [
            ep
            for ep in available
            if (ep.cost_per_1k_input + ep.cost_per_1k_output) <= max_cost
        ]
        if not affordable:
            raise ValueError(f"No endpoints available under cost: {max_cost}")

        endpoint = min(
            affordable, key=lambda ep: ep.cost_per_1k_input + ep.cost_per_1k_output
        )
        fallbacks = [ep for ep in affordable if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint, reason="cost_based", fallback_endpoints=fallbacks
        )

    def route_by_latency(self, max_latency_ms: float) -> RoutingDecision:
        """Route to fastest endpoint under latency limit."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        fast = [ep for ep in available if ep.latency_ms <= max_latency_ms]
        if not fast:
            raise ValueError(
                f"No endpoints available under latency: {max_latency_ms} ms"
            )

        endpoint = min(fast, key=lambda ep: ep.latency_ms)
        fallbacks = [ep for ep in fast if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint, reason="latency_based", fallback_endpoints=fallbacks
        )

    def route_by_context_length(self, token_count: int) -> RoutingDecision:
        """Route to endpoint supporting context length."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        suitable = [ep for ep in available if ep.max_context_length >= token_count]
        if not suitable:
            raise ValueError(
                f"No endpoints available for context length: {token_count}"
            )

        endpoint = min(suitable, key=lambda ep: ep.max_context_length)
        fallbacks = [ep for ep in suitable if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint,
            reason="context_length_based",
            fallback_endpoints=fallbacks,
        )

    def route_round_robin(self) -> RoutingDecision:
        """Route using round-robin."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        endpoint = available[self._round_robin_index % len(available)]
        self._round_robin_index += 1

        fallbacks = [ep for ep in available if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint, reason="round_robin", fallback_endpoints=fallbacks
        )

    def route_weighted(self) -> RoutingDecision:
        """Route using weighted random."""
        available = [ep for ep in self._endpoints.values() if ep.enabled]
        if not available:
            raise ValueError("No enabled endpoints available")

        total_weight = sum(ep.weight for ep in available)
        if total_weight == 0:
            raise ValueError("No endpoints with positive weight available")

        choice = random.uniform(0, total_weight)
        cumulative_weight = 0
        for ep in available:
            cumulative_weight += ep.weight
            if choice <= cumulative_weight:
                endpoint = ep
                break

        fallbacks = [ep for ep in available if ep.name != endpoint.name]
        return RoutingDecision(
            endpoint=endpoint, reason="weighted_random", fallback_endpoints=fallbacks
        )

    # ==================== Strategy Management ====================

    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """Set routing strategy."""
        if strategy not in RoutingStrategy:
            raise ValueError(f"Invalid routing strategy: {strategy}")

        self._strategy = strategy

    def get_strategy(self) -> RoutingStrategy:
        """Get current strategy."""
        return self._strategy

    def set_fallback_chain(self, endpoint_names: List[str]) -> None:
        """Set fallback chain."""
        for name in endpoint_names:
            if name not in self._endpoints:
                raise ValueError(f"Endpoint not found for fallback: {name}")
        self._fallback_chain = endpoint_names

    def get_fallback_chain(self) -> List[str]:
        """Get fallback chain."""
        return self._fallback_chain

    def add_custom_strategy(self, name: str, strategy_func: Callable) -> None:
        """Add custom routing strategy."""
        if hasattr(
            self, f"_custom_strategy_{name}"
        ):  # this is checking is the strategy already exists, if it does it raises an error to avoid overwriting existing strategies
            raise ValueError(f"Custom strategy already exists: {name}")
        setattr(self, f"_custom_strategy_{name}", strategy_func)

    # ==================== Capability Matching ====================

    def get_endpoints_by_capability(
        self, capability: ModelCapability
    ) -> List[ModelEndpoint]:
        """Get endpoints with specific capability."""
        return [ep for ep in self._endpoints.values() if capability in ep.capabilities]

    def get_endpoints_by_provider(self, provider: str) -> List[ModelEndpoint]:
        """Get endpoints by provider."""
        return [ep for ep in self._endpoints.values() if ep.provider == provider]

    def get_best_for_task(self, task_type: str) -> Optional[ModelEndpoint]:
        """Get best endpoint for task type."""
        if task_type == "code_generation":
            return self.route_by_capability(ModelCapability.CODE_GENERATION).endpoint
        elif task_type == "reasoning":
            return self.route_by_capability(ModelCapability.REASONING).endpoint
        elif task_type == "creative_writing":
            return self.route_by_capability(ModelCapability.CREATIVE_WRITING).endpoint
        elif task_type == "summarization":
            return self.route_by_capability(ModelCapability.SUMMARIZATION).endpoint
        elif task_type == "translation":
            return self.route_by_capability(ModelCapability.TRANSLATION).endpoint
        elif task_type == "vision":
            return self.route_by_capability(ModelCapability.VISION).endpoint
        elif task_type == "tool_use":
            return self.route_by_capability(ModelCapability.TOOL_USE).endpoint
        elif task_type == "long_context":
            return self.route_by_capability(ModelCapability.LONG_CONTEXT).endpoint
        else:
            return None

    def supports_capability(
        self, endpoint_name: str, capability: ModelCapability
    ) -> bool:
        """Check if endpoint supports capability."""
        for ep in self._endpoints.values():
            if ep.name == endpoint_name:
                return capability in ep.capabilities
        return False

    # ==================== Load Balancing ====================

    def get_endpoint_load(self, name: str) -> Dict[str, Any]:
        """Get endpoint load metrics."""
        for ep in self._endpoints.values():
            if ep.name == name:
                return {
                    "active_requests": 0,  # Placeholder for active request count
                    "queue_length": 0,  # Placeholder for queue length
                    "latency_ms": ep.latency_ms,
                }
        raise ValueError(f"Endpoint not found: {name}")

    def set_endpoint_weight(self, name: str, weight: float) -> None:
        """Set endpoint weight for load balancing."""
        for ep in self._endpoints.values():
            if ep.name == name:
                ep.weight = weight
                return
        raise ValueError(f"Endpoint not found: {name}")

    def rebalance_weights(self) -> None:
        """Rebalance weights based on performance (inverse latency)."""
        endpoints = [ep for ep in self._endpoints.values() if ep.enabled]
        if not endpoints:
            return

        # Score = 1 / latency_ms; endpoints with latency=0 get max score
        scores = [
            1.0 / ep.latency_ms if ep.latency_ms > 0 else float("inf")
            for ep in endpoints
        ]

        # If any endpoint has infinite score, give it weight=1.0 and others weight=0.0
        if any(s == float("inf") for s in scores):
            for ep, score in zip(endpoints, scores):
                ep.weight = 1.0 if score == float("inf") else 0.0
            return

        total = sum(scores)
        for ep, score in zip(endpoints, scores):
            ep.weight = score / total

    def get_health_status(self, name: str) -> Dict[str, Any]:
        """Get endpoint health status."""
        pass

    def mark_unhealthy(self, name: str, duration_seconds: int = 60) -> None:
        """Mark endpoint as unhealthy."""
        pass

    def mark_healthy(self, name: str) -> None:
        """Mark endpoint as healthy."""
        pass

    # ==================== Cost Management ====================

    def estimate_cost(
        self, endpoint_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate request cost."""
        pass

    def get_cheapest_endpoint(
        self, capabilities: Optional[List[ModelCapability]] = None
    ) -> Optional[ModelEndpoint]:
        """Get cheapest endpoint."""
        pass

    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary by endpoint."""
        pass

    def set_cost_limit(self, endpoint_name: str, daily_limit: float) -> None:
        """Set daily cost limit for endpoint."""
        pass

    # ==================== Rate Limiting ====================

    def check_rate_limit(self, name: str) -> bool:
        """Check if endpoint is within rate limit."""
        pass

    def get_rate_limit_status(self, name: str) -> Dict[str, Any]:
        """Get rate limit status."""
        pass

    def set_rate_limit(self, name: str, requests_per_minute: int) -> None:
        """Set rate limit for endpoint."""
        pass

    def reset_rate_limit(self, name: str) -> None:
        """Reset rate limit counter."""
        pass

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        pass

    def get_endpoint_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for endpoint."""
        pass

    def get_routing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get routing decision history."""
        pass

    def reset_stats(self) -> None:
        """Reset all statistics."""
        pass

    # ==================== Configuration ====================

    def export_config(self) -> Dict[str, Any]:
        """Export router configuration."""
        pass

    def import_config(self, config: Dict[str, Any]) -> bool:
        """Import router configuration."""
        pass

    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration."""
        pass
