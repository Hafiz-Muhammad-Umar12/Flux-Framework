"""Tests for event bus."""

import asyncio
import pytest
from flux.events.bus import Event, EventBus, AGENT_START, LLM_START


def test_event_bus_subscribe_emit():
    bus = EventBus()
    received = []

    def handler(event: Event):
        received.append(event)

    bus.on(AGENT_START, handler)
    bus.emit(Event(type=AGENT_START, data={"agent": "test"}))

    assert len(received) == 1
    assert received[0].data["agent"] == "test"


def test_event_bus_global_handler():
    bus = EventBus()
    received = []

    bus.on_all(lambda e: received.append(e))
    bus.emit(Event(type="something"))
    bus.emit(Event(type="something_else"))

    assert len(received) == 2


def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    def handler(event: Event):
        received.append(event)

    bus.on(AGENT_START, handler)
    bus.emit(Event(type=AGENT_START))
    assert len(received) == 1

    bus.off(AGENT_START, handler)
    bus.emit(Event(type=AGENT_START))
    assert len(received) == 1  # No new events


def test_event_bus_clear():
    bus = EventBus()
    bus.on(AGENT_START, lambda e: None)
    bus.on_all(lambda e: None)
    bus.clear()
    assert len(bus._handlers) == 0
    assert len(bus._global_handlers) == 0


@pytest.mark.asyncio
async def test_event_bus_async():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.on(LLM_START, handler)
    await bus.emit_async(Event(type=LLM_START))

    assert len(received) == 1


@pytest.mark.asyncio
async def test_event_bus_mixed_handlers():
    bus = EventBus()
    received = []

    def sync_handler(event: Event):
        received.append("sync")

    async def async_handler(event: Event):
        received.append("async")

    bus.on(AGENT_START, sync_handler)
    bus.on(AGENT_START, async_handler)
    await bus.emit_async(Event(type=AGENT_START))

    assert "sync" in received
    assert "async" in received
