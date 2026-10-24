"""
Standard Model Context Protocol (MCP) Server for Filesystem operations.
Provides read, write, list_directory, and directory search tools over stdio.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def get_tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "read_file",
            "description": "Read complete text content of a file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"}
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Create or overwrite a file with given text content.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Text content"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "list_directory",
            "description": "List files and directories in a target directory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path", "default": "."}
                },
            },
        },
    ]


def handle_call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name == "read_file":
            path = Path(args["path"])
            if not path.exists():
                return {"content": [{"type": "text", "text": f"Error: File '{path}' not found"}], "isError": True}
            content = path.read_text(encoding="utf-8")
            return {"content": [{"type": "text", "text": content}], "isError": False}

        elif name == "write_file":
            path = Path(args["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["content"], encoding="utf-8")
            return {
                "content": [{"type": "text", "text": f"Successfully wrote {len(args['content'])} characters."}],
                "isError": False,
            }

        elif name == "list_directory":
            target = Path(args.get("path", "."))
            if not target.exists():
                return {"content": [{"type": "text", "text": f"Error: Directory '{target}' not found"}], "isError": True}
            entries = []
            for item in target.iterdir():
                entries.append({"name": item.name, "is_dir": item.is_dir(), "size": item.stat().st_size if item.is_file() else 0})
            return {"content": [{"type": "text", "text": json.dumps(entries, indent=2)}], "isError": False}

        else:
            return {"content": [{"type": "text", "text": f"Error: Unknown tool '{name}'"}], "isError": True}

    except Exception as exc:
        return {"content": [{"type": "text", "text": f"Error: {str(exc)}"}], "isError": True}


def run_stdio_server() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "Filesystem-MCP", "version": "1.0.0"},
                },
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": get_tool_definitions()},
            }
        elif method == "tools/call":
            call_res = handle_call_tool(params.get("name", ""), params.get("arguments", {}))
            resp = {"jsonrpc": "2.0", "id": req_id, "result": call_res}
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"},
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
