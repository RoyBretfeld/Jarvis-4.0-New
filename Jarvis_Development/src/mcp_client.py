"""
Jarvis 4.0 – MCP Client (Model Context Protocol)
AWP-041: Generic MCP client  |  AWP-042: Filesystem server binding

MCP (https://modelcontextprotocol.io) defines a standard JSON-RPC 2.0
transport for tool-capable LLM servers.  This client speaks the protocol
over stdio (subprocess) or TCP, and exposes a clean async Python API.

RB-Protokoll: Transparenz – every tool call is logged before execution.
Security:     Only paths inside PROJECT_ROOT are allowed for fs-server ops.
Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.mcp")

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# ─────────────────────────────────────────────
# Protocol types (JSON-RPC 2.0 / MCP)
# ─────────────────────────────────────────────

@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class MCPCallResult:
    tool: str
    success: bool
    content: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    @property
    def text(self) -> str:
        return "\n".join(
            c.get("text", "") for c in self.content if c.get("type") == "text"
        )


# ─────────────────────────────────────────────
# Base MCP transport (stdio subprocess)
# ─────────────────────────────────────────────

class MCPTransport:
    """JSON-RPC 2.0 over stdio (spawned MCP server process)."""

    def __init__(self, command: list[str]) -> None:
        self._command = command
        self._proc: asyncio.subprocess.Process | None = None
        self._pending: dict[str, asyncio.Future[dict]] = {}
        self._reader_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            *self._command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._reader_task = asyncio.create_task(self._read_loop())
        log.info("MCP transport started: %s", " ".join(self._command))

    async def stop(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
        if self._proc:
            self._proc.kill()
            await self._proc.wait()

    async def send(self, method: str, params: dict | None = None) -> dict:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("MCP transport not started")
        req_id = str(uuid.uuid4())
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }
        raw = json.dumps(message) + "\n"
        fut: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        self._proc.stdin.write(raw.encode())
        await self._proc.stdin.drain()
        return await asyncio.wait_for(fut, timeout=30)

    async def _read_loop(self) -> None:
        assert self._proc and self._proc.stdout
        while True:
            try:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                msg = json.loads(line)
                req_id = msg.get("id")
                if req_id and req_id in self._pending:
                    self._pending.pop(req_id).set_result(msg)
            except (json.JSONDecodeError, asyncio.CancelledError):
                break
            except Exception as exc:
                log.error("MCP read error: %s", exc)


# ─────────────────────────────────────────────
# MCP Client
# ─────────────────────────────────────────────

class MCPClient:
    """
    High-level MCP client.
    Usage:
        async with MCPClient.stdio(["npx", "-y", "@modelcontextprotocol/server-filesystem",
                                    str(PROJECT_ROOT)]) as client:
            tools = await client.list_tools()
            result = await client.call_tool("read_file", {"path": "src/librarian.py"})
    """

    def __init__(self, transport: MCPTransport) -> None:
        self._t = transport
        self._tools: list[MCPTool] = []

    @classmethod
    def stdio(cls, command: list[str]) -> "MCPClient":
        return cls(MCPTransport(command))

    async def __aenter__(self) -> "MCPClient":
        await self._t.start()
        await self._initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._t.stop()

    async def _initialize(self) -> None:
        resp = await self._t.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "jarvis-4.0", "version": "4.0.0"},
        })
        log.info("MCP initialized: %s", resp.get("result", {}).get("serverInfo", {}))
        await self._t.send("notifications/initialized")

    async def list_tools(self) -> list[MCPTool]:
        resp = await self._t.send("tools/list")
        tools_raw = resp.get("result", {}).get("tools", [])
        self._tools = [
            MCPTool(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
            )
            for t in tools_raw
        ]
        log.info("MCP tools available: %s", [t.name for t in self._tools])
        return self._tools

    async def call_tool(self, tool_name: str, arguments: dict) -> MCPCallResult:
        log.info("MCP call_tool: %s %s", tool_name, list(arguments.keys()))
        resp = await self._t.send("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        if "error" in resp:
            return MCPCallResult(
                tool=tool_name, success=False,
                error=resp["error"].get("message", "Unknown error"),
            )
        content = resp.get("result", {}).get("content", [])
        return MCPCallResult(tool=tool_name, success=True, content=content)


# ─────────────────────────────────────────────
# AWP-042: Filesystem MCP Server helper
# ─────────────────────────────────────────────

class JarvisFilesystemMCP:
    """
    Wraps the official @modelcontextprotocol/server-filesystem npm package.
    Provides safe file operations scoped to PROJECT_ROOT.
    Requires: npm / npx available in PATH.

    Security:
      - All paths are validated against PROJECT_ROOT before call.
      - Write operations require explicit allow_write=True.
    """

    SERVER_CMD = ["npx", "-y", "@modelcontextprotocol/server-filesystem"]

    def __init__(self, root: Path = PROJECT_ROOT, allow_write: bool = False) -> None:
        self._root = root.resolve()
        self._allow_write = allow_write
        self._client = MCPClient.stdio(self.SERVER_CMD + [str(self._root)])

    async def __aenter__(self) -> "JarvisFilesystemMCP":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.__aexit__(*args)

    def _guard(self, path: str) -> str:
        resolved = (self._root / path).resolve()
        if not str(resolved).startswith(str(self._root)):
            raise PermissionError(f"Path traversal blocked: {path!r}")
        return str(resolved)

    async def read_file(self, path: str) -> str:
        self._guard(path)
        result = await self._client.call_tool("read_file", {"path": self._guard(path)})
        if not result.success:
            raise OSError(f"MCP read_file failed: {result.error}")
        return result.text

    async def write_file(self, path: str, content: str) -> None:
        if not self._allow_write:
            raise PermissionError("write_file requires allow_write=True")
        self._guard(path)
        result = await self._client.call_tool(
            "write_file", {"path": self._guard(path), "content": content}
        )
        if not result.success:
            raise OSError(f"MCP write_file failed: {result.error}")

    async def list_directory(self, path: str = ".") -> list[str]:
        self._guard(path)
        result = await self._client.call_tool(
            "list_directory", {"path": self._guard(path)}
        )
        if not result.success:
            raise OSError(result.error)
        return result.text.splitlines()

    async def search_files(self, pattern: str, path: str = ".") -> list[str]:
        self._guard(path)
        result = await self._client.call_tool(
            "search_files", {"path": self._guard(path), "pattern": pattern}
        )
        return result.text.splitlines() if result.success else []
