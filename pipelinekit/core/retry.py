"""Retry logic with exponential backoff for ETL operations."""

import asyncio
from typing import Any, Callable, Optional, Type

import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()


class RetryConfig:
    """Configuration for retry behavior.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        multiplier: Exponential backoff multiplier
        retry_on: Exception types to retry on
        log_retries: Whether to log retry attempts
    """

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 60.0,
        multiplier: float = 2.0,
        retry_on: Optional[tuple[Type[Exception], ...]] = None,
        log_retries: bool = True,
    ):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.multiplier = multiplier
        self.retry_on = retry_on or (Exception,)
        self.log_retries = log_retries


async def retry_async(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs,
) -> Any:
    """Execute an async function with retry logic.

    Args:
        func: Async function to execute
        config: RetryConfig instance (uses defaults if None)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution

    Raises:
        RetryError: If all retry attempts fail

    Example:
        result = await retry_async(
            fetch_data,
            RetryConfig(max_attempts=5),
            url="https://api.example.com"
        )
    """
    config = config or RetryConfig()

    retry_strategy = AsyncRetrying(
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_exponential(
            multiplier=config.multiplier,
            min=config.min_wait,
            max=config.max_wait,
        ),
        retry=retry_if_exception_type(config.retry_on),
        reraise=True,
    )

    attempt = 0
    async for attempt_state in retry_strategy:
        with attempt_state:
            attempt += 1

            if config.log_retries and attempt > 1:
                logger.warning(
                    "retry_attempt",
                    function=func.__name__,
                    attempt=attempt,
                    max_attempts=config.max_attempts,
                )

            result = await func(*args, **kwargs)
            return result


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator to add retry logic to async functions.

    Args:
        config: RetryConfig instance (uses defaults if None)

    Example:
        @with_retry(RetryConfig(max_attempts=5))
        async def fetch_data(url: str):
            response = await client.get(url)
            return response.json()
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)

        return wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for ETL operations.

    Prevents cascading failures by stopping requests to a failing service
    after a threshold of consecutive failures.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type that counts as failure
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half_open

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self._state == "open":
            if self._should_attempt_reset():
                self._state = "half_open"
                logger.info("circuit_breaker_half_open", function=func.__name__)
            else:
                raise Exception(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    f"Retry after {self.recovery_timeout}s"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False

        import time

        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self._failure_count = 0
        if self._state == "half_open":
            self._state = "closed"
            logger.info("circuit_breaker_closed")

    def _on_failure(self):
        """Increment failure count and potentially open circuit."""
        import time

        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.error(
                "circuit_breaker_opened",
                failure_count=self._failure_count,
                threshold=self.failure_threshold,
            )
