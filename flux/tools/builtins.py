"""Built-in tools."""

from __future__ import annotations

import os
from typing import Any

from ..context import ToolContext
from .base import ToolResult


class ShellTool:
    """Execute shell commands."""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute a shell command and return its output."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
            },
            "required": ["command"],
        }

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
        import asyncio

        command = args.get("command", "")
        if not command:
            return ToolResult(output="Error: No command provided", success=False)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace")
            if stderr:
                output += "\nSTDERR: " + stderr.decode("utf-8", errors="replace")
            return ToolResult(output=output.strip(), success=proc.returncode == 0)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", success=False)


class FileReadTool:
    """Read file contents."""

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read the contents of a file."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
            },
            "required": ["path"],
        }

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        if not path:
            return ToolResult(output="Error: No path provided", success=False)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolResult(output=content)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", success=False)


class FileWriteTool:
    """Write file contents."""

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        content = args.get("content", "")
        if not path:
            return ToolResult(output="Error: No path provided", success=False)
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(output=f"Successfully wrote to {path}")
        except Exception as e:
            return ToolResult(output=f"Error: {e}", success=False)
