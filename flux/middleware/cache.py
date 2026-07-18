"""Caching middleware."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .base import NextFn, RequestContext, Response


class CacheMiddleware:
    """Caches model responses by message hash with configurable TTL."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Response]] = {}

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        key = self._cache_key(ctx)
        now = time.time()

        # Check cache
        if key in self._cache:
            cached_time, cached_response = self._cache[key]
            if now - cached_time < self._ttl:
                return cached_response
            else:
                del self._cache[key]

        response = await next(ctx)

        # Store in cache
        self._cache[key] = (now, response)
        return response

    def _cache_key(self, ctx: RequestContext) -> str:
        """Generate cache key from request context."""
        data = json.dumps(
            {"agent": ctx.agent_name, "messages": ctx.messages},
            default=str,
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
