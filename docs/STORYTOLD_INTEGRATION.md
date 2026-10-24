# StoryTold Software Ecosystem & MCP Integration Guide

This guide explains how NexusCUH interfaces directly with [StoryTold](https://github.com/storytold/) applications and other software exposing Model Context Protocol (MCP) endpoints.

---

## 1. What is StoryTold?

StoryTold is an ecosystem of creative and desktop applications designed with native AI agent interoperability:
- **WordCraft**: Document editor with structured AST manipulation and rendering parity verification.
- **DeckCraft**: Slide presentation design engine.
- **ArtCraft**: Generative visual and graphic design suite.
- **SheetCraft**: Data analysis and spreadsheet automation.

Rather than forcing AI agents to guess coordinates on screen, StoryTold applications provide a **Model Context Protocol (MCP)** server that exposes high-fidelity tools over JSON-RPC 2.0.

---

## 2. The WordCraft MCP Tool Contract

NexusCUH includes a native standalone WordCraft MCP server (`harness/mcp/servers/wordcraft_server.py`) exposing the full tool suite:

| Tool Name | Parameters | Purpose |
|:---|:---|:---|
| `wordcraft__new_document` | `title: string` | Creates a new blank document with a designated title. |
| `wordcraft__open_document` | `path: string` | Loads an existing document from the sandbox workspace. |
| `wordcraft__save_document` | `path: string` | Flushes document paragraphs to disk. |
| `wordcraft__type_text` | `text: string, paragraph_type: string` | Appends a heading or paragraph node into the document AST. |
| `wordcraft__get_text` | None | Retrieves all plain text content across paragraphs. |
| `wordcraft__inspect_document` | None | Returns the full JSON Abstract Syntax Tree (AST). |
| `wordcraft__render_page` | `page_index: int` | Renders a high-resolution raster image preview of the page. |
| `wordcraft__parity` | None | Validates layout and rendering parity with the document AST. |
| `wordcraft__ui_inspect` | None | Inspects active window title, toolbar bounds, and focused widgets. |

---

## 3. High-Level Python API: `StoryToldAppClient`

For programmatic workflows, NexusCUH provides the `StoryToldAppClient` helper:

```python
import asyncio
from harness.mcp.client import MCPClient
from harness.mcp.storytold import StoryToldAppClient

async def main():
    client = MCPClient(
        command="python3",
        args=["harness/mcp/servers/wordcraft_server.py"],
        server_name="wordcraft"
    )
    await client.connect()

    app = StoryToldAppClient(client)

    # Create formatted document in one call
    res = await app.create_formatted_document(
        title="Q3 Engineering Architecture Memo",
        sections=[
            {"heading": "Executive Summary", "content": "NexusCUH orchestrates MCP, shell, and GUI."},
            {"heading": "Reliability Specs", "content": "Validated with multi-modal ground-truth assertions."}
        ],
        save_path="docs/architecture_memo.txt"
    )

    print("Document Saved:", res["path"])

    # Verify rendering parity
    parity_ok = await app.verify_visual_parity()
    print("Visual Parity Verified:", parity_ok)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Why MCP is the Future of Computer Use

| Feature | Naive Vision Computer Use | StoryTold MCP Integration |
|:---|:---|:---|
| **Latency** | 3.5 – 6.0 seconds / click | 10 – 25 milliseconds / call |
| **Visual Tokens** | 1,600 tokens / step | 0 tokens (pure JSON-RPC) |
| **Accuracy** | Prone to missed clicks and coordinate drift | 100% deterministic |
| **State Inspection** | Inferred from pixels | Direct AST query |
| **Failure Recovery** | Hard to diagnose visually | Structured JSON error codes |
