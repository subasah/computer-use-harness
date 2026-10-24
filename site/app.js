/**
 * NexusCUH Interactive Web Dashboard & Simulator Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  initSimulator();
  initArchTabs();
  initConfigBuilder();
  initCharts();
});

/* ==============================================================================
 * 1. LIVE EXECUTION SIMULATOR
 * ============================================================================== */

const SCENARIOS = {
  storytold_wordcraft: [
    {
      step: 1,
      cmd: "curl -s http://localhost:8000/health || test -f /tmp/wordcraft.sock",
      stdout: "StoryTold WordCraft Desktop Runtime active.\nMCP Server listening on stdio.",
      cursor: { x: 120, y: 85 },
      winTitle: "StoryTold WordCraft Desktop",
      doc: {
        h1: "Q3 Engineering Architecture Memo",
        h2: "Initializing...",
        p: "Waiting for agent MCP input..."
      },
      router: "Level 1: MCP Deterministic Tool (Fastest, 0 Visual Tokens)",
      mcp: `{\n  "jsonrpc": "2.0",\n  "method": "tools/call",\n  "params": {\n    "name": "wordcraft__new_document",\n    "arguments": { "title": "Q3 Engineering Architecture Memo" }\n  }\n}`,
      tokens: { prompt: 240, visual: "0 (Saved via MCP)", duration: "12.2ms", groundTruth: "ASSERT_OK" }
    },
    {
      step: 2,
      cmd: "nexus mcp call wordcraft type_text --text 'Executive Summary' --paragraph_type 'heading1'",
      stdout: "Inserted heading 'Executive Summary' at AST node p-1.",
      cursor: { x: 190, y: 85 },
      winTitle: "StoryTold WordCraft — Q3 Memo",
      doc: {
        h1: "Q3 Engineering Architecture Memo",
        h2: "Executive Summary",
        p: "Drafting body paragraph..."
      },
      router: "Level 1: MCP Deterministic Tool",
      mcp: `{\n  "jsonrpc": "2.0",\n  "method": "tools/call",\n  "params": {\n    "name": "wordcraft__type_text",\n    "arguments": {\n      "text": "Executive Summary",\n      "paragraph_type": "heading1"\n    }\n  }\n}`,
      tokens: { prompt: 310, visual: "0 (Saved via MCP)", duration: "15.8ms", groundTruth: "ASSERT_OK" }
    },
    {
      step: 3,
      cmd: "nexus mcp call wordcraft type_text --text 'NexusCUH delivers hybrid shell, GUI, and MCP orchestration with high reliability.'",
      stdout: "Inserted body paragraph at AST node p-2 (12 words).",
      cursor: { x: 280, y: 220 },
      winTitle: "StoryTold WordCraft — Q3 Memo",
      doc: {
        h1: "Q3 Engineering Architecture Memo",
        h2: "Executive Summary",
        p: "NexusCUH delivers hybrid shell, GUI, and MCP orchestration with high reliability."
      },
      router: "Level 1: MCP Deterministic Tool",
      mcp: `{\n  "jsonrpc": "2.0",\n  "method": "tools/call",\n  "params": {\n    "name": "wordcraft__type_text",\n    "arguments": {\n      "text": "NexusCUH delivers hybrid shell, GUI, and MCP orchestration with high reliability.",\n      "paragraph_type": "paragraph"\n    }\n  }\n}`,
      tokens: { prompt: 380, visual: "0 (Saved via MCP)", duration: "14.1ms", groundTruth: "ASSERT_OK" }
    },
    {
      step: 4,
      cmd: "nexus mcp call wordcraft save_document --path 'docs/architecture_memo.txt'",
      stdout: "Saved document to 'docs/architecture_memo.txt' (148 bytes written).",
      cursor: { x: 120, y: 85 },
      winTitle: "StoryTold WordCraft — Saved",
      doc: {
        h1: "Q3 Engineering Architecture Memo",
        h2: "Executive Summary",
        p: "NexusCUH delivers hybrid shell, GUI, and MCP orchestration with high reliability."
      },
      router: "Level 1: MCP Deterministic Tool",
      mcp: `{\n  "jsonrpc": "2.0",\n  "method": "tools/call",\n  "params": {\n    "name": "wordcraft__save_document",\n    "arguments": { "path": "docs/architecture_memo.txt" }\n  }\n}`,
      tokens: { prompt: 420, visual: "0 (Saved via MCP)", duration: "19.3ms", groundTruth: "ASSERT_OK" }
    },
    {
      step: 5,
      cmd: "test -f docs/architecture_memo.txt && sha256sum docs/architecture_memo.txt",
      stdout: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  docs/architecture_memo.txt\n[VERIFIER] Ground-Truth Check: 4/4 Assertions PASSED.",
      cursor: { x: 300, y: 350 },
      winTitle: "StoryTold WordCraft — Synced & Verified",
      doc: {
        h1: "Q3 Engineering Architecture Memo",
        h2: "Executive Summary",
        p: "NexusCUH delivers hybrid shell, GUI, and MCP orchestration with high reliability."
      },
      router: "Ground-Truth Verification Engine",
      mcp: `{\n  "jsonrpc": "2.0",\n  "method": "tools/call",\n  "params": {\n    "name": "wordcraft__parity",\n    "arguments": {}\n  }\n}`,
      tokens: { prompt: 460, visual: "0 (Saved via MCP)", duration: "9.2ms", groundTruth: "TASK_PASSED_100%" }
    }
  ],
  receipt_processing: [
    {
      step: 1,
      cmd: "ls -la inbox/",
      stdout: "total 12\n-rw-r--r-- 1 sandboxuser staff 98 Oct 24 inv_001.txt\n-rw-r--r-- 1 sandboxuser staff 102 Oct 24 inv_002.txt\n-rw-r--r-- 1 sandboxuser staff 95 Oct 24 inv_003.txt",
      cursor: { x: 100, y: 100 },
      winTitle: "Terminal Session — Inbox Directory",
      doc: { h1: "Invoice Processing Pipeline", h2: "Directory Scan", p: "Found 3 invoices: Harbour Cafe, City Taxi, Parkside Hotel" },
      router: "Level 3: Shell Batch Execution",
      mcp: `{\n  "tool": "shell",\n  "command": "ls -la inbox/"\n}`,
      tokens: { prompt: 180, visual: "0", duration: "8.5ms", groundTruth: "SCAN_OK" }
    },
    {
      step: 2,
      cmd: "python3 -c 'import glob, re, json; files=glob.glob(\"inbox/*.txt\"); print(len(files))'",
      stdout: "Total invoices detected: 3",
      cursor: { x: 150, y: 150 },
      winTitle: "Terminal Session — Extraction",
      doc: { h1: "Invoice Processing Pipeline", h2: "Data Extraction", p: "Parsed amounts: $45.50, $67.00, $300.00 -> Sum = $412.50" },
      router: "Level 3: Shell Python Processor",
      mcp: `{\n  "tool": "shell",\n  "command": "python3 parse_receipts.py"\n}`,
      tokens: { prompt: 290, visual: "0", duration: "24.1ms", groundTruth: "PARSE_OK" }
    },
    {
      step: 3,
      cmd: "mkdir -p reports && echo '{\"invoice_count\": 3, \"grand_total\": 412.50}' > reports/accounting_summary.json",
      stdout: "Wrote structured ledger to reports/accounting_summary.json",
      cursor: { x: 200, y: 200 },
      winTitle: "Terminal Session — Report Written",
      doc: { h1: "Invoice Processing Pipeline", h2: "Ledger Complete", p: "Grand Total: $412.50 across 3 vendors. Saved." },
      router: "Level 2: Direct FileSystem Tool",
      mcp: `{\n  "tool": "filesystem",\n  "action": "write",\n  "path": "reports/accounting_summary.json"\n}`,
      tokens: { prompt: 350, visual: "0", duration: "11.0ms", groundTruth: "WRITE_OK" }
    },
    {
      step: 4,
      cmd: "cat reports/accounting_summary.json | jq .",
      stdout: "{\n  \"invoice_count\": 3,\n  \"grand_total\": 412.5\n}",
      cursor: { x: 250, y: 250 },
      winTitle: "Terminal Session — Ground Truth Verification",
      doc: { h1: "Invoice Processing Pipeline", h2: "Verified", p: "Asserted JSON structure against schema." },
      router: "Ground-Truth Verification Engine",
      mcp: `{\n  "assertion": "FileJsonAssertion",\n  "path": "reports/accounting_summary.json"\n}`,
      tokens: { prompt: 410, visual: "0", duration: "6.2ms", groundTruth: "TASK_PASSED_100%" }
    }
  ]
};

