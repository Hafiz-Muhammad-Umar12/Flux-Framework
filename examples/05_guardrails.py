"""Example 05: Guardrails for input/output validation.

Requires: Ollama running locally.
    python examples/05_guardrails.py
"""

import asyncio
from flux import Agent, Runner, LengthGuardrail, PIIGuardrail
from flux.guardrails.base import GuardrailResult, OutputGuardrail
from flux.models.ollama import OllamaModel


class NoCodeOutputGuardrail(OutputGuardrail):
    """Rejects output containing code blocks."""

    @property
    def name(self) -> str:
        return "no_code"

    async def check(self, output: str, context=None) -> GuardrailResult:
        if "```" in output:
            return GuardrailResult(
                passed=False,
                message="Output contains code blocks, which are not allowed",
            )
        return GuardrailResult(passed=True)


model = OllamaModel(model="llama3.2")
agent = Agent(
    name="safe_assistant",
    instructions="You are a helpful assistant. Never output code.",
    model=model,
    guardrails=(
        LengthGuardrail(max_chars=5000),
        PIIGuardrail(),
        NoCodeOutputGuardrail(),
    ),
)

async def main():
    # This should work fine
    result = await Runner.run(agent, "What is Python?")
    print(f"Output: {result.final_output[:100]}...")

    # This should be blocked by PIIGuardrail
    try:
        result = await Runner.run(
            agent,
            "My email is test@example.com, send me info",
        )
    except Exception as e:
        print(f"\nGuardrail blocked: {e}")

asyncio.run(main())
