"""Logging middleware."""

from __future__ import annotations

import logging
from typing import Any

from .base import NextFn, RequestContext, Response

logger = logging.getLogger("flux.middleware")


class LoggingMiddleware:
    """Logs requests and responses."""

    def __init__(self, level: int = logging.DEBUG) -> None:
        self._level = level

    async def process(self, ctx: RequestContext, next: NextFn) -> Response:
        logger.log(self._level, "→ Agent: %s, messages: %d", ctx.agent_name, len(ctx.messages))
        response = await next(ctx)
        content_preview = (response.content or "")[:200]
        logger.log(self._level, "← Response: %s...", content_preview)
        return response