let currentScenarioKey = 'storytold_wordcraft';
let currentStepIdx = 0;
let isPlaying = false;
let playInterval = null;

function initSimulator() {
  const scenarioSelect = document.getElementById('scenarioSelect');
  const prevBtn = document.getElementById('simPrevBtn');
  const nextBtn = document.getElementById('simNextBtn');
  const playBtn = document.getElementById('simPlayBtn');
  const resetBtn = document.getElementById('simResetBtn');
  const somToggle = document.getElementById('toggleSOM');

  scenarioSelect.addEventListener('change', (e) => {
    currentScenarioKey = e.target.value in SCENARIOS ? e.target.value : 'storytold_wordcraft';
    currentStepIdx = 0;
    stopAutoPlay();
    renderStep();
  });

  prevBtn.addEventListener('click', () => {
    stopAutoPlay();
    if (currentStepIdx > 0) {
      currentStepIdx--;
      renderStep();
    }
  });

  nextBtn.addEventListener('click', () => {
    stopAutoPlay();
    const scenario = SCENARIOS[currentScenarioKey];
    if (currentStepIdx < scenario.length - 1) {
      currentStepIdx++;
      renderStep();
    }
  });

  playBtn.addEventListener('click', () => {
    if (isPlaying) {
      stopAutoPlay();
    } else {
      startAutoPlay();
    }
  });

  resetBtn.addEventListener('click', () => {
    stopAutoPlay();
    currentStepIdx = 0;
    renderStep();
  });

  somToggle.addEventListener('change', (e) => {
    const tags = document.querySelectorAll('.som-tag');
    tags.forEach(t => t.style.display = e.target.checked ? 'block' : 'none');
  });

  renderStep();
}

