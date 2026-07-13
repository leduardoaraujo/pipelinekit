"""Rate limiting for API requests."""

import asyncio
import time
from collections import deque
from typing import Optional

import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Token bucket rate limiter for API requests.

    Args:
        max_requests: Maximum number of requests allowed in the time window
        time_window: Time window in seconds
        burst_size: Maximum burst size (defaults to max_requests)

    Example:
        limiter = RateLimiter(max_requests=100, time_window=60)
        await limiter.acquire()  # Wait if necessary before making request
    """

    def __init__(
        self,
        max_requests: int,
        time_window: float = 60.0,
        burst_size: Optional[int] = None,
    ):
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        self._tokens = float(self.burst_size)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire

        Raises:
            ValueError: If tokens > burst_size
        """
        if tokens > self.burst_size:
            raise ValueError(f"Cannot acquire {tokens} tokens (burst_size={self.burst_size})")

        async with self._lock:
            while True:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    logger.debug(
                        "rate_limit_acquired",
                        tokens=tokens,
                        remaining=self._tokens,
                    )
                    return

                # Calculate wait time
                wait_time = (tokens - self._tokens) * (self.time_window / self.max_requests)

                logger.debug(
                    "rate_limit_waiting",
                    tokens_needed=tokens,
                    tokens_available=self._tokens,
                    wait_seconds=wait_time,
                )

                await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update

        # Calculate tokens to add based on rate
        tokens_to_add = elapsed * (self.max_requests / self.time_window)

        self._tokens = min(self.burst_size, self._tokens + tokens_to_add)
        self._last_update = now

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more accurate rate limiting.

    Args:
        max_requests: Maximum number of requests in the time window
        time_window: Time window in seconds

    Example:
        limiter = SlidingWindowRateLimiter(max_requests=100, time_window=60)
        async with limiter:
            # Make API request
            pass
    """

    def __init__(self, max_requests: int, time_window: float = 60.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request, waiting if necessary."""
        async with self._lock:
            while True:
                now = time.monotonic()

                # Remove old requests outside the window
                while self._requests and self._requests[0] <= now - self.time_window:
                    self._requests.popleft()

                # Check if we can make a request
                if len(self._requests) < self.max_requests:
                    self._requests.append(now)
                    logger.debug(
                        "sliding_window_acquired",
                        current_requests=len(self._requests),
                        max_requests=self.max_requests,
                    )
                    return

                # Calculate wait time until oldest request expires
                wait_time = (self._requests[0] + self.time_window) - now

                logger.debug(
                    "sliding_window_waiting",
                    current_requests=len(self._requests),
                    wait_seconds=wait_time,
                )

                await asyncio.sleep(wait_time)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on response codes.

    Automatically reduces request rate on errors and gradually increases
    on success.

    Args:
        initial_rate: Initial requests per second
        min_rate: Minimum requests per second
        max_rate: Maximum requests per second
        increase_factor: Factor to increase rate on success
        decrease_factor: Factor to decrease rate on error
    """

    def __init__(
        self,
        initial_rate: float = 10.0,
        min_rate: float = 1.0,
        max_rate: float = 100.0,
        increase_factor: float = 1.1,
        decrease_factor: float = 0.5,
    ):
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.monotonic()
            time_since_last = now - self._last_request

            required_interval = 1.0 / self.current_rate
            if time_since_last < required_interval:
                wait_time = required_interval - time_since_last
                await asyncio.sleep(wait_time)

            self._last_request = time.monotonic()

    def on_success(self) -> None:
        """Increase rate after successful request."""
        self.current_rate = min(self.max_rate, self.current_rate * self.increase_factor)
        logger.debug("adaptive_rate_increased", rate=self.current_rate)

    def on_error(self, status_code: Optional[int] = None) -> None:
        """Decrease rate after error."""
        self.current_rate = max(self.min_rate, self.current_rate * self.decrease_factor)
        logger.warning(
            "adaptive_rate_decreased",
            rate=self.current_rate,
            status_code=status_code,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_val is None:
            self.on_success()
        else:
            self.on_error()
