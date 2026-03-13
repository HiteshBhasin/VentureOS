# Multi-model routing (GPT/Claude/Local)
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

    # ==================== Endpoint Management ====================

    def register_endpoint(self, endpoint: ModelEndpoint) -> bool:
        """Register a model endpoint."""
        pass

    def unregister_endpoint(self, name: str) -> bool:
        """Unregister an endpoint."""
        pass

    def update_endpoint(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update endpoint configuration."""
        pass

    def get_endpoint(self, name: str) -> Optional[ModelEndpoint]:
        """Get endpoint by name."""
        pass

    def list_endpoints(self, enabled_only: bool = True) -> List[ModelEndpoint]:
        """List all endpoints."""
        pass

    def enable_endpoint(self, name: str) -> bool:
        """Enable an endpoint."""
        pass

    def disable_endpoint(self, name: str) -> bool:
        """Disable an endpoint."""
        pass

    # ==================== Routing ====================

    def route(self, request: Dict[str, Any]) -> RoutingDecision:
        """Route request to appropriate endpoint."""
        pass

    def route_by_capability(self, capability: ModelCapability) -> RoutingDecision:
        """Route by required capability."""
        pass

    def route_by_cost(self, max_cost: float) -> RoutingDecision:
        """Route to cheapest endpoint under cost limit."""
        pass

    def route_by_latency(self, max_latency_ms: float) -> RoutingDecision:
        """Route to fastest endpoint under latency limit."""
        pass

    def route_by_context_length(self, token_count: int) -> RoutingDecision:
        """Route to endpoint supporting context length."""
        pass

    def route_round_robin(self) -> RoutingDecision:
        """Route using round-robin."""
        pass

    def route_weighted(self) -> RoutingDecision:
        """Route using weighted random."""
        pass

    # ==================== Strategy Management ====================

    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """Set routing strategy."""
        pass

    def get_strategy(self) -> RoutingStrategy:
        """Get current strategy."""
        pass

    def set_fallback_chain(self, endpoint_names: List[str]) -> None:
        """Set fallback chain."""
        pass

    def get_fallback_chain(self) -> List[str]:
        """Get fallback chain."""
        pass

    def add_custom_strategy(self, name: str, strategy_func: Callable) -> None:
        """Add custom routing strategy."""
        pass

    # ==================== Capability Matching ====================

    def get_endpoints_by_capability(
        self, capability: ModelCapability
    ) -> List[ModelEndpoint]:
        """Get endpoints with specific capability."""
        pass

    def get_endpoints_by_provider(self, provider: str) -> List[ModelEndpoint]:
        """Get endpoints by provider."""
        pass

    def get_best_for_task(self, task_type: str) -> Optional[ModelEndpoint]:
        """Get best endpoint for task type."""
        pass

    def supports_capability(
        self, endpoint_name: str, capability: ModelCapability
    ) -> bool:
        """Check if endpoint supports capability."""
        pass

    # ==================== Load Balancing ====================

    def get_endpoint_load(self, name: str) -> Dict[str, Any]:
        """Get endpoint load metrics."""
        pass

    def set_endpoint_weight(self, name: str, weight: float) -> None:
        """Set endpoint weight for load balancing."""
        pass

    def rebalance_weights(self) -> None:
        """Rebalance weights based on performance."""
        pass

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