function startAutoPlay() {
  isPlaying = true;
  const playBtn = document.getElementById('simPlayBtn');
  playBtn.textContent = '⏸ Pause';
  playBtn.classList.add('sim-btn-active');

  playInterval = setInterval(() => {
    const scenario = SCENARIOS[currentScenarioKey];
    if (currentStepIdx < scenario.length - 1) {
      currentStepIdx++;
      renderStep();
    } else {
      stopAutoPlay();
    }
  }, 2200);
}

function stopAutoPlay() {
  isPlaying = false;
  if (playInterval) clearInterval(playInterval);
  const playBtn = document.getElementById('simPlayBtn');
  playBtn.textContent = '▶ Auto-Play';
  playBtn.classList.remove('sim-btn-active');
}

function renderStep() {
  const scenario = SCENARIOS[currentScenarioKey];
  const stepData = scenario[currentStepIdx];

  document.getElementById('simStepCurrent').textContent = currentStepIdx + 1;
  document.getElementById('simStepTotal').textContent = scenario.length;

  // Terminal
  document.getElementById('simTermCmd').textContent = stepData.cmd;
  document.getElementById('simTermStdout').textContent = stepData.stdout;

  // Desktop Window & Cursor
  document.getElementById('simWinTitle').textContent = stepData.winTitle;
  document.getElementById('docH1').textContent = stepData.doc.h1;
  document.getElementById('docH2').textContent = stepData.doc.h2;
  document.getElementById('docP').textContent = stepData.doc.p;

  const cursor = document.getElementById('simCursor');
  cursor.style.top = stepData.cursor.y + 'px';
  cursor.style.left = stepData.cursor.x + 'px';

  const ripple = document.getElementById('clickRipple');
  ripple.classList.remove('animate');
  void ripple.offsetWidth; // Trigger reflow
  ripple.classList.add('animate');

  // Telemetry & MCP
  document.getElementById('simRouterDecision').textContent = stepData.router;
  document.getElementById('simMcpPacket').textContent = stepData.mcp;
  document.getElementById('simPromptTokens').textContent = stepData.tokens.prompt;
  document.getElementById('simVisualTokens').textContent = stepData.tokens.visual;
  document.getElementById('simDuration').textContent = stepData.tokens.duration;
  document.getElementById('simGroundTruth').textContent = stepData.tokens.groundTruth;
}

