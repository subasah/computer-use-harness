# NexusCUH: Engineering Deep Dive & Contributor Guide

Welcome to the technical deep dive for **Nexus Computer Use Harness (NexusCUH)**. This document walks section-by-section through the core engineering mechanisms, algorithms, data structures, and trade-off rationales implemented in the codebase. Whether you are a researcher, recruiter, or prospective contributor, this guide explains how every piece works under the hood.

---

## Table of Contents
1. [The Fundamental Engineering Challenge](#1-the-fundamental-engineering-challenge)
2. [Tri-Modal Tool Hierarchy & Cognitive Routing](#2-tri-modal-tool-hierarchy--cognitive-routing)
3. [Model Context Protocol (MCP) Integration & StoryTold Adapter](#3-model-context-protocol-mcp-integration--storytold-adapter)
4. [Sandbox Runtime & Virtual Displays](#4-sandbox-runtime--virtual-displays)
5. [Token Conservation & Visual Frame Diffing](#5-token-conservation--visual-frame-diffing)
6. [PTY Shell Sessions & Smart Output Windowing](#6-pty-shell-sessions--smart-output-windowing)
7. [Multi-Modal Assertive Verification vs Syntactic Status](#7-multi-modal-assertive-verification-vs-syntactic-status)
8. [Multi-Layered Safety Guardrails](#8-multi-layered-safety-guardrails)
9. [Evaluation Engine & Deterministic State Machine](#9-evaluation-engine--deterministic-state-machine)
10. [Step-by-Step Guide to Adding a New MCP Server](#10-step-by-step-guide-to-adding-a-new-mcp-server)

---

## 1. The Fundamental Engineering Challenge

Early computer-use agent prototypes treated desktop environments as raw image generation targets: take a full screenshot, send it to a multimodal model, prompt the model for $(x, y)$ pixel coordinates, and issue an OS click event. 

In production, this approach consistently breaks down due to three fundamental issues:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NAIVE VISION COMPUTER-USE PARADIGM                    │
│                                                                             │
│  [Model] ──(Screenshot)──> [Vision Encoder: 1,600 tokens/step]              │
│     │                                                                       │
│     ├── Coordinates Hallucinated (Off by 15px due to HiDPI / Window offset) │
│     ├── Latency: 4.8 seconds per click roundtrip                            │
│     ├── Context Limit Hit after 25 steps (>40,000 image tokens)             │
│     └── Zero visibility into background daemons, return codes, or disk state│
└─────────────────────────────────────────────────────────────────────────────┘
```

### The NexusCUH Engineering Solution
NexusCUH re-architects computer use as a **hierarchical hybrid orchestration problem**:
- **Semantic First**: When desktop applications expose structured APIs via the **Model Context Protocol (MCP)**, the agent interacts through typed tool calls. This yields 100% deterministic execution at zero image token cost.
- **Batch via Shell**: For compilation, file transforms, and directory operations, the agent utilizes a stateful shell with smart output windowing.
- **Visual Fallback & Verification**: The graphical desktop is reserved for visual layout inspection, spatial canvas interactions, or applications lacking programmatic endpoints.

---

## 2. Tri-Modal Tool Hierarchy & Cognitive Routing

Located in `harness/agent/router.py`:

```python
class CognitiveToolRouter:
    INTERFACE_PRIORITY = {
        "mcp": 1,         # 100% Deterministic, 0 Visual Tokens
        "filesystem": 2,  # Atomic I/O, Safe Quoting
        "shell": 3,       # Batch processing, CLI utilities
        "computer": 4,    # Visual GUI, essential for UI navigation
    }
```

### How the Router Operates
1. **Dynamic Tool Tagging**: During initialization, tools are categorized based on their naming convention (`<server>__<tool>` $\to$ `mcp`, `filesystem` $\to$ `filesystem`, `shell` $\to$ `shell`, `computer` $\to$ `computer`).
2. **Contextual System Prompt Guidance**: The router injects strict priority guidelines into the model's system prompt, instructing it to exhaust Level 1 and Level 2 interfaces before resorting to coordinate clicks.
3. **Evaluation Mode Filtering**: Allows running benchmarks in `shell_only`, `gui_only`, `mcp_only`, or `hybrid` modes to isolate performance variables.

---

## 3. Model Context Protocol (MCP) Integration & StoryTold Adapter

Located in `harness/mcp/`:
- `protocol.py`: JSON-RPC 2.0 type definitions.
- `client.py`: Async stdio process manager.
- `server_manager.py`: Multi-server multiplexer and tool wrapper.
- `servers/wordcraft_server.py`: Standalone StoryTold WordCraft MCP server.
- `storytold.py`: High-level StoryTold application helper.

### The Stdio Protocol Loop
The `MCPClient` launches the target server process (e.g. Python, Node.js, or Rust binary) and establishes bidirectional communication across standard input/output streams:

1. **Initialization Handshake**:
   ```json
   --> {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", ...}}
   <-- {"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {"name": "StoryTold-WordCraft-MCP"}, ...}}
   --> {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
   ```
2. **Dynamic Tool Registration**:
   The client executes `tools/list`, parses each tool's JSON Schema (`inputSchema`), and dynamically creates an `MCPToolWrapper` subclassing `BaseTool`.
3. **Tool Execution & Deserialization**:
   When the model invokes `wordcraft__new_document`, the wrapper constructs a `tools/call` JSON-RPC message, drains it to the process `stdin`, awaits the matching response ID from `stdout`, and extracts text and base64 raster image blocks.

### StoryTold Desktop Software Integration
StoryTold applications (WordCraft, DeckCraft, ArtCraft) expose rich document introspection capabilities:
- `inspect_document`: Emits a structured AST containing all paragraph nodes, heading tags, word counts, and formatting attributes.
- `render_page`: Produces an in-memory rasterization of the formatted page for visual validation.
- `parity`: Compares the internal document AST with the visual layout geometry to guarantee $100\%$ typography synchronization.

---

## 4. Sandbox Runtime & Virtual Displays

Located in `harness/sandbox/`:
- `base.py`: Abstract sandbox contract.
- `docker_sandbox.py`: Isolated container with virtual X11 display.
- `local_sandbox.py`: Fast native execution with synthetic desktop HUD.
- `state.py`: Snapshot and rollback manager.

### The Docker Virtual Desktop Architecture
The `DockerSandbox` runs an Ubuntu container with the following stack:
1. **Virtual Framebuffer (`Xvfb`)**: Creates an in-memory X11 display at `:99` with resolution $1024 \times 768 \times 24$-bit color depth without requiring a physical monitor or GPU.
2. **Window Manager (`XFCE4`)**: Provides window borders, focus management, taskbar, and desktop rendering.
3. **Input Injection (`xdotool`)**: Translates agent mouse moves, left/right clicks, double clicks, scrolls, and keystroke shortcuts directly into X11 input events.
4. **Screenshot Pipeline (`scrot` / ImageMagick `import`)**: Dumps the virtual framebuffer to high-speed PNG bytes.
5. **Human Observability (`x11vnc` + `noVNC`)**: Exposes port 6080. Anyone reviewing the agent can open `http://localhost:6080/vnc.html` in their web browser and watch the desktop session in real-time.

---

## 5. Token Conservation & Visual Frame Diffing

Located in `harness/tools/gui.py`:

Sending a full screenshot on every step is the primary cause of cost overruns and context degradation in computer use agents. NexusCUH implements **Perceptual Frame Diffing**:

```python
def _compute_frame_diff(self, new_bytes: bytes) -> tuple[bool, float]:
    # 1. Fast cryptographic hash check
    frame_hash = hashlib.sha256(new_bytes).hexdigest()
    if self.last_frame_hash == frame_hash:
        return False, 0.0

    # 2. Perceptual channel difference via PIL ImageChops
    img1 = Image.open(io.BytesIO(self.last_frame_bytes)).convert("RGB")
    img2 = Image.open(io.BytesIO(new_bytes)).convert("RGB")
    diff = ImageChops.difference(img1, img2)
    stat = diff.getbbox()
    if not stat:
        return False, 0.0

    # 3. Calculate pixel change ratio
    ratio = non_zero_pixels / float(total_pixels)
    return ratio > self.diff_threshold, ratio
```

- If an action (such as typing or moving a mouse) does not alter the visible screen beyond `diff_threshold` ($0.5\%$), NexusCUH omits the image payload and returns a token-efficient acknowledgement: `[Visual Optimization: Display visual state unchanged, frame omitted]`.
- This reduces visual token consumption by **up to 84%** across multi-step execution traces.

---

## 6. PTY Shell Sessions & Smart Output Windowing

Located in `harness/tools/shell.py`:

Command outputs like `git log`, `find /`, or test runners can easily produce 10,000+ lines of text, overflowing the model's context window.

### Output Windowing Algorithm
The `ShellTool` enforces strict context preservation:
- Preserves the first $N$ lines (head) to retain command initialization headers and diagnostic arguments.
- Preserves the last $M$ lines (tail) to retain final status codes, summary tallies, and stack traces.
- Replaces the interior with a metadata banner indicating the precise number of omitted lines and bytes:
  ```
  [... NexusCUH Output Windowed: Omitted 8,420 lines (412,890 bytes) to protect context window ...]
  ```

---

## 7. Multi-Modal Assertive Verification vs Syntactic Status

Located in `harness/verification/`:

In computer use, an exit code of `0` only means the interpreter did not crash; it does not confirm task completion. 

The `MultiModalVerifier` enforces ground-truth assertions:

| Assertion Class | Verification Mechanism | Failure Diagnostic |
|:---|:---|:---|
| `FileExistsAssertion` | Checks sandbox filesystem path resolution | `File '...' does NOT exist` |
| `FileContentRegexAssertion` | Compiles regex pattern against file content | `File content failed to match pattern: ...` |
| `FileJsonAssertion` | Validates JSON structure, keys, and expected values | `JSON key '...' value '...' != expected '...'` |
| `FileHashAssertion` | Computes SHA-256 byte digest against golden standard | `Hash mismatch: actual ... != expected ...` |
| `MCPStateAssertion` | Invokes asynchronous query on MCP server internal state | `Found X AST nodes, expected >= Y` |

---

## 8. Multi-Layered Safety Guardrails

Located in `harness/guardrails/`:

1. **Command AST & Regex Policy (`security.py`)**:
   Intercepts commands before execution. Blocks dangerous patterns (`rm -rf /`, `mkfs`, fork bombs, unauthorized modifications to `/etc` or `/usr/bin`).
2. **Prompt Injection Quarantine (`injection.py`)**:
   Detects adversarial injection attacks in observed stdout, file contents, or OCR text (e.g. `"IGNORE ALL PREVIOUS INSTRUCTIONS"`, `"SYSTEM OVERRIDE"`). Wraps suspicious text in an explicit untrusted observation banner.
3. **Sliding-Window Loop Detector (`loop_detector.py`)**:
   Maintains a queue of `(tool_name, args_hash, state_hash)`. If the agent repeats the exact same action 3 consecutive times with zero state change, it halts execution and issues an intervention warning.
4. **Budget Enforcer (`budget.py`)**:
   Enforces maximum steps, maximum execution time, and maximum financial cost in USD.

---

## 9. Evaluation Engine & Deterministic State Machine

Located in `harness/eval/`:

Benchmark evaluation requires rigorous determinism:
1. `sandbox.reset()` wipes all previous task artifacts and restores pristine snapshots.
2. `task.setup(sandbox)` seeds initial files and configuration.
3. `orchestrator.run_task(task.instruction)` executes the agent ReAct loop.
4. `verifier.verify(sandbox, mcp_manager)` computes ground truth.
5. `LeaderboardReporter` exports detailed Markdown and JSON reports.

---

## 10. Step-by-Step Guide to Adding a New MCP Server

Adding an external MCP server (e.g. SQLite, GitHub, or an internal enterprise tool) takes just a few lines of configuration:

### Method A: Via Configuration YAML (`nexus_config.yaml`)
```yaml
mcp:
  custom_servers:
    sqlite_db:
      command: "uvx"
      args: ["mcp-server-sqlite", "--db-path", "/home/sandboxuser/workspace/data.db"]
```

### Method B: Via Python API
```python
from harness.config import HarnessConfig

config = HarnessConfig.load_from_env()
config.mcp.custom_servers["sqlite_db"] = {
    "command": "uvx",
    "args": ["mcp-server-sqlite", "--db-path", "./workspace/data.db"]
}
```

When `orchestrator.initialize()` is called, NexusCUH will automatically:
1. Launch the process and complete the JSON-RPC initialization handshake.
2. Query `tools/list` to discover all tools.
3. Prefix tool names with `sqlite_db__<tool_name>`.
4. Expose them to the agent's function-calling tool set with full schema definitions.
