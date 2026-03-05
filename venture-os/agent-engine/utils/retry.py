# Retry logic with exponential backoff
import asyncio
import random
import time
from typing import Any, Awaitable, Callable, List, Optional, Type, TypeVar
from functools import wraps
import logging


logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]


def calculate_delay(
    attempt: int,
    initial_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool = True,
) -> float:
    """Calculate delay for next retry attempt.

    Args:
        attempt: Current attempt number (0-indexed).
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential_base: Base for exponential backoff.
        jitter: Whether to add random jitter.

    Returns:
        Delay in seconds.
    """
    delay = min(initial_delay * (exponential_base**attempt), max_delay)
    if jitter:
        delay *= 1 + (random.random() - 0.5) * 0.1  # Add up to ±5% jitter
    return delay


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """Decorator for retrying a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay.
        retryable_exceptions: List of exceptions to retry on.
        on_retry: Optional callback on each retry.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempts = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if retryable_exceptions and not any(
                        isinstance(e, exc) for exc in retryable_exceptions
                    ):
                        logger.debug(f"Exception {e} is not retryable. Raising.")
                        raise
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.debug(
                            f"Max attempts reached ({attempts}). Raising exception."
                        )
                        raise
                    delay = calculate_delay(
                        attempt=attempts - 1,
                        initial_delay=initial_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter,
                    )
                    logger.debug(
                        f"Attempt {attempts} failed with exception: {e}. Retrying in {delay:.2f} seconds."
                    )
                    if on_retry:
                        on_retry(e, attempts)
                    time.sleep(delay)

        return wrapper

    return decorator


async def async_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """Async decorator for retrying a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay.
        retryable_exceptions: List of exceptions to retry on.
        on_retry: Optional callback on each retry.

    Returns:
        Decorated async function.
    """

    def decorative(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            attempts = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if retryable_exceptions and not any(
                        isinstance(e, exc) for exc in retryable_exceptions
                    ):
                        logger.debug(f"Exception {e} is not retryable. Raising.")
                        raise
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.debug(
                            f"Max attempts reached ({attempts}). Raising exception."
                        )
                        raise
                    delay = calculate_delay(
                        attempt=attempts - 1,
                        initial_delay=initial_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter,
                    )
                    logger.debug(
                        f"Attempt {attempts} failed with exception: {e}. Retrying in {delay:.2f} seconds."
                    )
                    if on_retry:
                        on_retry(e, attempts)
                    await asyncio.sleep(delay)

        return wrapper

    return decorative


class RetryExecutor:
    """Executor for running functions with retry logic."""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def execute(
        self,
        func: Callable[..., T],
        *args,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        **kwargs,
    ) -> T:
        """Execute a function with retry logic.

        Args:
            func: Function to execute.
            *args: Positional arguments for the function.
            on_retry: Optional callback on each retry.
            **kwargs: Keyword arguments for the function.

        Returns:
            Result of the function.
        """

        @retry(
            max_attempts=self.config.max_attempts,
        )
        def wrapped_func(*args, **kwargs) -> T:
            return func(*args, **kwargs)

        return wrapped_func(*args, **kwargs)

    async def execute_async(
        self,
        func: Callable[..., T],
        *args,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        **kwargs,
    ) -> T:
        """Execute an async function with retry logic.

        Args:
            func: Async function to execute.
            *args: Positional arguments for the function.
            on_retry: Optional callback on each retry.
            **kwargs: Keyword arguments for the function.

        Returns:
            Result of the function.
        """

        @async_retry(
            max_attempts=self.config.max_attempts,
        )
        async def wrapped_func(*args, **kwargs) -> T:
            return await func(*args, **kwargs)

        return await wrapped_func(*args, **kwargs)

    def is_retryable(self, exception: Exception) -> bool:
        """Check if an exception is retryable.

        Args:
            exception: Exception to check.

        Returns:
            True if retryable, False otherwise.
        """
        if not self.config.retryable_exceptions:
            return True
        return any(
            isinstance(exception, exc) for exc in self.config.retryable_exceptions
        )
