"""Rate limiting middleware."""

from __future__ import annotations

import asyncio
import time

from .base import NextFn, RequestContext, Response


class RateLimitMiddleware:
    """Token bucket rate limiter."""

    def __init__(self, max_per_second: float = 10.0) -> None:
        self._max_per_second = max_per_second
        self._tokens = max_per_second
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._max_per_second, self._tokens + elapsed * self._max_per_second)
            self._last_refill = now

            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self._max_per_second
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
            else:
                self._tokens -= 1.0

        return await next(ctx)
