"""
High-Level Integration Layer for StoryTold Applications Ecosystem.
Provides specialized workflows for WordCraft, DeckCraft, and ArtCraft via MCP.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from harness.mcp.client import MCPClient


class StoryToldAppClient:
    """
    Dedicated client wrapper providing ergonomic Pythonic APIs
    for StoryTold desktop and creative applications connected via MCP.
    """

    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client

    async def create_formatted_document(
        self,
        title: str,
        sections: List[Dict[str, str]],
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrate creation of a rich formatted document in WordCraft.
        Each section has 'heading' and 'content'.
        """
        await self.mcp.call_tool("new_document", {"title": title})

        for sec in sections:
            if "heading" in sec:
                await self.mcp.call_tool(
                    "type_text",
                    {"text": sec["heading"], "paragraph_type": "heading1"},
                )
            if "content" in sec:
                await self.mcp.call_tool(
                    "type_text",
                    {"text": sec["content"], "paragraph_type": "paragraph"},
                )

        if save_path:
            save_res = await self.mcp.call_tool("save_document", {"path": save_path})
            return json.loads(save_res.content[0].text or "{}")

        ast_res = await self.mcp.call_tool("inspect_document", {})
        return json.loads(ast_res.content[0].text or "{}")

    async def verify_visual_parity(self) -> bool:
        """Verify layout and visual rendering parity with underlying document AST."""
        res = await self.mcp.call_tool("parity", {})
        if res.content and res.content[0].text:
            data = json.loads(res.content[0].text)
            return bool(data.get("is_synced", False))
        return False
