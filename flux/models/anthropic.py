"""Anthropic model provider."""

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


class AnthropicModel:
    """Anthropic Claude model provider."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key

    def _get_client(self) -> Any:
        """Create an AsyncAnthropic client."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ProviderError(
                "anthropic",
                "anthropic package is required. Install with: pip install flux-agents[anthropic]",
            )

        kwargs: dict[str, Any] = {}
        if self._api_key:
            kwargs["api_key"] = self._api_key
        return AsyncAnthropic(**kwargs)

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Get a complete response from Anthropic."""
        client = self._get_client()
        params = self._build_params(request)

        try:
            response = await client.messages.create(**params)
        except Exception as e:
            raise ProviderError("anthropic", str(e))

        content_text = ""
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=json.dumps(block.input),
                    )
                )

        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            requests=1,
        )

        return ModelResponse(
            content=content_text if content_text else None,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=response.stop_reason,
            raw=response,
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        """Stream a response from Anthropic."""
        client = self._get_client()
        params = self._build_params(request)

        try:
            async with client.messages.stream(**params) as stream:
                current_tool_id = ""
                current_tool_name = ""
                current_tool_args = ""

                async for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            current_tool_name = event.content_block.name
                            current_tool_args = ""
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            yield StreamChunk(delta_text=event.delta.text)
                        elif event.delta.type == "input_json_delta":
                            current_tool_args += event.delta.partial_json
                    elif event.type == "content_block_stop":
                        if current_tool_name:
                            yield StreamChunk(
                                tool_call=ToolCall(
                                    id=current_tool_id,
                                    name=current_tool_name,
                                    arguments=current_tool_args,
                                )
                            )
                            current_tool_name = ""
                            current_tool_id = ""
                            current_tool_args = ""
                    elif event.type == "message_stop":
                        final_message = await stream.get_final_message()
                        usage = Usage(
                            input_tokens=final_message.usage.input_tokens,
                            output_tokens=final_message.usage.output_tokens,
                            total_tokens=(
                                final_message.usage.input_tokens
                                + final_message.usage.output_tokens
                            ),
                            requests=1,
                        )
                        yield StreamChunk(done=True, usage=usage)

    def _build_params(self, request: ModelRequest) -> dict[str, Any]:
        """Build Anthropic API parameters."""
        system = request.system_prompt or ""
        messages = []

        for msg in request.messages:
            if msg.role == "system":
                # Anthropic handles system separately
                system = msg.content or ""
                continue

            m: dict[str, Any] = {"role": msg.role}

            if msg.tool_calls:
                # Assistant message with tool calls
                content = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": json.loads(tc.arguments) if tc.arguments else {},
                        }
                    )
                m["content"] = content
            elif msg.tool_call_id:
                # Tool result message
                m["content"] = [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content or "",
                    }
                ]
            else:
                m["content"] = msg.content or ""

            messages.append(m)

        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": request.settings.max_tokens or 4096,
            "messages": messages,
        }

        if system:
            params["system"] = system

        if request.tools:
            params["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in request.tools
            ]

        # Apply settings
        s = request.settings
        if s.temperature is not None:
            params["temperature"] = s.temperature
        if s.top_p is not None:
            params["top_p"] = s.top_p
        if s.stop is not None:
            params["stop_sequences"] = s.stop

        return params
