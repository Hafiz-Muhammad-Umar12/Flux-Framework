"""Ollama model provider."""

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


class OllamaModel:
    """Ollama model provider using aiohttp."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Get a complete response from Ollama."""
        try:
            import aiohttp
        except ImportError:
            raise ProviderError(
                "ollama",
                "aiohttp is required for Ollama. Install with: pip install flux-agents[ollama]",
            )

        payload = self._build_payload(request, stream=False)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    # If tools not supported, retry without tools
                    if "does not support tools" in error_text and payload.get("tools"):
                        payload.pop("tools", None)
                        async with session.post(
                            f"{self.base_url}/api/chat",
                            json=payload,
                        ) as retry_resp:
                            if retry_resp.status != 200:
                                error_text2 = await retry_resp.text()
                                raise ProviderError("ollama", error_text2, retry_resp.status)
                            data = await retry_resp.json()
                    else:
                        raise ProviderError("ollama", error_text, resp.status)
                else:
                    data = await resp.json()

        return self._parse_response(data)

    async def stream(self, request: ModelRequest) -> AsyncIterator[StreamChunk]:
        """Stream a response from Ollama."""
        try:
            import aiohttp
        except ImportError:
            raise ProviderError(
                "ollama",
                "aiohttp is required for Ollama. Install with: pip install flux-agents[ollama]",
            )

        payload = self._build_payload(request, stream=True)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ProviderError("ollama", error_text, resp.status)

                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue
                    try:
                        chunk_data = json.loads(line_str)
                    except json.JSONDecodeError:
                        continue

                    message = chunk_data.get("message", {})
                    content = message.get("content", "")
                    done = chunk_data.get("done", False)

                    if content:
                        yield StreamChunk(delta_text=content)

                    if done:
                        yield StreamChunk(
                            done=True,
                            usage=Usage(
                                input_tokens=chunk_data.get("prompt_eval_count", 0),
                                output_tokens=chunk_data.get("eval_count", 0),
                                total_tokens=chunk_data.get("prompt_eval_count", 0)
                                + chunk_data.get("eval_count", 0),
                            ),
                        )

    def _build_payload(self, request: ModelRequest, stream: bool) -> dict[str, Any]:
        """Build Ollama API payload."""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            m: dict[str, Any] = {"role": msg.role, "content": msg.content or ""}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        }
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            messages.append(m)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        if request.tools:
            payload["tools"] = [
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

        # Apply settings
        s = request.settings
        if s.temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = s.temperature
        if s.top_p is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["top_p"] = s.top_p
        if s.max_tokens is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = s.max_tokens
        if s.stop is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["stop"] = s.stop

        return payload

    def _parse_response(self, data: dict[str, Any]) -> ModelResponse:
        """Parse Ollama response to ModelResponse."""
        message = data.get("message", {})
        content = message.get("content")
        tool_calls: list[ToolCall] = []

        raw_tool_calls = message.get("tool_calls", [])
        for i, tc in enumerate(raw_tool_calls):
            func = tc.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=f"call_{i}",
                    name=func.get("name", ""),
                    arguments=json.dumps(func.get("arguments", {})),
                )
            )

        usage = Usage(
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            requests=1,
        )

        return ModelResponse(
            content=content if content else None,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason="stop" if not tool_calls else "tool_calls",
            raw=data,
        )
