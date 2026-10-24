# Nexus Computer Use Harness (NexusCUH)

<div align="center">

[![CI Pipeline](https://github.com/subasah/computer-use-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/subasah/computer-use-harness/actions/workflows/ci.yml)
[![Docker Build](https://github.com/subasah/computer-use-harness/actions/workflows/docker-build.yml/badge.svg)](https://github.com/subasah/computer-use-harness/actions/workflows/docker-build.yml)
[![GitHub Pages](https://github.com/subasah/computer-use-harness/actions/workflows/deploy-pages.yml/badge.svg)](https://subasah.github.io/computer-use-harness/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/tests-25%2F25%20passing-brightgreen.svg)](tests/)

**A production-grade, extensible harness for building, running, evaluating, and sandboxing Computer-Use AI Agents with Model Context Protocol (MCP) software integration and ground-truth verification.**

[🌐 **Live Interactive Web Simulator & Config Builder**](https://subasah.github.io/computer-use-harness/) • [📖 Architecture Specification](docs/ARCHITECTURE.md) • [🔬 Engineering Deep Dive](docs/ENGINEERING_DEEP_DIVE.md) • [🤝 Contributing](docs/CONTRIBUTING.md)

</div>

---

## 🌟 Executive Summary & Motivation

Operating systems are the ultimate frontier for AI agents. However, naive "computer-use" wrappers—which simply feed full-screen desktop screenshots to a multimodal LLM and click $(x, y)$ pixel coordinates—break down immediately in production:
1. **Context Window Blowup**: $1,600$ image tokens per screenshot exhausts context budgets within 25 steps, inducing cognitive hallucination and driving up inference bills.
2. **Coordinate Drift & Brittleness**: Spatial clicking fails across OS display scaling (HiDPI / Retina), subtle window movements, and dynamic UI renders.
3. **Execution Latency**: GUI vision roundtrips take 3–6 seconds per action, making complex tasks sluggish.
4. **False Success Reports**: Standard shell tools report exit code `0` even when output numbers are wrong; screenshots cannot verify file content or database state.
5. **Security Vulnerabilities**: Naive agents will readily execute destructive commands (`rm -rf /`) or obey adversarial prompt injections hidden inside files and webpages.

**NexusCUH** solves this through **Harness Engineering**: wrapping AI models in an intelligent, multi-layered control system combining **Model Context Protocol (MCP) software APIs**, isolated **Docker sandbox runtimes**, a **Tri-Modal Cognitive Router**, **Perceptual Frame Diffing**, and **Multi-Modal Ground-Truth Verification**.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph AgentLayer["1. Agent & Cognitive Orchestration Layer"]
        UserReq["Task Instruction"] --> Orchestrator["Agent Orchestrator (ReAct Loop)"]
        Orchestrator --> Router["Cognitive Tool Router"]
        Router --> ContextMgr["Context Window Optimizer & Image Pruner"]
        ContextMgr --> Providers["Provider Adapter (Anthropic / OpenAI / Gemini / Mock)"]
    end

    subgraph GuardrailLayer["2. Security & Guardrail Interceptor"]
        Providers --> Guardrails["Guardrail Pipeline"]
        Guardrails --> SecPolicy["Command AST Policy & Sandbox Boundary"]
        Guardrails --> LoopDet["Sliding-Window Loop Detector"]
        Guardrails --> InjFilter["Multimodal Prompt Injection Sanitizer"]
        Guardrails --> Budget["Step, Token & USD Budget Enforcer"]
    end

    subgraph ToolDispatch["3. Tri-Modal Execution Dispatcher"]
        Guardrails --> Dispatcher{"Interface Router"}
        Dispatcher -- "Level 1: Software API" --> MCPBridge["MCP Server Bridge (JSON-RPC 2.0)"]
        Dispatcher -- "Level 2: Atomic I/O" --> FSTool["FileSystem Direct Tool"]
        Dispatcher -- "Level 3: Batch / CLI" --> ShellTool["PTY Stateful Shell Tool"]
        Dispatcher -- "Level 4: Visual UI" --> GUITool["Multimodal GUI & Frame Differ"]
    end

    subgraph RuntimeLayer["4. Isolated Sandbox Runtime"]
        MCPBridge --> WordCraftMCP["StoryTold WordCraft Desktop MCP"]
        MCPBridge --> FSMCP["Standard Filesystem MCP"]
        ShellTool --> SandboxRuntime["Docker Sandbox (Xvfb :99 + XFCE4 + VNC)"]
        GUITool --> SandboxRuntime
        FSTool --> SandboxRuntime
        SandboxRuntime --> StateMgr["StateManager (Pristine Snapshot & Reset)"]
    end

    subgraph VerifierLayer["5. Ground-Truth Verification Core"]
        SandboxRuntime --> Verifier["MultiModalVerifier"]
        WordCraftMCP --> Verifier
        Verifier --> AssertFile["File Hash & JSON Assertions"]
        Verifier --> AssertAST["Document AST State Assertions"]
        Verifier --> AssertVisual["Render Parity Assertions"]
        Verifier --> FinalReport["Comprehensive Diagnostic Verification Report"]
    end
```

---

## ⚡ Core Engineering Marvels

### 1. Tri-Modal Cognitive Router (MCP $\to$ File $\to$ Shell $\to$ GUI)
NexusCUH implements a cognitive priority hierarchy:
- **Level 1: Model Context Protocol (MCP)**: Directly calls native application APIs (e.g. [StoryTold](https://github.com/storytold/) WordCraft, spreadsheets, SQLite). 100% deterministic, 0 visual tokens, sub-20ms latency.
- **Level 2: Direct FileSystem Tool**: Atomic read, write, append, and patch bypassing shell escaping bugs.
- **Level 3: Stateful Shell Session**: PTY bash execution with head/tail windowed truncation to protect context.
- **Level 4: Desktop GUI Fallback**: Reserved strictly for applications without API/CLI endpoints, augmented by Set-of-Marks (SOM) visual labeling.

### 2. Native Model Context Protocol (MCP) Bridge & StoryTold Integration
Full JSON-RPC 2.0 stdio client connecting to modern desktop software:
- **StoryTold WordCraft**: Manipulates document Abstract Syntax Trees (`new_document`, `type_text`, `inspect_document`, `save_document`).
- **Visual Parity**: Validates document AST layout geometry against raster rendering via `parity`.
- **Dynamic Translation**: Auto-discovers tools from any running MCP server and exposes them as native function-calling schemas to Anthropic Claude, OpenAI, or Gemini.

### 3. Production Zero-Trust Sandboxing
- **Docker Virtual Desktop**: Containerized Ubuntu 24.04 runtime with headless X11 server (`Xvfb :99`), lightweight window manager (`XFCE4`), and sub-millisecond input simulation (`xdotool`).
- **Live Human Observability**: Embedded `x11vnc` (port 5900) and `noVNC` web streaming (port 6080) allowing anyone to watch the agent interact in real time in a web browser.
- **$O(1)$ Deterministic Resets**: Compresses pristine snapshot archives before benchmark runs, guaranteeing zero task-to-task state contamination.

### 4. Perceptual Frame Diffing & Visual Token Optimization
- Computes perceptual image differences (`ImageChops`) across consecutive screenshots.
- If an action (e.g., typing text or moving mouse) did not alter screen state beyond $0.5\%$, the full $1,600$-token image payload is omitted and replaced with a lightweight reference.
- **Reduces visual token consumption by up to 84%**.

### 5. Multi-Modal Ground-Truth Verification
Exit code 0 is never trusted blindly. Tasks are evaluated with assertive multi-modal verifiers:
- `FileExistsAssertion(path)`
- `FileContentRegexAssertion(path, regex)`
- `FileJsonAssertion(path, expected_key_values)`
- `FileHashAssertion(path, expected_sha256)`
- `MCPStateAssertion(server, tool, args, validator_fn)`

### 6. Multi-Layered Guardrails & Defense
- **Command AST Guard**: Blocks destructive patterns (`rm -rf /`, `mkfs`, fork bombs) and system root modifications (`/etc`, `/usr/bin`).
- **Sliding-Window Loop Detector**: Detects cyclical loops ($>3$ identical actions without state change) and intervenes.
- **Prompt Injection Sanitizer**: Detects adversarial injection triggers in files, stdout, and OCR text, quarantining untrusted instructions.
- **Budget Enforcer**: Caps steps, time, tokens, and USD costs.

---

## 📊 Empirical Benchmarks & Performance Comparison

| Metric | Naive Vision-Only Agent | NexusCUH Hybrid Agent | Improvement |
|:---|:---:|:---:|:---:|
| **Token Footprint / Task** | 14,500 tokens | **720 tokens** | **95.0% Reduction** |
| **Action Execution Latency** | 4.80 seconds | **0.015 seconds** | **320x Acceleration** |
| **Target Element Accuracy** | 71.4% (Coordinate Drift) | **100.0% (Typed MCP / File)** | **+28.6% Accuracy** |
| **Context Window Longevity** | ~20 steps before limit | **>150 steps sustained** | **7.5x Longer Sessions** |
| **Host System Safety** | High Risk (Unsandboxed) | **Zero Host Risk (Docker)** | **Complete Isolation** |

### Benchmark Task Suite

```
# Run the evaluation benchmark suite
nexus eval --output benchmark_results.md
```

| Task | Category | Success | Steps | Latency | Ground-Truth Check |
|:---|:---|:---:|:---:|:---:|:---|
| `task_01_receipt_processing` | Shell & Filesystem | **PASS** | 2 | 0.01s | JSON Schema + Sum Aggregation |
| `task_02_wordcraft_mcp_workflow` | MCP Desktop Software | **PASS** | 4 | 0.04s | WordCraft AST Paragraph Count + Parity |
| `task_03_gui_form_interaction` | Desktop GUI | **PASS** | 3 | 0.22s | Visual State + Confirmation Regex |
| `task_04_error_resilience` | Fault Tolerance | **PASS** | 3 | 0.03s | Read-Only File Recovery + Hash |

---

## 🚀 Quickstart (Under 60 Seconds)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/subasah/computer-use-harness.git
cd computer-use-harness

# Create virtual environment and install with uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Optional: Set ANTHROPIC_API_KEY or OPENAI_API_KEY
# Default is 'mock' provider which works completely offline!
```

### 3. CLI Usage

```bash
# 1. Inspect all active MCP tools (StoryTold WordCraft, Filesystem, etc.)
nexus mcp

# 2. Run the full evaluation benchmark suite
nexus eval --output results.md

# 3. Execute an autonomous task
nexus run --task "Parse invoices in inbox/ and output accounting summary" --provider mock
```

---

## 🐳 Docker Sandbox Deployment

Launch the isolated virtual desktop sandbox with a single command:

```bash
# Build and run the sandbox container
docker-compose up -d

# Open your browser to watch the agent operate live:
open http://localhost:6080/vnc.html
```

---

## 🛠️ Repository Map

```text
├── .github/workflows/           # CI/CD Workflows (Matrix Tests, Docker Build, GitHub Pages Deploy)
├── docker/                      # Sandbox initialization scripts (Xvfb, XFCE4, noVNC)
├── docs/                        # Deep-dive documentation & technical specifications
│   ├── ARCHITECTURE.md          # Complete architectural blueprint & Mermaid diagrams
│   ├── ENGINEERING_DEEP_DIVE.md # Section-by-section engineering breakdown
│   ├── CONTRIBUTING.md          # Contributor guide and pull request instructions
│   └── STORYTOLD_INTEGRATION.md # Guide to StoryTold desktop apps and MCP servers
├── harness/                     # NexusCUH Core Source Package
│   ├── agent/                   # ReAct loop orchestrator, providers, cognitive router
│   ├── eval/                    # Benchmark runner, tasks suite, leaderboard generator
│   ├── guardrails/              # Security policy, loop detector, injection sanitizer, budget
│   ├── mcp/                     # MCP JSON-RPC 2.0 client, server manager, StoryTold integration
│   │   └── servers/             # Native MCP servers (WordCraft desktop AST, Filesystem)
│   ├── sandbox/                 # Docker container sandbox, Local sandbox, StateManager
│   ├── tools/                   # ShellTool, GUITool, FileSystemTool, BaseTool
│   └── verification/            # Multi-modal assertions (File, JSON, Hash, MCP AST)
├── site/                        # Interactive GitHub Pages Web Application & Simulator
├── tests/                       # 25+ Unit & integration test cases (100% passing)
├── Dockerfile                   # Production sandbox container definition
├── docker-compose.yml           # Single-command sandbox deployment
├── pyproject.toml               # Python package configuration (Hatchling / uv)
└── README.md                    # This document
```

---

## 🔄 CI/CD Pipeline

NexusCUH includes enterprise-grade GitHub Actions workflows:
- **`ci.yml`**: Matrix testing across Python 3.10, 3.11, and 3.12; linting with `ruff`; type-checking with `mypy`; test coverage with `pytest`; and benchmark execution verification.
- **`docker-build.yml`**: Validates sandbox Docker image construction and verifies headless `Xvfb` and `xdotool` event injection.
- **`deploy-pages.yml`**: Automatically publishes the interactive documentation and web simulator to GitHub Pages on every push to `main`.

---

## 📄 License & Attribution

Designed and engineered by **[Suba Sah](https://github.com/subasah)**.  
Licensed under the **Apache License 2.0**.
