# Centralized logging configuration
import logging
from typing import Any, Dict, Optional
from pathlib import Path


class LoggerConfig:
    """Configuration for the logging system."""

    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LEVEL = logging.INFO

    def __init__(
        self,
        level: int = DEFAULT_LEVEL,
        log_format: str = DEFAULT_FORMAT,
        log_file: Optional[Path] = None,
        enable_console: bool = True,
    ):
        self.level = level
        self.log_format = log_format
        self.log_file = log_file
        self.enable_console = enable_console


def setup_logging(config: Optional[LoggerConfig] = None) -> None:
    """Initialize the logging system with given configuration.

    Args:
        config: Optional logging configuration.
    """
    setup_config = config or LoggerConfig()
    handlers = []
    if setup_config.enable_console:
        handlers.append(logging.StreamHandler())


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name, typically __name__.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


class AgentLogger:
    """Specialized logger for agents with context tracking."""

    def __init__(self, agent_id: str, logger: Optional[logging.Logger] = None):
        self.agent_id = agent_id
        self._logger = logger or get_logger(f"agent.{agent_id}")
        self._context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """Set context data to include in all log messages."""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context data."""
        self._context.clear()

    def _format_message(self, message: str) -> str:
        """Format message with context data."""
        if self._context:
            context_str = " | ".join(f"{k} = {v}" for k, v in self._context.items())
            return f"{message} | {context_str}"
        return message

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        return self._logger.debug(self._format_message(message), **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        return self._logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message."""
        self._logger.error(self._format_message(message), exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message."""
        self._logger.critical(
            self._format_message(message), exc_info=exc_info, **kwargs
        )

    def log_task_start(self, task_id: str, task_name: str) -> None:
        """Log task start event."""
        self._logger.info(f"Task started: {task_name} (ID: {task_id})")

    def log_task_complete(self, task_id: str, result: Any) -> None:
        """Log task completion event."""
        self._logger.info(f"Task completed: ID {task_id} with result: {result}")

    def log_task_error(self, task_id: str, error: Exception) -> None:
        """Log task error event."""
        self._logger.error(
            f"Task error: ID {task_id} with error: {error}", exc_info=True
        )

    def log_llm_request(self, prompt_tokens: int, model: str) -> None:
        """Log LLM request event."""
        self._logger.info(f"LLM request: model={model}, prompt_tokens={prompt_tokens}")

    def log_llm_response(self, completion_tokens: int, total_tokens: int) -> None:
        """Log LLM response event."""
        self._logger.info(
            f"LLM response: completion_tokens={completion_tokens}, total_tokens={total_tokens}"
        )
