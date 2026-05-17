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
        self._default_models: Dict[ModelType, str] = {}

    # ==================== Provider Configuration ====================

    def configure_provider(self, config: ProviderConfig) -> bool:
        """Configure a model provider."""
        self._providers[config.provider] = config
        return True

    def get_provider_config(self, provider: ModelProvider) -> Optional[ProviderConfig]:
        """Get provider configuration."""
        return self._providers.get(provider)

    def update_provider(self, provider: ModelProvider, updates: Dict[str, Any]) -> bool:
        """Update provider configuration."""
        if provider not in self._providers:
            return False
        cfg = self._providers[provider]
        for key, value in updates.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        return True

    def remove_provider(self, provider: ModelProvider) -> bool:
        """Remove provider configuration."""
        if provider in self._providers:
            del self._providers[provider]
            return True
        return False

    def list_configured_providers(self) -> List[ModelProvider]:
        """List configured providers."""
        return list(self._providers.keys())

    def set_api_key(self, provider: ModelProvider, api_key: str) -> None:
        """Set API key for provider."""
        if provider not in self._providers:
            self._providers[provider] = ProviderConfig(
                provider=provider, api_key=api_key
            )
        else:
            self._providers[provider].api_key = api_key

    def get_api_key(self, provider: ModelProvider) -> Optional[str]:
        """Get API key for provider."""
        cfg = self._providers.get(provider)
        return cfg.api_key if cfg else None

    def set_base_url(self, provider: ModelProvider, base_url: str) -> None:
        """Set base URL for provider."""
        if provider not in self._providers:
            self._providers[provider] = ProviderConfig(
                provider=provider, api_key="", base_url=base_url
            )
        else:
            self._providers[provider].base_url = base_url

    # ==================== Model Registration ====================

    def register_model(self, spec: ModelSpec) -> bool:
        """Register a model."""
        if spec.name in self._models:
            return False
        self._models[spec.name] = spec
        return True

    def unregister_model(self, name: str) -> bool:
        """Unregister a model."""
        if name in self._models:
            del self._models[name]
            return True
        return False

    def get_model_spec(self, name: str) -> Optional[ModelSpec]:
        """Get model specification."""
        return self._models.get(name)

    def list_models(
        self,
        provider: Optional[ModelProvider] = None,
        model_type: Optional[ModelType] = None,
    ) -> List[ModelSpec]:
        """List registered models."""
        models = list(self._models.values())
        if provider is not None:
            models = [m for m in models if m.provider == provider]
        if model_type is not None:
            models = [m for m in models if m.model_type == model_type]
        return models

    def has_model(self, name: str) -> bool:
        """Check if model is registered."""
        return name in self._models

    def update_model_spec(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update model specification."""
        if name not in self._models:
            return False
        spec = self._models[name]
        for key, value in updates.items():
            if hasattr(spec, key):
                setattr(spec, key, value)
        return True

    # ==================== Default Parameters ====================

    def set_default_parameters(self, params: ModelParameters) -> None:
        """Set default model parameters."""
        self._default_parameters = params

    def get_default_parameters(self) -> ModelParameters:
        """Get default parameters."""
        return self._default_parameters

    def set_default_temperature(self, temperature: float) -> None:
        """Set default temperature."""
        self._default_parameters.temperature = temperature

    def set_default_max_tokens(self, max_tokens: int) -> None:
        """Set default max tokens."""
        self._default_parameters.max_tokens = max_tokens

    def merge_parameters(self, custom: Dict[str, Any]) -> ModelParameters:
        """Merge custom parameters with defaults."""
        import copy

        merged = copy.copy(self._default_parameters)
        for key, value in custom.items():
            if hasattr(merged, key):
                setattr(merged, key, value)
        return merged

    # ==================== Model Selection ====================

    def get_default_model(
        self, model_type: ModelType = ModelType.CHAT
    ) -> Optional[ModelSpec]:
        """Get default model for type."""
        name = self._default_models.get(model_type)
        if name:
            return self._models.get(name)
        for spec in self._models.values():
            if spec.model_type == model_type:
                return spec
        return None

    def set_default_model(
        self, name: str, model_type: ModelType = ModelType.CHAT
    ) -> None:
        """Set default model for type."""
        if name not in self._models:
            raise ValueError(f"Model not registered: {name}")
        self._default_models[model_type] = name

    def get_cheapest_model(
        self, model_type: ModelType = ModelType.CHAT
    ) -> Optional[ModelSpec]:
        """Get cheapest model for type."""
        candidates = [m for m in self._models.values() if m.model_type == model_type]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda m: m.cost_per_1k_input + m.cost_per_1k_output,
        )

    def get_models_with_vision(self) -> List[ModelSpec]:
        """Get models supporting vision."""
        return [m for m in self._models.values() if m.supports_vision]

    def get_models_with_tools(self) -> List[ModelSpec]:
        """Get models supporting tool use."""
        return [m for m in self._models.values() if m.supports_tools]

    def get_models_by_context(self, min_context: int) -> List[ModelSpec]:
        """Get models with minimum context window."""
        return [m for m in self._models.values() if m.context_window >= min_context]

    # ==================== Model Info ====================

    def get_context_window(self, name: str) -> int:
        """Get model context window."""
        spec = self._models.get(name)
        if spec is None:
            raise ValueError(f"Model not registered: {name}")
        return spec.context_window

    def get_max_output(self, name: str) -> int:
        """Get model max output tokens."""
        spec = self._models.get(name)
        if spec is None:
            raise ValueError(f"Model not registered: {name}")
        return spec.max_output_tokens

    def supports_streaming(self, name: str) -> bool:
        """Check if model supports streaming."""
        spec = self._models.get(name)
        if spec is None:
            raise ValueError(f"Model not registered: {name}")
        return spec.supports_streaming

    def supports_vision(self, name: str) -> bool:
        """Check if model supports vision."""
        spec = self._models.get(name)
        if spec is None:
            raise ValueError(f"Model not registered: {name}")
        return spec.supports_vision

    def supports_tools(self, name: str) -> bool:
        """Check if model supports tools."""
        spec = self._models.get(name)
        if spec is None:
            raise ValueError(f"Model not registered: {name}")
        return spec.supports_tools

    def get_cost_per_token(self, name: str) -> Dict[str, float]:
        """Get cost per token (input/output)."""
        spec = self._models.get(name)
        if spec is None:
            raise ValueError(f"Model not registered: {name}")
        return {
            "input_per_1k": spec.cost_per_1k_input,
            "output_per_1k": spec.cost_per_1k_output,
            "input_per_token": spec.cost_per_1k_input / 1000.0,
            "output_per_token": spec.cost_per_1k_output / 1000.0,
        }

    # ==================== Built-in Models ====================

    def load_builtin_models(self) -> int:
        """Load built-in model definitions. Returns count."""
        all_models = (
            self.get_openai_models()
            + self.get_anthropic_models()
            + self.get_google_models()
            + self.get_groq_models()
        )
        return sum(1 for spec in all_models if self.register_model(spec))

    def get_openai_models(self) -> List[ModelSpec]:
        """Get OpenAI model definitions."""
        return [
            ModelSpec(
                name="gpt-4o",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.CHAT,
                model_id="gpt-4o",
                context_window=128000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.005,
                cost_per_1k_output=0.015,
            ),
            ModelSpec(
                name="gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.CHAT,
                model_id="gpt-4o-mini",
                context_window=128000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
            ),
            ModelSpec(
                name="gpt-4-turbo",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.CHAT,
                model_id="gpt-4-turbo",
                context_window=128000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
            ),
            ModelSpec(
                name="text-embedding-3-small",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.EMBEDDING,
                model_id="text-embedding-3-small",
                context_window=8191,
                max_output_tokens=0,
                supports_streaming=False,
                cost_per_1k_input=0.00002,
                cost_per_1k_output=0.0,
            ),
        ]

    def get_anthropic_models(self) -> List[ModelSpec]:
        """Get Anthropic model definitions."""
        return [
            ModelSpec(
                name="claude-3-5-sonnet",
                provider=ModelProvider.ANTHROPIC,
                model_type=ModelType.CHAT,
                model_id="claude-3-5-sonnet-20241022",
                context_window=200000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
            ),
            ModelSpec(
                name="claude-3-5-haiku",
                provider=ModelProvider.ANTHROPIC,
                model_type=ModelType.CHAT,
                model_id="claude-3-5-haiku-20241022",
                context_window=200000,
                max_output_tokens=8192,
                supports_vision=False,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.0008,
                cost_per_1k_output=0.004,
            ),
            ModelSpec(
                name="claude-3-opus",
                provider=ModelProvider.ANTHROPIC,
                model_type=ModelType.CHAT,
                model_id="claude-3-opus-20240229",
                context_window=200000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
            ),
        ]

    def get_google_models(self) -> List[ModelSpec]:
        """Get Google model definitions."""
        return [
            ModelSpec(
                name="gemini-1.5-pro",
                provider=ModelProvider.GOOGLE,
                model_type=ModelType.CHAT,
                model_id="gemini-1.5-pro-latest",
                context_window=1000000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.00125,
                cost_per_1k_output=0.005,
            ),
            ModelSpec(
                name="gemini-1.5-flash",
                provider=ModelProvider.GOOGLE,
                model_type=ModelType.CHAT,
                model_id="gemini-1.5-flash-latest",
                context_window=1000000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.000075,
                cost_per_1k_output=0.0003,
            ),
            ModelSpec(
                name="gemini-2.0-flash",
                provider=ModelProvider.GOOGLE,
                model_type=ModelType.CHAT,
                model_id="gemini-2.0-flash",
                context_window=1000000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.0001,
                cost_per_1k_output=0.0004,
            ),
        ]

    def get_groq_models(self) -> List[ModelSpec]:
        """Get Groq model definitions."""
        return [
            ModelSpec(
                name="llama-3.1-70b-versatile",
                provider=ModelProvider.GROQ,
                model_type=ModelType.CHAT,
                model_id="llama-3.1-70b-versatile",
                context_window=128000,
                max_output_tokens=8000,
                supports_vision=False,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.00059,
                cost_per_1k_output=0.00079,
            ),
            ModelSpec(
                name="llama-3.1-8b-instant",
                provider=ModelProvider.GROQ,
                model_type=ModelType.CHAT,
                model_id="llama-3.1-8b-instant",
                context_window=128000,
                max_output_tokens=8000,
                supports_vision=False,
                supports_tools=True,
                supports_streaming=True,
                cost_per_1k_input=0.00005,
                cost_per_1k_output=0.00008,
            ),
            ModelSpec(
                name="mixtral-8x7b-32768",
                provider=ModelProvider.GROQ,
                model_type=ModelType.CHAT,
                model_id="mixtral-8x7b-32768",
                context_window=32768,
                max_output_tokens=32768,
                supports_vision=False,
                supports_tools=False,
                supports_streaming=True,
                cost_per_1k_input=0.00027,
                cost_per_1k_output=0.00027,
            ),
        ]

    # ==================== Validation ====================

    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration."""
        errors: List[str] = []
        warnings: List[str] = []
        if not self._providers:
            warnings.append("No providers configured")
        if not self._models:
            warnings.append("No models registered")
        for provider, cfg in self._providers.items():
            if not cfg.api_key and provider not in (
                ModelProvider.OLLAMA,
                ModelProvider.LOCAL,
            ):
                warnings.append(f"Provider '{provider.value}' has no API key set")
        for name, spec in self._models.items():
            if not spec.model_id:
                errors.append(f"Model '{name}' has no model_id")
            if spec.context_window <= 0:
                errors.append(f"Model '{name}' has invalid context_window")
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "provider_count": len(self._providers),
            "model_count": len(self._models),
        }

    def validate_provider(self, provider: ModelProvider) -> bool:
        """Validate provider configuration."""
        if provider not in self._providers:
            return False
        if provider in (ModelProvider.OLLAMA, ModelProvider.LOCAL):
            return True
        return bool(self._providers[provider].api_key)

    def validate_model(self, name: str) -> bool:
        """Validate model configuration."""
        if name not in self._models:
            return False
        spec = self._models[name]
        return bool(spec.model_id) and spec.context_window > 0

    def test_connection(self, provider: ModelProvider) -> bool:
        """Test provider connection (validates config is present and API key is set)."""
        return self.validate_provider(provider)

    # ==================== Import/Export ====================

    def export_config(self) -> Dict[str, Any]:
        """Export configuration."""
        return {
            "providers": {
                p.value: {
                    "api_key": cfg.api_key,
                    "base_url": cfg.base_url,
                    "organization": cfg.organization,
                    "project": cfg.project,
                    "headers": cfg.headers,
                    "timeout": cfg.timeout,
                    "max_retries": cfg.max_retries,
                }
                for p, cfg in self._providers.items()
            },
            "models": {
                name: {
                    "provider": spec.provider.value,
                    "model_type": spec.model_type.value,
                    "model_id": spec.model_id,
                    "context_window": spec.context_window,
                    "max_output_tokens": spec.max_output_tokens,
                    "supports_vision": spec.supports_vision,
                    "supports_tools": spec.supports_tools,
                    "supports_streaming": spec.supports_streaming,
                    "cost_per_1k_input": spec.cost_per_1k_input,
                    "cost_per_1k_output": spec.cost_per_1k_output,
                }
                for name, spec in self._models.items()
            },
            "default_models": {
                mt.value: name for mt, name in self._default_models.items()
            },
            "default_parameters": {
                "temperature": self._default_parameters.temperature,
                "max_tokens": self._default_parameters.max_tokens,
                "top_p": self._default_parameters.top_p,
                "top_k": self._default_parameters.top_k,
                "frequency_penalty": self._default_parameters.frequency_penalty,
                "presence_penalty": self._default_parameters.presence_penalty,
                "stop_sequences": self._default_parameters.stop_sequences,
                "seed": self._default_parameters.seed,
            },
        }

    def import_config(self, config: Dict[str, Any]) -> bool:
        """Import configuration."""
        try:
            for provider_str, cfg_data in config.get("providers", {}).items():
                provider = ModelProvider(provider_str)
                self._providers[provider] = ProviderConfig(
                    provider=provider,
                    api_key=cfg_data.get("api_key", ""),
                    base_url=cfg_data.get("base_url"),
                    organization=cfg_data.get("organization"),
                    project=cfg_data.get("project"),
                    headers=cfg_data.get("headers", {}),
                    timeout=cfg_data.get("timeout", 60),
                    max_retries=cfg_data.get("max_retries", 3),
                )
            for name, spec_data in config.get("models", {}).items():
                self._models[name] = ModelSpec(
                    name=name,
                    provider=ModelProvider(spec_data["provider"]),
                    model_type=ModelType(spec_data["model_type"]),
                    model_id=spec_data["model_id"],
                    context_window=spec_data["context_window"],
                    max_output_tokens=spec_data["max_output_tokens"],
                    supports_vision=spec_data.get("supports_vision", False),
                    supports_tools=spec_data.get("supports_tools", False),
                    supports_streaming=spec_data.get("supports_streaming", True),
                    cost_per_1k_input=spec_data.get("cost_per_1k_input", 0.0),
                    cost_per_1k_output=spec_data.get("cost_per_1k_output", 0.0),
                )
            for mt_str, name in config.get("default_models", {}).items():
                self._default_models[ModelType(mt_str)] = name
            params = config.get("default_parameters", {})
            if params:
                self._default_parameters = ModelParameters(
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 4096),
                    top_p=params.get("top_p", 1.0),
                    top_k=params.get("top_k"),
                    frequency_penalty=params.get("frequency_penalty", 0.0),
                    presence_penalty=params.get("presence_penalty", 0.0),
                    stop_sequences=params.get("stop_sequences", []),
                    seed=params.get("seed"),
                )
            return True
        except (KeyError, ValueError):
            return False

    def load_from_file(self, filepath: str) -> bool:
        """Load configuration from file."""
        import json

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                config = json.load(f)
            return self.import_config(config)
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            return False

    def save_to_file(self, filepath: str) -> bool:
        """Save configuration to file."""
        import json

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.export_config(), f, indent=2)
            return True
        except OSError:
            return False

    def load_from_env(self) -> Dict[ModelProvider, str]:
        """Load API keys from environment variables."""
        import os

        env_map = {
            "OPENAI_API_KEY": ModelProvider.OPENAI,
            "ANTHROPIC_API_KEY": ModelProvider.ANTHROPIC,
            "GOOGLE_API_KEY": ModelProvider.GOOGLE,
            "GEMINI_API_KEY": ModelProvider.GOOGLE,
            "MISTRAL_API_KEY": ModelProvider.MISTRAL,
            "COHERE_API_KEY": ModelProvider.COHERE,
            "GROQ_API_KEY": ModelProvider.GROQ,
        }
        loaded: Dict[ModelProvider, str] = {}
        for env_var, provider in env_map.items():
            key = os.environ.get(env_var)
            if key:
                self.set_api_key(provider, key)
                loaded[provider] = key
        return loaded
