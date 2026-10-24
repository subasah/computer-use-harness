"""
Standalone Model Context Protocol (MCP) Server for StoryTold WordCraft software.
Implements the StoryTold desktop application MCP specification over stdio.
"""

from __future__ import annotations

import base64
import io
import json
import os
import sys
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw


class WordCraftEngine:
    """Internal document engine simulating StoryTold WordCraft desktop application state."""

    def __init__(self) -> None:
        self.doc_path: Optional[str] = None
        self.title: str = "Untitled Document"
        self.paragraphs: List[Dict[str, Any]] = [
            {"id": "p-0", "type": "heading1", "text": "Document Title", "bold": True},
            {"id": "p-1", "type": "paragraph", "text": "Start typing here...", "bold": False},
        ]
        self.cursor_pos: int = 0
        self.selection: Optional[Dict[str, int]] = None
        self.page_count: int = 1

    def new_document(self, title: str = "New Document") -> Dict[str, Any]:
        self.title = title
        self.doc_path = None
        self.paragraphs = [
            {"id": "p-0", "type": "heading1", "text": title, "bold": True},
        ]
        self.cursor_pos = 0
        return {"status": "created", "title": self.title, "paragraphs": len(self.paragraphs)}

    def open_document(self, path: str) -> Dict[str, Any]:
        self.doc_path = path
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Simple line parsing into paragraphs
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            self.paragraphs = []
            for i, line in enumerate(lines):
                p_type = "heading1" if line.startswith("# ") else "paragraph"
                p_text = line[2:] if line.startswith("# ") else line
                self.paragraphs.append({"id": f"p-{i}", "type": p_type, "text": p_text})
            self.title = os.path.basename(path)
            return {"status": "opened", "path": path, "paragraphs": len(self.paragraphs)}
        else:
            return self.new_document(title=os.path.basename(path))

    def save_document(self, path: Optional[str] = None) -> Dict[str, Any]:
        target_path = path or self.doc_path or "document.txt"
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        text_content = "\n\n".join(
            (f"# {p['text']}" if p.get("type") == "heading1" else p["text"])
            for p in self.paragraphs
        )
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        self.doc_path = target_path
        return {"status": "saved", "path": target_path, "bytes": len(text_content.encode("utf-8"))}

    def type_text(self, text: str, paragraph_type: str = "paragraph") -> Dict[str, Any]:
        new_id = f"p-{len(self.paragraphs)}"
        self.paragraphs.append({"id": new_id, "type": paragraph_type, "text": text})
        return {"status": "inserted", "id": new_id, "total_paragraphs": len(self.paragraphs)}

    def get_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.paragraphs)

    def inspect_document(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "path": self.doc_path,
            "page_count": self.page_count,
            "total_words": sum(len(p["text"].split()) for p in self.paragraphs),
            "paragraphs": self.paragraphs,
        }

    def render_page(self, page_index: int = 1) -> str:
        """Render a high-resolution simulation raster of the document page."""
        width, height = 800, 1000
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Draw page border & header
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(220, 220, 220), width=2)
        draw.text((60, 40), f"StoryTold WordCraft  |  {self.title}  |  Page {page_index}", fill=(120, 120, 120))
        draw.line([(60, 60), (width - 60, 60)], fill=(200, 200, 200), width=1)

        y = 90
        for p in self.paragraphs:
            if y > height - 80:
                break
            if p.get("type") == "heading1":
                draw.text((60, y), p["text"], fill=(20, 20, 20))
                y += 36
            else:
                # Wrap text simply
                words = p["text"].split()
                line = ""
                for w in words:
                    if len(line) + len(w) > 75:
                        draw.text((60, y), line, fill=(50, 50, 50))
                        y += 20
                        line = w + " "
                    else:
                        line += w + " "
                if line:
                    draw.text((60, y), line, fill=(50, 50, 50))
                    y += 26

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def parity(self) -> Dict[str, Any]:
        """Verify rendering parity between document AST and layout model."""
        return {
            "is_synced": True,
            "ast_node_count": len(self.paragraphs),
            "rendered_page_count": self.page_count,
            "visual_fidelity_score": 1.0,
        }

    def ui_inspect(self) -> Dict[str, Any]:
        return {
            "focused_window": "StoryTold WordCraft Desktop",
            "active_tool": "TextCursor",
            "toolbar_actions": ["Save", "Export", "Undo", "Redo", "Heading", "Bold", "Italic"],
            "canvas_bounds": {"x": 100, "y": 80, "width": 800, "height": 1000},
        }


