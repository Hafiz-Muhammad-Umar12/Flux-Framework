"""Tests for middleware."""

import pytest
from flux.middleware.base import RequestContext, Response
from flux.middleware.logging import LoggingMiddleware
from flux.middleware.cache import CacheMiddleware
from flux.middleware.rate_limit import RateLimitMiddleware


@pytest.mark.asyncio
async def test_logging_middleware():
    middleware = LoggingMiddleware()
    ctx = RequestContext(agent_name="test", messages=["hello"])

    async def next_fn(ctx):
        return Response(content="response")

    response = await middleware.process(ctx, next_fn)
    assert response.content == "response"


@pytest.mark.asyncio
async def test_cache_middleware():
    cache = CacheMiddleware(ttl_seconds=60)
    ctx = RequestContext(agent_name="test", messages=["hello"])
    call_count = 0

    async def next_fn(ctx):
        nonlocal call_count
        call_count += 1
        return Response(content=f"response_{call_count}")

    # First call
    r1 = await cache.process(ctx, next_fn)
    assert r1.content == "response_1"

    # Second call — should hit cache
    r2 = await cache.process(ctx, next_fn)
    assert r2.content == "response_1"
    assert call_count == 1  # next_fn not called again

    # Different context — should miss cache
    ctx2 = RequestContext(agent_name="test", messages=["different"])
    r3 = await cache.process(ctx2, next_fn)
    assert r3.content == "response_2"


@pytest.mark.asyncio
async def test_cache_clear():
    cache = CacheMiddleware()
    ctx = RequestContext(agent_name="test", messages=["hello"])

    async def next_fn(ctx):
        return Response(content="cached")

    await cache.process(ctx, next_fn)
    cache.clear()
    assert len(cache._cache) == 0


@pytest.mark.asyncio
async def test_rate_limit_middleware():
    import asyncio
    middleware = RateLimitMiddleware(max_per_second=100)
    ctx = RequestContext(agent_name="test")

    async def next_fn(ctx):
        return Response(content="ok")

    # Should not block
    response = await middleware.process(ctx, next_fn)
    assert response.content == "ok"
