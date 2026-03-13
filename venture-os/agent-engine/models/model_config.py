# Model configuration
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ModelProvider(Enum):
    """Supported model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    GROQ = "groq"
    OLLAMA = "ollama"
    AZURE = "azure"
    LOCAL = "local"


class ModelType(Enum):
    """Types of models."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"


@dataclass
class ModelParameters:
    """Parameters for model inference."""

    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    top_k: Optional[int] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    seed: Optional[int] = None


@dataclass
class ModelSpec:
    """Specification for a model."""

    name: str
    provider: ModelProvider
    model_type: ModelType
    model_id: str
    context_window: int
    max_output_tokens: int
    supports_vision: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class ProviderConfig:
    """Configuration for a model provider."""

    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 60
    max_retries: int = 3


class ModelConfig:
    """Model configuration management."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._providers: Dict[ModelProvider, ProviderConfig] = {}
        self._models: Dict[str, ModelSpec] = {}
        self._default_parameters: ModelParameters = ModelParameters()

    # ==================== Provider Configuration ====================

    def configure_provider(self, config: ProviderConfig) -> bool:
        """Configure a model provider."""
        pass

    def get_provider_config(self, provider: ModelProvider) -> Optional[ProviderConfig]:
        """Get provider configuration."""
        pass

    def update_provider(self, provider: ModelProvider, updates: Dict[str, Any]) -> bool:
        """Update provider configuration."""
        pass

    def remove_provider(self, provider: ModelProvider) -> bool:
        """Remove provider configuration."""
        pass

    def list_configured_providers(self) -> List[ModelProvider]:
        """List configured providers."""
        pass

    def set_api_key(self, provider: ModelProvider, api_key: str) -> None:
        """Set API key for provider."""
        pass

    def get_api_key(self, provider: ModelProvider) -> Optional[str]:
        """Get API key for provider."""
        pass

    def set_base_url(self, provider: ModelProvider, base_url: str) -> None:
        """Set base URL for provider."""
        pass

    # ==================== Model Registration ====================

    def register_model(self, spec: ModelSpec) -> bool:
        """Register a model."""
        pass

    def unregister_model(self, name: str) -> bool:
        """Unregister a model."""
        pass

    def get_model_spec(self, name: str) -> Optional[ModelSpec]:
        """Get model specification."""
        pass

    def list_models(
        self,
        provider: Optional[ModelProvider] = None,
        model_type: Optional[ModelType] = None,
    ) -> List[ModelSpec]:
        """List registered models."""
        pass

    def has_model(self, name: str) -> bool:
        """Check if model is registered."""
        pass

    def update_model_spec(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update model specification."""
        pass

    # ==================== Default Parameters ====================

    def set_default_parameters(self, params: ModelParameters) -> None:
        """Set default model parameters."""
        pass

    def get_default_parameters(self) -> ModelParameters:
        """Get default parameters."""
        pass

    def set_default_temperature(self, temperature: float) -> None:
        """Set default temperature."""
        pass

    def set_default_max_tokens(self, max_tokens: int) -> None:
        """Set default max tokens."""
        pass

    def merge_parameters(self, custom: Dict[str, Any]) -> ModelParameters:
        """Merge custom parameters with defaults."""
        pass

    # ==================== Model Selection ====================

    def get_default_model(
        self, model_type: ModelType = ModelType.CHAT
    ) -> Optional[ModelSpec]:
        """Get default model for type."""
        pass

    def set_default_model(
        self, name: str, model_type: ModelType = ModelType.CHAT
    ) -> None:
        """Set default model for type."""
        pass

    def get_cheapest_model(
        self, model_type: ModelType = ModelType.CHAT
    ) -> Optional[ModelSpec]:
        """Get cheapest model for type."""
        pass

    def get_models_with_vision(self) -> List[ModelSpec]:
        """Get models supporting vision."""
        pass

    def get_models_with_tools(self) -> List[ModelSpec]:
        """Get models supporting tool use."""
        pass

    def get_models_by_context(self, min_context: int) -> List[ModelSpec]:
        """Get models with minimum context window."""
        pass

    # ==================== Model Info ====================

    def get_context_window(self, name: str) -> int:
        """Get model context window."""
        pass

    def get_max_output(self, name: str) -> int:
        """Get model max output tokens."""
        pass

    def supports_streaming(self, name: str) -> bool:
        """Check if model supports streaming."""
        pass

    def supports_vision(self, name: str) -> bool:
        """Check if model supports vision."""
        pass

    def supports_tools(self, name: str) -> bool:
        """Check if model supports tools."""
        pass

    def get_cost_per_token(self, name: str) -> Dict[str, float]:
        """Get cost per token (input/output)."""
        pass

    # ==================== Built-in Models ====================

    def load_builtin_models(self) -> int:
        """Load built-in model definitions. Returns count."""
        pass

    def get_openai_models(self) -> List[ModelSpec]:
        """Get OpenAI model definitions."""
        pass

    def get_anthropic_models(self) -> List[ModelSpec]:
        """Get Anthropic model definitions."""
        pass

    def get_google_models(self) -> List[ModelSpec]:
        """Get Google model definitions."""
        pass

    def get_groq_models(self) -> List[ModelSpec]:
        """Get Groq model definitions."""
        pass

    # ==================== Validation ====================

    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration."""
        pass

    def validate_provider(self, provider: ModelProvider) -> bool:
        """Validate provider configuration."""
        pass

    def validate_model(self, name: str) -> bool:
        """Validate model configuration."""
        pass

    def test_connection(self, provider: ModelProvider) -> bool:
        """Test provider connection."""
        pass

    # ==================== Import/Export ====================

    def export_config(self) -> Dict[str, Any]:
        """Export configuration."""
        pass

    def import_config(self, config: Dict[str, Any]) -> bool:
        """Import configuration."""
        pass

    def load_from_file(self, filepath: str) -> bool:
        """Load configuration from file."""
        pass

    def save_to_file(self, filepath: str) -> bool:
        """Save configuration to file."""
        pass

    def load_from_env(self) -> Dict[ModelProvider, str]:
        """Load API keys from environment."""
        passs
