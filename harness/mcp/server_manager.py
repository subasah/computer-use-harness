"""
Multi-server Model Context Protocol (MCP) Manager and Agent Tool Wrapper.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.config import MCPConfig
from harness.mcp.client import MCPClient
from harness.mcp.protocol import MCPToolDefinition
from harness.tools.base import BaseTool, ToolResult


class MCPToolWrapper(BaseTool):
    """Wraps an individual tool from an MCP server as a native agent BaseTool."""

    def __init__(
        self,
        server_name: str,
        tool_def: MCPToolDefinition,
        client: MCPClient,
    ):
        self.server_name = server_name
        self.original_name = tool_def.name
        self.name = f"{server_name}__{tool_def.name}"
        self.description = f"[{server_name.upper()}] {tool_def.description or ''}"
        self.parameters_schema = tool_def.inputSchema
        self.client = client

    async def execute(self, **kwargs: Any) -> ToolResult:
        result = await self.client.call_tool(self.original_name, kwargs)

        text_parts: List[str] = []
        image_bytes: Optional[bytes] = None

        for item in result.content:
            if item.type == "text" and item.text:
                text_parts.append(item.text)
            elif item.type == "image" and item.data:
                try:
                    image_bytes = base64.b64decode(item.data)
                except Exception:
                    pass

        joined_text = "\n".join(text_parts) if text_parts else ("Success" if not result.isError else "Error")

        return ToolResult(
            content=joined_text,
            image_bytes=image_bytes,
            is_error=result.isError,
            metadata={"server": self.server_name, "tool": self.original_name},
        )


class MCPServerManager:
    """
    Orchestrates multiple MCP servers, launches their processes, registers
    their tools dynamically, and routes agent calls to the appropriate server.
    """

    def __init__(self, config: MCPConfig, workspace_dir: Optional[str | Path] = None):
        self.config = config
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else None
        self.clients: Dict[str, MCPClient] = {}
        self.wrapped_tools: Dict[str, MCPToolWrapper] = {}

    async def start_all(self) -> None:
        """Start all configured MCP servers."""
        python_exe = sys.executable
        cwd_str = str(self.workspace_dir) if self.workspace_dir else None

        # 1. StoryTold WordCraft MCP Server
        if self.config.storytold_enabled:
            server_script = str(Path(__file__).parent / "servers" / "wordcraft_server.py")
            client = MCPClient(
                command=python_exe,
                args=[server_script],
                cwd=cwd_str,
                server_name="wordcraft",
            )
            await client.connect()
            self.clients["wordcraft"] = client

        # 2. Filesystem MCP Server
        if self.config.filesystem_enabled:
            fs_script = str(Path(__file__).parent / "servers" / "filesystem_server.py")
            client = MCPClient(
                command=python_exe,
                args=[fs_script],
                cwd=cwd_str,
                server_name="filesystem",
            )
            await client.connect()
            self.clients["filesystem"] = client

        # 3. Custom user-defined servers
        for name, spec in self.config.custom_servers.items():
            cmd = spec.get("command", "")
            args = spec.get("args", [])
            client = MCPClient(
                command=cmd,
                args=args,
                env=spec.get("env"),
                cwd=spec.get("cwd"),
                server_name=name,
            )
            await client.connect()
            self.clients[name] = client

        # Wrap all discovered tools
        await self._register_all_tools()

    async def _register_all_tools(self) -> None:
        self.wrapped_tools.clear()
        for server_name, client in self.clients.items():
            tools = client.get_cached_tools()
            for tool_def in tools:
                wrapper = MCPToolWrapper(server_name, tool_def, client)
                self.wrapped_tools[wrapper.name] = wrapper

    def get_agent_tools(self) -> List[BaseTool]:
        """Return list of native BaseTools exposed by all MCP servers."""
        return list(self.wrapped_tools.values())

    async def stop_all(self) -> None:
        """Disconnect and terminate all running MCP servers."""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()
        self.wrapped_tools.clear()
