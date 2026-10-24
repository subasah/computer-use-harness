"""
Benchmark Task: StoryTold WordCraft Document Authoring via MCP Server.
"""

from __future__ import annotations

import json
from typing import List

from harness.sandbox.base import BaseSandbox
from harness.verification.assertions import (
    BaseAssertion,
    FileContentRegexAssertion,
    FileExistsAssertion,
    MCPStateAssertion,
)


class WordCraftDocumentTask:
    name = "task_02_wordcraft_mcp_workflow"
    category = "mcp_desktop_software"
    instruction = (
        "Using the StoryTold WordCraft MCP tools, create a new document titled 'Q3 Engineering Architecture Memo'. "
        "Insert a section with heading 'Executive Summary' and paragraph 'NexusCUH delivers hybrid shell, GUI, and MCP orchestration.'. "
        "Then insert another section with heading 'Reliability Specs' and paragraph 'Verified with ground-truth assertions.'. "
        "Save the document to 'docs/architecture_memo.txt' and verify parity."
    )

    def setup(self, sandbox: BaseSandbox) -> None:
        sandbox.exec_command("mkdir -p docs")

    def get_assertions(self) -> List[BaseAssertion]:
        def validate_ast(ast_json_str: str) -> tuple[bool, str]:
            try:
                data = json.loads(ast_json_str)
                paragraphs = data.get("paragraphs", [])
                if len(paragraphs) >= 3:
                    return True, f"Found {len(paragraphs)} paragraphs in document AST."
                return False, f"Expected at least 3 paragraphs, found {len(paragraphs)}."
            except Exception as e:
                return False, f"Failed to parse AST JSON: {e}"

        return [
            FileExistsAssertion("docs/architecture_memo.txt"),
            FileContentRegexAssertion(
                "docs/architecture_memo.txt",
                r"Q3 Engineering Architecture Memo",
                description="Contains memo title",
            ),
            FileContentRegexAssertion(
                "docs/architecture_memo.txt",
                r"Executive Summary",
                description="Contains executive summary heading",
            ),
            MCPStateAssertion(
                server_name="wordcraft",
                tool_name="inspect_document",
                tool_args={},
                validator_fn=validate_ast,
            ),
        ]
