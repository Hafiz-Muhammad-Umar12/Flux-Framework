"""Retry middleware."""

from __future__ import annotations

import asyncio
import logging

from ..exceptions import FluxError, ProviderError, ToolError
from .base import NextFn, RequestContext, Response

logger = logging.getLogger("flux.middleware")


class RetryMiddleware:
    """Retries failed requests with exponential backoff."""

    def __init__(self, max_retries: int = 3, backoff_base: float = 1.0) -> None:
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return await next(ctx)
            except (ProviderError, ToolError) as e:
                last_error = e
                if attempt < self._max_retries:
                    wait = self._backoff_base * (2 ** attempt)
                    logger.warning(
                        "Retry %d/%d after %.1fs: %s",
                        attempt + 1,
                        self._max_retries,
                        wait,
                        e,
                    )
                    await asyncio.sleep(wait)

        raise last_error  # type: ignore[misc]
