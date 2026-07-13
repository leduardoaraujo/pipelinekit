"""Compatibility wrapper for pipelinekit.core.rate_limiter."""

from pipelinekit.core.rate_limiter import (
    AdaptiveRateLimiter,
    RateLimiter,
    SlidingWindowRateLimiter,
)

__all__ = ["RateLimiter", "SlidingWindowRateLimiter", "AdaptiveRateLimiter"]
