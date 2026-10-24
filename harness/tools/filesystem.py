"""
FileSystem tool for direct, structured file manipulation without shell overhead.
"""

from __future__ import annotations

import hashlib
from typing import Any

from harness.sandbox.base import BaseSandbox
from harness.tools.base import BaseTool, ToolResult


class FileSystemTool(BaseTool):
    """
    Direct file operations in the sandbox: read, write, append, search, and patch.
    Guarantees atomic file updates without shell character-escaping hazards.
    """

    name = "filesystem"
    description = (
        "Perform structured file operations inside the sandbox. Actions include: "
        "'read', 'write', 'append', 'str_replace', 'exists', and 'checksum'."
    )

    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "append", "str_replace", "exists", "checksum"],
                "description": "File operation to perform.",
            },
            "path": {
                "type": "string",
                "description": "Target file path inside the sandbox.",
            },
            "content": {
                "type": "string",
                "description": "Text content to write or append.",
            },
            "old_str": {
                "type": "string",
                "description": "Existing substring to replace (for 'str_replace' action).",
            },
            "new_str": {
                "type": "string",
                "description": "New replacement substring (for 'str_replace' action).",
            },
        },
        "required": ["action", "path"],
    }

    def __init__(self, sandbox: BaseSandbox):
        self.sandbox = sandbox

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action")
        path = kwargs.get("path", "").strip()
        content = kwargs.get("content", "")
        old_str = kwargs.get("old_str")
        new_str = kwargs.get("new_str")

        if not path:
            return ToolResult(content="Error: Path cannot be empty.", is_error=True)

        try:
            if action == "read":
                if not self.sandbox.file_exists(path):
                    return ToolResult(content=f"Error: File '{path}' does not exist.", is_error=True)
                data = self.sandbox.read_file(path)
                return ToolResult(content=data, is_error=False, metadata={"size": len(data)})

            elif action == "write":
                self.sandbox.write_file(path, content)
                return ToolResult(
                    content=f"Successfully wrote {len(content)} characters to '{path}'.",
                    is_error=False,
                    metadata={"bytes_written": len(content.encode("utf-8"))},
                )

            elif action == "append":
                existing = self.sandbox.read_file(path) if self.sandbox.file_exists(path) else ""
                updated = existing + content
                self.sandbox.write_file(path, updated)
                return ToolResult(
                    content=f"Successfully appended {len(content)} characters to '{path}'.",
                    is_error=False,
                )

            elif action == "str_replace":
                if not self.sandbox.file_exists(path):
                    return ToolResult(content=f"Error: File '{path}' does not exist.", is_error=True)
                if old_str is None or new_str is None:
                    return ToolResult(content="Error: 'old_str' and 'new_str' are required for str_replace.", is_error=True)

                existing = self.sandbox.read_file(path)
                if old_str not in existing:
                    return ToolResult(content=f"Error: Target text '{old_str[:50]}...' not found in '{path}'.", is_error=True)

                updated = existing.replace(old_str, new_str, 1)
                self.sandbox.write_file(path, updated)
                return ToolResult(
                    content=f"Successfully replaced occurrence in '{path}'.",
                    is_error=False,
                )

            elif action == "exists":
                exists = self.sandbox.file_exists(path)
                return ToolResult(content="true" if exists else "false", is_error=False, metadata={"exists": exists})

            elif action == "checksum":
                if not self.sandbox.file_exists(path):
                    return ToolResult(content=f"Error: File '{path}' does not exist.", is_error=True)
                raw_bytes = self.sandbox.read_file_bytes(path)
                sha256 = hashlib.sha256(raw_bytes).hexdigest()
                return ToolResult(content=sha256, is_error=False, metadata={"sha256": sha256})

            else:
                return ToolResult(content=f"Error: Unknown action '{action}'.", is_error=True)

        except Exception as exc:
            return ToolResult(content=f"FileSystem error: {str(exc)}", is_error=True)
