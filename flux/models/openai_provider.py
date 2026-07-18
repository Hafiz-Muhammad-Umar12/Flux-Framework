"""OpenAI model provider (also works with OpenRouter, DeepSeek, Groq, etc.)."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from ..context import Usage
from ..exceptions import ProviderError
from .base import (
    Message,
    ModelRequest,
    ModelResponse,
    StreamChunk,
    ToolCall,
)


class OpenAIModel:
    """OpenAI-compatible model provider.

    Works with OpenAI, OpenRouter, DeepSeek, Groq, and any OpenAI-compatible API.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._base_url = base_url

    def _get_client(self) -> Any:
        """Create an AsyncOpenAI client."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ProviderError(
                "openai",
                "openai package is required. Install with: pip install flux-agents[openai]",
            )

        kwargs: dict[str, Any] = {}
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return AsyncOpenAI(**kwargs)

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Get a complete response from OpenAI."""
        client = self._get_client()
        params = self._build_params(request)

        try:
            response = await client.chat.completions.create(**params)
        except Exception as e:
            raise ProviderError("openai", str(e))

        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=tc.function.arguments,
                    )
                )

        usage = Usage()
        if response.usage:
            usage = Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                requests=1,
            )

        return ModelResponse(
            content=message.content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw=response,
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        """Stream a response from OpenAI."""
        client = self._get_client()
        params = self._build_params(request)
        params["stream"] = True
        params["stream_options"] = {"include_usage": True}

        try:
            response = await client.chat.completions.create(**params)
        except Exception as e:
            raise ProviderError("openai", str(e))

        # Track accumulated tool calls
        tool_calls_accum: dict[int, dict[str, Any]] = {}

        async for chunk in response:
            if not chunk.choices and chunk.usage:
                # Final usage chunk
                yield StreamChunk(
                    done=True,
                    usage=Usage(
                        input_tokens=chunk.usage.prompt_tokens,
                        output_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
                        requests=1,
                    ),
                )
                continue

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                yield StreamChunk(delta_text=delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_accum:
                        tool_calls_accum[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc_delta.id:
                        tool_calls_accum[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_accum[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_accum[idx]["arguments"] += (
                                tc_delta.function.arguments
                            )

            if choice.finish_reason:
                # Emit accumulated tool calls
                tool_calls = []
                for idx in sorted(tool_calls_accum.keys()):
                    tc_data = tool_calls_accum[idx]
                    if tc_data["name"]:
                        tool_calls.append(
                            ToolCall(
                                id=tc_data["id"],
                                name=tc_data["name"],
                                arguments=tc_data["arguments"],
                            )
                        )

                if tool_calls:
                    yield StreamChunk(
                        tool_call=tool_calls[0] if len(tool_calls) == 1 else None,
                        done=True,
                    )
                else:
                    yield StreamChunk(done=True)

    def _build_params(self, request: ModelRequest) -> dict[str, Any]:
        """Build OpenAI API parameters."""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            m: dict[str, Any] = {"role": msg.role}
            if msg.content:
                m["content"] = msg.content
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            messages.append(m)

        params: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if request.tools:
            params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in request.tools
            ]

        if request.output_schema:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "output",
                    "strict": True,
                    "schema": request.output_schema,
                },
            }

        # Apply settings
        s = request.settings
        if s.temperature is not None:
            params["temperature"] = s.temperature
        if s.top_p is not None:
            params["top_p"] = s.top_p
        if s.max_tokens is not None:
            params["max_tokens"] = s.max_tokens
        if s.frequency_penalty is not None:
            params["frequency_penalty"] = s.frequency_penalty
        if s.presence_penalty is not None:
            params["presence_penalty"] = s.presence_penalty
        if s.stop is not None:
            params["stop"] = s.stop
        if s.seed is not None:
            params["seed"] = s.seed
        if s.tool_choice is not None:
            params["tool_choice"] = s.tool_choice
        if s.parallel_tool_calls is not None:
            params["parallel_tool_calls"] = s.parallel_tool_calls

        params.update(s.extra)
        params.update(request.extra)

        return params
