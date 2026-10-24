"""
Asynchronous Model Context Protocol (MCP) Client over Stdio and HTTP transports.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from harness.mcp.protocol import (
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
    MCPCallToolResult,
    MCPContentItem,
    MCPToolDefinition,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for interacting with any Model Context Protocol (MCP) server.
    Handles process lifecycle, JSON-RPC message framing, asynchronous dispatch,
    tool discovery, and tool execution.
    """

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        server_name: str = "mcp_server",
    ):
        self.command = command
        self.args = args or []
        self.env = env
        self.cwd = cwd
        self.server_name = server_name

        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._pending_requests: Dict[int | str, asyncio.Future[JSONRPCResponse]] = {}
        self._read_task: Optional[asyncio.Task[None]] = None
        self._is_initialized = False
        self._tools: Dict[str, MCPToolDefinition] = {}

    @property
    def is_connected(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def connect(self) -> None:
        """Start server process and establish stdio transport."""
        cmd = [self.command, *self.args]
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
            cwd=self.cwd,
        )

        self._read_task = asyncio.create_task(self._reader_loop())
        await self._initialize_handshake()

    async def _initialize_handshake(self) -> None:
        """Perform MCP initialize handshake and send notifications/initialized."""
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {},
            },
            "clientInfo": {
                "name": "NexusCUH-MCP-Client",
                "version": "0.1.0",
            },
        }

        resp = await self._send_request("initialize", init_params)
        if resp.error:
            raise RuntimeError(f"MCP Initialize failed for {self.server_name}: {resp.error.message}")

        # Send notifications/initialized
        await self._send_notification("notifications/initialized", {})
        self._is_initialized = True

        # Pre-fetch tools
        await self.refresh_tools()

    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> JSONRPCResponse:
        """Send a JSON-RPC request and wait for the response."""
        if not self.is_connected or not self._process or not self._process.stdin:
            raise ConnectionError(f"MCP server '{self.server_name}' is not connected.")

        self._request_id += 1
        req_id = self._request_id

        req = JSONRPCRequest(id=req_id, method=method, params=params or {})
        payload = req.model_dump_json() + "\n"

        loop = asyncio.get_running_loop()
        future: asyncio.Future[JSONRPCResponse] = loop.create_future()
        self._pending_requests[req_id] = future

        self._process.stdin.write(payload.encode("utf-8"))
        await self._process.stdin.drain()

        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError as err:
            self._pending_requests.pop(req_id, None)
            raise TimeoutError(f"MCP Request '{method}' timed out after 30s.") from err

    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a JSON-RPC notification."""
        if not self.is_connected or not self._process or not self._process.stdin:
            return

        notif = JSONRPCNotification(method=method, params=params or {})
        payload = notif.model_dump_json() + "\n"
        self._process.stdin.write(payload.encode("utf-8"))
        await self._process.stdin.drain()

    async def _reader_loop(self) -> None:
        """Continuously read lines from server stdout."""
        if not self._process or not self._process.stdout:
            return

        while True:
            try:
                line = await self._process.stdout.readline()
                if not line:
                    break

                text = line.decode("utf-8").strip()
                if not text:
                    continue

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    continue

                if "id" in data and data["id"] is not None:
                    req_id = data["id"]
                    future = self._pending_requests.pop(req_id, None)
                    if future and not future.done():
                        resp = JSONRPCResponse.model_validate(data)
                        future.set_result(resp)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error in MCP reader loop for {self.server_name}: {exc}")
                break

    async def refresh_tools(self) -> List[MCPToolDefinition]:
        """Fetch list of tools from the MCP server."""
        resp = await self._send_request("tools/list", {})
        if resp.error:
            raise RuntimeError(f"Failed to list tools from {self.server_name}: {resp.error.message}")

        tools_data = resp.result.get("tools", []) if resp.result else []
        self._tools.clear()
        for t in tools_data:
            tool_def = MCPToolDefinition.model_validate(t)
            self._tools[tool_def.name] = tool_def

        return list(self._tools.values())

    def get_cached_tools(self) -> List[MCPToolDefinition]:
        return list(self._tools.values())

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """Execute a tool exposed by the MCP server."""
        params = {"name": name, "arguments": arguments}
        resp = await self._send_request("tools/call", params)

        if resp.error:
            return MCPCallToolResult(
                content=[MCPContentItem(type="text", text=f"MCP Error [{resp.error.code}]: {resp.error.message}")],
                isError=True,
            )

        if not resp.result:
            return MCPCallToolResult(content=[], isError=False)

        return MCPCallToolResult.model_validate(resp.result)

    async def disconnect(self) -> None:
        """Terminate the server process cleanly."""
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()

        if self._process:
            try:
                if self._process.stdin:
                    self._process.stdin.close()
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=2.0)
            except Exception:
                if self._process:
                    self._process.kill()

        self._process = None
        self._is_initialized = False