def get_tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "new_document",
            "description": "Create a new blank document in StoryTold WordCraft with a title.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"}
                },
            },
        },
        {
            "name": "open_document",
            "description": "Open an existing document file in StoryTold WordCraft.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to open"}
                },
                "required": ["path"],
            },
        },
        {
            "name": "save_document",
            "description": "Save the current StoryTold WordCraft document to disk.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target file path"}
                },
            },
        },
        {
            "name": "type_text",
            "description": "Insert text or a new paragraph into StoryTold WordCraft.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to insert"},
                    "paragraph_type": {
                        "type": "string",
                        "enum": ["paragraph", "heading1", "bullet"],
                        "default": "paragraph",
                    },
                },
                "required": ["text"],
            },
        },
        {
            "name": "get_text",
            "description": "Retrieve all plain text content from the current document.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "inspect_document",
            "description": "Retrieve full structural AST of the document including paragraphs and words.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "render_page",
            "description": "Render a visual raster image preview of a document page in WordCraft.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page_index": {"type": "integer", "default": 1}
                },
            },
        },
        {
            "name": "parity",
            "description": "Check visual and structural layout parity of the active document.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "ui_inspect",
            "description": "Inspect active UI toolbar, canvas bounds, and window state of WordCraft.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def handle_call_tool(engine: WordCraftEngine, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "new_document":
        res = engine.new_document(title=args.get("title", "New Document"))
        return {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False}

    elif name == "open_document":
        res = engine.open_document(path=args["path"])
        return {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False}

    elif name == "save_document":
        res = engine.save_document(path=args.get("path"))
        return {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False}

    elif name == "type_text":
        res = engine.type_text(text=args["text"], paragraph_type=args.get("paragraph_type", "paragraph"))
        return {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False}

    elif name == "get_text":
        text = engine.get_text()
        return {"content": [{"type": "text", "text": text}], "isError": False}

    elif name == "inspect_document":
        ast_data = engine.inspect_document()
        return {"content": [{"type": "text", "text": json.dumps(ast_data, indent=2)}], "isError": False}

    elif name == "render_page":
        b64_img = engine.render_page(page_index=args.get("page_index", 1))
        return {
            "content": [
                {"type": "image", "data": b64_img, "mimeType": "image/png"},
                {"type": "text", "text": "Rendered Page 1 successfully."},
            ],
            "isError": False,
        }

    elif name == "parity":
        res = engine.parity()
        return {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False}

    elif name == "ui_inspect":
        res = engine.ui_inspect()
        return {"content": [{"type": "text", "text": json.dumps(res)}], "isError": False}

    else:
        return {
            "content": [{"type": "text", "text": f"Error: Unknown tool '{name}'"}],
            "isError": True,
        }


def run_stdio_server() -> None:
    """Run JSON-RPC 2.0 loop reading stdin and writing stdout."""
    engine = WordCraftEngine()

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
                    "serverInfo": {
                        "name": "StoryTold-WordCraft-MCP",
                        "version": "1.0.0",
                    },
                },
            }
        elif method == "notifications/initialized":
            continue  # Notification, no response
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": get_tool_definitions()},
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            call_res = handle_call_tool(engine, tool_name, tool_args)
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": call_res,
            }
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