/* ==============================================================================
 * 2. ARCHITECTURE TABS
 * ============================================================================== */

function initArchTabs() {
  const tabs = document.querySelectorAll('.arch-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetId = `tab-${tab.getAttribute('data-tab')}`;
      document.querySelectorAll('.arch-panel').forEach(p => p.classList.remove('active'));
      const activePanel = document.getElementById(targetId);
      if (activePanel) activePanel.classList.add('active');
    });
  });
}

/* ==============================================================================
 * 3. CONFIGURATION BUILDER
 * ============================================================================== */

function initConfigBuilder() {
  const sandboxRadios = document.querySelectorAll('input[name="cfgSandbox"]');
  const providerSelect = document.getElementById('cfgProvider');
  const mcpStorytold = document.getElementById('cfgMcpStorytold');
  const mcpFilesystem = document.getElementById('cfgMcpFilesystem');
  const mcpBrowser = document.getElementById('cfgMcpBrowser');
  const maxSteps = document.getElementById('cfgMaxSteps');
  const maxCost = document.getElementById('cfgMaxCost');
  const injDefense = document.getElementById('cfgInjectionDefense');
  const frameDiffing = document.getElementById('cfgFrameDiffing');

  const stepVal = document.getElementById('cfgStepVal');
  const costVal = document.getElementById('cfgCostVal');
  const copyBtn = document.getElementById('copyConfigBtn');
  const tabYaml = document.getElementById('tabYaml');
  const tabPython = document.getElementById('tabPython');

  let activeFormat = 'yaml';

  maxSteps.addEventListener('input', () => {
    stepVal.textContent = maxSteps.value;
    updateConfig();
  });

  maxCost.addEventListener('input', () => {
    costVal.textContent = parseFloat(maxCost.value).toFixed(2);
    updateConfig();
  });

  [...sandboxRadios, providerSelect, mcpStorytold, mcpFilesystem, mcpBrowser, injDefense, frameDiffing].forEach(el => {
    el.addEventListener('change', updateConfig);
  });

  tabYaml.addEventListener('click', () => {
    activeFormat = 'yaml';
    tabYaml.classList.add('active');
    tabPython.classList.remove('active');
    updateConfig();
  });

  tabPython.addEventListener('click', () => {
    activeFormat = 'python';
    tabPython.classList.add('active');
    tabYaml.classList.remove('active');
    updateConfig();
  });

  copyBtn.addEventListener('click', () => {
    const code = document.getElementById('configOutput').textContent;
    navigator.clipboard.writeText(code).then(() => {
      copyBtn.textContent = '✔ Copied!';
      setTimeout(() => copyBtn.textContent = '📋 Copy', 2000);
    });
  });

  function updateConfig() {
    const sandbox = document.querySelector('input[name="cfgSandbox"]:checked').value;
    const [provider, model] = providerSelect.value.split(':');
    const steps = maxSteps.value;
    const cost = maxCost.value;

    if (activeFormat === 'yaml') {
      const yaml = `# Nexus Computer Use Harness Configuration
version: "0.1.0"
provider: "${provider}"
model_name: "${model}"

sandbox:
  type: "${sandbox}"
  workspace_dir: "./workspace"
  display: ":99"
  resolution:
    width: 1024
    height: 768
  vnc_port: 5900
  novnc_port: 6080

mcp:
  auto_discovery: true
  storytold_enabled: ${mcpStorytold.checked}
  filesystem_enabled: ${mcpFilesystem.checked}
  browser_enabled: ${mcpBrowser.checked}

guardrails:
  max_steps: ${steps}
  max_cost_usd: ${cost}.00
  command_timeout_seconds: 30
  prompt_injection_defense: ${injDefense.checked}
  frame_diffing: ${frameDiffing.checked}
  loop_detection_window: 4
`;
      document.getElementById('configOutput').textContent = yaml;
    } else {
      const py = `import asyncio
from harness import HarnessConfig, AgentOrchestrator
from harness.config import SandboxType, LLMProviderType

async def main():
    config = HarnessConfig.load_from_env()
    config.sandbox.sandbox_type = SandboxType.${sandbox.toUpperCase()}
    config.provider = LLMProviderType.${provider.toUpperCase()}
    config.model_name = "${model}"
    config.guardrails.max_steps = ${steps}
    config.guardrails.max_cost_usd = ${cost}.00
    config.mcp.storytold_enabled = ${mcpStorytold.checked}

    orchestrator = AgentOrchestrator(config=config)
    await orchestrator.initialize()

    result = await orchestrator.run_task(
        "Open WordCraft via MCP, write tech memo, and verify output."
    )
    print(f"Task Outcome: {result['success']} in {result['steps_count']} steps")
    await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
`;
      document.getElementById('configOutput').textContent = py;
    }
  }

  updateConfig();
}

