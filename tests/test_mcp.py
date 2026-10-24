"""
Unit tests for Model Context Protocol (MCP) Client, Server Manager, and StoryTold integration.
"""

import json
import sys
from pathlib import Path

import pytest

from harness.config import MCPConfig
from harness.mcp.client import MCPClient
from harness.mcp.server_manager import MCPServerManager
from harness.mcp.storytold import StoryToldAppClient


@pytest.mark.asyncio
async def test_mcp_client_wordcraft_stdio_roundtrip():
    python_exe = sys.executable
    server_script = str(Path(__file__).parent.parent / "harness" / "mcp" / "servers" / "wordcraft_server.py")

    client = MCPClient(
        command=python_exe,
        args=[server_script],
        server_name="wordcraft_test",
    )

    await client.connect()
    assert client.is_connected

    # Discover tools
    tools = client.get_cached_tools()
    tool_names = [t.name for t in tools]
    assert "new_document" in tool_names
    assert "type_text" in tool_names
    assert "inspect_document" in tool_names
    assert "parity" in tool_names

    # Call new_document
    res1 = await client.call_tool("new_document", {"title": "Test MCP Spec"})
    assert not res1.isError
    res1_data = json.loads(res1.content[0].text or "{}")
    assert res1_data["title"] == "Test MCP Spec"

    # Call type_text
    res2 = await client.call_tool(
        "type_text",
        {"text": "Harness Engineering with MCP works seamlessly.", "paragraph_type": "paragraph"},
    )
    assert not res2.isError

    # Inspect document AST
    res3 = await client.call_tool("inspect_document", {})
    assert not res3.isError
    ast_data = json.loads(res3.content[0].text or "{}")
    assert ast_data["title"] == "Test MCP Spec"
    assert len(ast_data["paragraphs"]) >= 2

    # Verify parity
    res4 = await client.call_tool("parity", {})
    assert not res4.isError
    parity_data = json.loads(res4.content[0].text or "{}")
    assert parity_data["is_synced"] is True

    await client.disconnect()
    assert not client.is_connected


@pytest.mark.asyncio
async def test_mcp_server_manager_wrapping():
    config = MCPConfig(storytold_enabled=True, filesystem_enabled=True)
    manager = MCPServerManager(config)

    await manager.start_all()
    tools = manager.get_agent_tools()
    tool_names = [t.name for t in tools]

    assert "wordcraft__new_document" in tool_names
    assert "wordcraft__save_document" in tool_names
    assert "filesystem__read_file" in tool_names

    # Test executing wrapped tool
    wc_tool = manager.wrapped_tools["wordcraft__new_document"]
    tool_res = await wc_tool.execute(title="Wrapped Document")
    assert not tool_res.is_error
    assert "Wrapped Document" in tool_res.content

    await manager.stop_all()


@pytest.mark.asyncio
async def test_storytold_high_level_client():
    python_exe = sys.executable
    server_script = str(Path(__file__).parent.parent / "harness" / "mcp" / "servers" / "wordcraft_server.py")

    client = MCPClient(command=python_exe, args=[server_script], server_name="wordcraft_hl")
    await client.connect()

    app = StoryToldAppClient(client)
    res = await app.create_formatted_document(
        title="Architecture Overview",
        sections=[
            {"heading": "Section 1", "content": "Paragraph content 1"},
            {"heading": "Section 2", "content": "Paragraph content 2"},
        ],
    )

    assert res["title"] == "Architecture Overview"
    assert len(res["paragraphs"]) >= 4

    parity_ok = await app.verify_visual_parity()
    assert parity_ok is True

    await client.disconnect()
