# Environment configuration
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path
from celery import Celery
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ==================== API Keys ====================
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )
    COHERE_API_KEY: Optional[str] = Field(default=None, description="Cohere API key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google AI API key")

    # ==================== Server Configuration ====================
    APP_NAME: str = "VentureOS Agent Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )

    # ==================== Database Configuration ====================
    DATABASE_URL: Optional[str] = Field(
        default="sqlite:///./agent_engine.db", description="Database connection URL"
    )
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    VECTOR_DB_URL: Optional[str] = Field(
        default=None, description="Vector database URL (Qdrant, Pinecone, etc.)"
    )
    VECTOR_DB_API_KEY: Optional[str] = Field(
        default=None, description="Vector DB API key"
    )

    # ==================== Logging Configuration ====================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    LOG_TO_CONSOLE: bool = Field(default=True, description="Log to console")

    # ==================== Agent Factory ====================
    AGENT_FACTORY_CLASS: str = "venture_os.agent_engine.core.agent_factory.AgentFactory"

    # Agent Types
    AGENT_TYPES: List[str] = [
        "base",
        "react",
        "reflex",
        "task-specific",
        "custom",
    ]

    # LLM Defaults
    DEFAULT_LLM_MODEL: str = "gpt-4"
    DEFAULT_LLM_TEMPERATURE: float = 0.7
    DEFAULT_LLM_MAX_TOKENS: int = 2048
    DEFAULT_LLM_TOP_P: float = 1.0
    DEFAULT_LLM_FREQUENCY_PENALTY: float = 0.0

    # Memory Defaults
    DEFAULT_MEMORY_SHORT_TERM_ENABLED: bool = True
    DEFAULT_MEMORY_LONG_TERM_ENABLED: bool = True
    DEFAULT_MEMORY_MAX_HISTORY: int = 100
    DEFAULT_MEMORY_VECTOR_STORE_ENABLED: bool = False

    # Tool Defaults
    DEFAULT_TOOL_CONFIG: dict = {
        "web_search": {"enabled": True, "config": {"engine": "google"}},
        "code_execution": {"enabled": True, "config": {"language": "python"}},
        "file_management": {
            "enabled": True,
            "config": {"base_path": "/tmp/agent_files"},
        },
        "api_access": {"enabled": True, "config": {}},
        "calendar": {"enabled": True, "config": {}},
        "email": {"enabled": True, "config": {}},
        "data_analysis": {"enabled": True, "config": {}},
        "market_research": {"enabled": True, "config": {}},
        "social_media": {"enabled": True, "config": {}},
        "custom_tool": {"enabled": False, "config": {}},
        "budget_monitoring": {"enabled": True, "config": {}},
        "performance_tracking": {"enabled": True, "config": {}},
        "collaboration": {"enabled": True, "config": {}},
        "knowledge_base": {"enabled": True, "config": {}},
        "sentiment_analysis": {"enabled": True, "config": {}},
        "translation": {"enabled": True, "config": {}},
        "summarization": {"enabled": True, "config": {}},
        "question_answering": {"enabled": True, "config": {}},
        "code_generation": {"enabled": True, "config": {}},
        "code_review": {"enabled": True, "config": {}},
        "debugging": {"enabled": True, "config": {}},
        "data_visualization": {"enabled": True, "config": {}},
        "report_generation": {"enabled": True, "config": {}},
        "project_management": {"enabled": True, "config": {}},
        "time_management": {"enabled": True, "config": {}},
        "resource_management": {"enabled": True, "config": {}},
        "communication": {"enabled": True, "config": {}},
        "collaborative_editing": {"enabled": True, "config": {}},
        "version_control": {"enabled": True, "config": {}},
        "testing": {"enabled": True, "config": {}},
        "deployment": {"enabled": True, "config": {}},
        "financial_analysis": {"enabled": True, "config": {}},
        "customer_support": {"enabled": True, "config": {}},
        "hr_management": {
            "enabled": True,
            "config": {},
            "sales": {"enabled": True, "config": {}},
            "marketing": {"enabled": True, "config": {}},
        },
    }

    # Budget Defaults (None = unlimited)
    DEFAULT_BUDGET_MAX_TOKENS: Optional[int] = Field(
        default=None, description="Max tokens per task"
    )
    DEFAULT_BUDGET_MAX_COST: Optional[float] = Field(
        default=10.0, description="Max cost in USD per task"
    )
    DEFAULT_BUDGET_MAX_REQUESTS: Optional[int] = Field(
        default=100, description="Max LLM requests per task"
    )
    DEFAULT_BUDGET_MAX_DURATION_SECONDS: Optional[int] = Field(
        default=300, description="Max execution time"
    )

    # ==================== Model Pricing (per 1K tokens) ====================
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    }

    # ==================== Available Models ====================
    AVAILABLE_MODELS: List[str] = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
    ]

    # ==================== Task Execution ====================
    TASK_DEFAULT_TIMEOUT: int = Field(
        default=300, description="Default task timeout in seconds"
    )
    TASK_MAX_RETRIES: int = Field(
        default=3, description="Max retry attempts for failed tasks"
    )
    TASK_RETRY_DELAY: float = Field(
        default=1.0, description="Initial retry delay in seconds"
    )
    TASK_PARALLEL_LIMIT: int = Field(
        default=5, description="Max parallel task executions"
    )

    # ==================== Rate Limiting ====================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60, description="Max API requests per minute"
    )
    RATE_LIMIT_TOKENS_PER_MINUTE: int = Field(
        default=100000, description="Max tokens per minute"
    )

    # ==================== Cache Configuration ====================
    CACHE_ENABLED: bool = Field(default=True, description="Enable response caching")
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Max cache entries")

    # ==================== Embedding Configuration ====================
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small", description="Embedding model"
    )
    EMBEDDING_DIMENSIONS: int = Field(
        default=1536, description="Embedding vector dimensions"
    )

    class Config:
        env_file = str(Path(__file__).resolve().parents[3] / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# ==================== Settings Instance ====================
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()


#===================Celery Task setting ==========================


# 1. Initialize the Celery app
app = Celery(
    "my_api_project",
    broker="redis://localhost:6379/0",  # Your broker URL
    backend="redis://localhost:6379/0"  # Optional: For storing Celery results
)

# 2. Tell Celery to automatically look inside 'api/tasks/' 
#    for files containing @shared_task
app.autodiscover_tasks(['api'])