/* ==============================================================================
 * 4. PERFORMANCE CHARTS
 * ============================================================================== */

function initCharts() {
  // Chart 1: Token Usage Comparison
  const tokenCtx = document.getElementById('tokenChart');
  if (tokenCtx) {
    new Chart(tokenCtx, {
      type: 'bar',
      data: {
        labels: ['Invoice Parsing', 'WordCraft Memo', 'GUI Form', 'Error Recovery'],
        datasets: [
          {
            label: 'Pure GUI (Naive Vision)',
            data: [11200, 14500, 8900, 12800],
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderColor: '#ef4444',
            borderWidth: 1
          },
          {
            label: 'NexusCUH (Hybrid MCP + Shell)',
            data: [380, 720, 1850, 610],
            backgroundColor: 'rgba(99, 102, 241, 0.85)',
            borderColor: '#6366f1',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8' } }
        },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }

  // Chart 2: Latency Comparison
  const latencyCtx = document.getElementById('latencyChart');
  if (latencyCtx) {
    new Chart(latencyCtx, {
      type: 'bar',
      data: {
        labels: ['New Doc', 'Insert Heading', 'Insert Body', 'Save File', 'Parity Check'],
        datasets: [
          {
            label: 'GUI Coordinate Clicks (s)',
            data: [4.2, 3.8, 5.1, 4.5, 3.9],
            backgroundColor: 'rgba(245, 158, 11, 0.7)',
            borderColor: '#f59e0b',
            borderWidth: 1
          },
          {
            label: 'StoryTold MCP Tool Call (s)',
            data: [0.012, 0.015, 0.014, 0.019, 0.009],
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderColor: '#10b981',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8' } }
        },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: {
            type: 'logarithmic',
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(255,255,255,0.05)' }
          }
        }
      }
    });
  }
}
