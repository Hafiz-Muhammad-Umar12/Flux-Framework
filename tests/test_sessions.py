"""Tests for sessions."""

import pytest
from flux.sessions.in_memory import InMemorySession
from flux.sessions.sqlite import SQLiteSession
import tempfile
import os


@pytest.mark.asyncio
async def test_in_memory_session():
    session = InMemorySession()
    assert session.session_id

    await session.add_messages([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ])

    messages = await session.get_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["content"] == "Hi!"


@pytest.mark.asyncio
async def test_in_memory_session_limit():
    session = InMemorySession(max_messages=5)
    for i in range(10):
        await session.add_messages([{"role": "user", "content": f"msg {i}"}])

    messages = await session.get_messages(limit=3)
    assert len(messages) == 3
    assert messages[0]["content"] == "msg 7"


@pytest.mark.asyncio
async def test_in_memory_session_clear():
    session = InMemorySession()
    await session.add_messages([{"role": "user", "content": "Hello"}])
    await session.clear()
    messages = await session.get_messages()
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_sqlite_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        session = SQLiteSession(db_path=db_path)

        await session.add_messages([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ])

        messages = await session.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_sqlite_session_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        session_id = "test_session"

        # Write
        session1 = SQLiteSession(db_path=db_path, session_id=session_id)
        await session1.add_messages([{"role": "user", "content": "Persist me"}])

        # Read from new instance
        session2 = SQLiteSession(db_path=db_path, session_id=session_id)
        messages = await session2.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Persist me"
