"""Tests for guardrails."""

import pytest
from flux.guardrails.builtins import LengthGuardrail, PIIGuardrail, ProfanityGuardrail


@pytest.mark.asyncio
async def test_length_guardrail_pass():
    g = LengthGuardrail(max_chars=100)
    result = await g.check("short text")
    assert result.passed


@pytest.mark.asyncio
async def test_length_guardrail_fail():
    g = LengthGuardrail(max_chars=5)
    result = await g.check("this is too long")
    assert not result.passed
    assert "exceeds" in result.message


@pytest.mark.asyncio
async def test_profanity_guardrail_pass():
    g = ProfanityGuardrail(word_list=["bad", "worse"])
    result = await g.check("This is good")
    assert result.passed


@pytest.mark.asyncio
async def test_profanity_guardrail_fail():
    g = ProfanityGuardrail(word_list=["bad", "worse"])
    result = await g.check("This is bad")
    assert not result.passed


@pytest.mark.asyncio
async def test_pii_guardrail_pass():
    g = PIIGuardrail()
    result = await g.check("No PII here")
    assert result.passed


@pytest.mark.asyncio
async def test_pii_guardrail_email():
    g = PIIGuardrail()
    result = await g.check("My email is test@example.com")
    assert not result.passed
    assert "email" in result.metadata["pii_types"]


@pytest.mark.asyncio
async def test_pii_guardrail_phone():
    g = PIIGuardrail()
    result = await g.check("Call me at 555-123-4567")
    assert not result.passed
    assert "phone" in result.metadata["pii_types"]


@pytest.mark.asyncio
async def test_pii_guardrail_ssn():
    g = PIIGuardrail()
    result = await g.check("SSN: 123-45-6789")
    assert not result.passed
    assert "ssn" in result.metadata["pii_types"]
