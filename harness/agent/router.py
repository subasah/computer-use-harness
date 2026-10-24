"""
Cognitive Tool Router for Computer Use Agents.
"""

from __future__ import annotations

from typing import List

from harness.tools.base import BaseTool


class CognitiveToolRouter:
    """
    Intelligent routing heuristic that categorizes available tools by interface type
    (MCP, Shell, GUI, FileSystem) and guides agent tool selection for optimal speed,
    cost efficiency, and deterministic reliability.
    """

    INTERFACE_PRIORITY = {
        "mcp": 1,         # Fast, deterministic, zero visual token cost
        "filesystem": 2,  # Direct file I/O, no shell quoting escapes
        "shell": 3,       # High flexibility, batch processing, CLI utilities
        "computer": 4,    # Visual GUI, essential for UI navigation but highest token cost
    }

    def __init__(self, tools: List[BaseTool]):
        self.tools = {t.name: t for t in tools}

    def categorize_tool(self, tool_name: str) -> str:
        """Classify a tool into its interaction category."""
        if "__" in tool_name:
            return "mcp"
        if tool_name == "filesystem":
            return "filesystem"
        if tool_name == "shell":
            return "shell"
        if tool_name == "computer":
            return "computer"
        return "other"

    def get_tool_routing_guidance(self) -> str:
        """
        Produce clear system guidance on when to prefer each interface type
        to enforce optimal harness engineering trade-offs.
        """
        return (
            "TOOL SELECTION POLICY & HIERARCHY:\n"
            "1. MCP TOOLS (e.g. wordcraft__*, filesystem__*): Always prefer MCP tools when available "
            "for application and document operations. They execute deterministically via API without visual hallucination.\n"
            "2. DIRECT FILESYSTEM TOOLS: Use 'filesystem' for reading, writing, and atomic edits of files.\n"
            "3. SHELL TOOLS: Use 'shell' for batch commands, scripts, builds, searches (grep/find), and process inspection.\n"
            "4. GUI / COMPUTER TOOLS: Use 'computer' (screenshot, click, type) ONLY when interacting with GUI applications "
            "that lack CLI/MCP endpoints, or to visually verify the rendered output on screen."
        )

    def filter_tools_for_mode(self, mode: str) -> List[BaseTool]:
        """Filter tools for specific evaluation modes (e.g., 'shell_only', 'gui_only', 'mcp_only', 'all')."""
        if mode == "all":
            return list(self.tools.values())

        filtered = []
        for name, tool in self.tools.items():
            cat = self.categorize_tool(name)
            if mode == "shell_only" and cat in ("shell", "filesystem"):
                filtered.append(tool)
            elif mode == "gui_only" and cat == "computer":
                filtered.append(tool)
            elif mode == "mcp_only" and cat == "mcp":
                filtered.append(tool)
            elif mode == "hybrid" and cat in ("mcp", "shell", "filesystem", "computer"):
                filtered.append(tool)

        return filtered or list(self.tools.values())
