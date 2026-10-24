/**
 * NexusCUH Interactive Web Dashboard & Simulator Engine
 * Responsive, accessible, and high-performance client script.
 */

document.addEventListener('DOMContentLoaded', () => {
  initScrollProgress();
  initMobileNav();
  initSimulator();
  initArchTabs();
  initConfigBuilder();
  initCopyCodeButtons();
  initBackToTop();
  initCharts();
});

/* ==============================================================================
 * 1. READING PROGRESS BAR
 * ============================================================================== */

function initScrollProgress() {
  const progressBar = document.getElementById('progressBar');
  if (!progressBar) return;

  window.addEventListener('scroll', () => {
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = totalHeight > 0 ? (window.scrollY / totalHeight) * 100 : 0;
    progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
  }, { passive: true });
}

/* ==============================================================================
 * 2. MOBILE NAVIGATION DRAWER
 * ============================================================================== */

function initMobileNav() {
  const menuBtn = document.getElementById('mobileMenuBtn');
  const navLinks = document.getElementById('navLinks');
  if (!menuBtn || !navLinks) return;

  menuBtn.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');
    menuBtn.classList.toggle('open', isOpen);
    menuBtn.setAttribute('aria-expanded', String(isOpen));
  });

  // Close drawer when any nav link is tapped
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      menuBtn.classList.remove('open');
      menuBtn.setAttribute('aria-expanded', 'false');
    });
  });

  // Close with Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      menuBtn.classList.remove('open');
      menuBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

/* ==============================================================================
 * 3. LIVE EXECUTION SIMULATOR & PANE VIEW SWITCHER
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
  ],
  gui_desktop_form: [
    {
      step: 1,
      cmd: "xdotool search --name 'Form' windowactivate",
      stdout: "Found window ID 0x2400001 (Title: 'Desktop Submission Portal')",
      cursor: { x: 100, y: 90 },
      winTitle: "Desktop Submission Portal",
      doc: { h1: "Portal Status Form", h2: "Pending Input", p: "Form ready for agent submission." },
      router: "Level 4: Desktop GUI Tool (Set-of-Marks Overlay)",
      mcp: `{\n  "action": "screenshot",\n  "som_tags_detected": 3\n}`,
      tokens: { prompt: 420, visual: "1,600 (Initial Frame)", duration: "210.4ms", groundTruth: "WINDOW_READY" }
    },
    {
      step: 2,
      cmd: "xdotool mousemove 200 150 click 1 && xdotool type 'SUBMITTED_STATUS=CONFIRMED'",
      stdout: "Clicked input box at (200, 150). Typed confirmation text.",
      cursor: { x: 200, y: 150 },
      winTitle: "Desktop Submission Portal — Focused",
      doc: { h1: "Portal Status Form", h2: "Typing Entry", p: "Status: SUBMITTED_STATUS=CONFIRMED" },
      router: "Level 4: Desktop GUI Tool (Frame Differ Active)",
      mcp: `{\n  "action": "left_click",\n  "coordinate": [200, 150]\n}`,
      tokens: { prompt: 490, visual: "0 (Frame Omitted: Unchanged)", duration: "18.2ms", groundTruth: "TYPED_OK" }
    },
    {
      step: 3,
      cmd: "echo 'SUBMITTED_STATUS=CONFIRMED' > gui_submission.log && grep -q 'CONFIRMED' gui_submission.log",
      stdout: "Status verified in log.\n[VERIFIER] Ground-Truth Assertion PASSED.",
      cursor: { x: 220, y: 220 },
      winTitle: "Desktop Submission Portal — Confirmed",
      doc: { h1: "Portal Status Form", h2: "Completed", p: "Submission recorded and verified with ground truth." },
      router: "Ground-Truth Verification Engine",
      mcp: `{\n  "assertion": "FileContentRegexAssertion",\n  "pattern": "SUBMITTED_STATUS=CONFIRMED"\n}`,
      tokens: { prompt: 540, visual: "0", duration: "12.0ms", groundTruth: "TASK_PASSED_100%" }
    }
  ],
  error_recovery: [
    {
      step: 1,
      cmd: "echo 'TEST' >> protected/config.env",
      stdout: "bash: protected/config.env: Permission denied (Exit Code: 1)",
      cursor: { x: 80, y: 80 },
      winTitle: "Terminal — Error Detected",
      doc: { h1: "Self-Healing Diagnostic", h2: "Fault Injected", p: "Read-only permission error on protected/config.env" },
      router: "Fault Tolerance Subsystem",
      mcp: `{\n  "error_handler": "detect_permission_failure",\n  "target": "protected/config.env"\n}`,
      tokens: { prompt: 210, visual: "0", duration: "11.5ms", groundTruth: "ERROR_DIAGNOSED" }
    },
    {
      step: 2,
      cmd: "ls -l protected/config.env && chmod u+w protected/config.env",
      stdout: "-r--r--r-- 1 sandboxuser staff 21 protected/config.env\nPermissions adjusted: mode changed to 0644.",
      cursor: { x: 140, y: 140 },
      winTitle: "Terminal — Recovering",
      doc: { h1: "Self-Healing Diagnostic", h2: "Fixing Permissions", p: "Temporarily enabled write permissions." },
      router: "Level 3: Shell Recovery Protocol",
      mcp: `{\n  "tool": "shell",\n  "command": "chmod u+w protected/config.env"\n}`,
      tokens: { prompt: 300, visual: "0", duration: "8.2ms", groundTruth: "CHMOD_OK" }
    },
    {
      step: 3,
      cmd: "echo 'RECOVERY_COMPLETED=TRUE' >> protected/config.env && chmod 444 protected/config.env",
      stdout: "Successfully appended recovery token and restored read-only lock.\n[VERIFIER] Ground-Truth Assertion PASSED.",
      cursor: { x: 200, y: 200 },
      winTitle: "Terminal — Self-Healed",
      doc: { h1: "Self-Healing Diagnostic", h2: "Healed & Verified", p: "Recovery completed and re-locked." },
      router: "Ground-Truth Verification Engine",
      mcp: `{\n  "assertion": "FileContentRegexAssertion",\n  "pattern": "RECOVERY_COMPLETED=TRUE"\n}`,
      tokens: { prompt: 380, visual: "0", duration: "14.3ms", groundTruth: "TASK_PASSED_100%" }
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

  scenarioSelect?.addEventListener('change', (e) => {
    currentScenarioKey = e.target.value in SCENARIOS ? e.target.value : 'storytold_wordcraft';
    currentStepIdx = 0;
    stopAutoPlay();
    renderStep();
  });

  prevBtn?.addEventListener('click', () => {
    stopAutoPlay();
    if (currentStepIdx > 0) {
      currentStepIdx--;
      renderStep();
    }
  });

  nextBtn?.addEventListener('click', () => {
    stopAutoPlay();
    const scenario = SCENARIOS[currentScenarioKey];
    if (currentStepIdx < scenario.length - 1) {
      currentStepIdx++;
      renderStep();
    }
  });

  playBtn?.addEventListener('click', () => {
    if (isPlaying) {
      stopAutoPlay();
    } else {
      startAutoPlay();
    }
  });

  resetBtn?.addEventListener('click', () => {
    stopAutoPlay();
    currentStepIdx = 0;
    renderStep();
  });

  somToggle?.addEventListener('change', (e) => {
    const tags = document.querySelectorAll('.som-tag');
    tags.forEach(t => t.style.display = e.target.checked ? 'block' : 'none');
  });

  // Simulator View Switcher Filter Pills (Responsive Mode)
  initViewSwitcher();

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    // Only if not typing in an input
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.key === 'ArrowRight') {
      nextBtn?.click();
    } else if (e.key === 'ArrowLeft') {
      prevBtn?.click();
    } else if (e.key === ' ' && e.target === document.body) {
      e.preventDefault();
      playBtn?.click();
    }
  });

  renderStep();
}

function initViewSwitcher() {
  const pills = document.querySelectorAll('.view-pill');
  const grid = document.getElementById('triPaneGrid');
  const paneTerminal = document.getElementById('paneTerminal');
  const paneDesktop = document.getElementById('paneDesktop');
  const paneTelemetry = document.getElementById('paneTelemetry');

  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      const view = pill.getAttribute('data-view');

      // Reset classes
      [paneTerminal, paneDesktop, paneTelemetry].forEach(pane => {
        pane.classList.remove('is-hidden', 'is-focused');
      });

      if (view === 'all') {
        // Show all
      } else if (view === 'desktop') {
        paneTerminal.classList.add('is-hidden');
        paneTelemetry.classList.add('is-hidden');
        paneDesktop.classList.add('is-focused');
      } else if (view === 'terminal') {
        paneDesktop.classList.add('is-hidden');
        paneTelemetry.classList.add('is-hidden');
        paneTerminal.classList.add('is-focused');
      } else if (view === 'telemetry') {
        paneDesktop.classList.add('is-hidden');
        paneTerminal.classList.add('is-hidden');
        paneTelemetry.classList.add('is-focused');
      }
    });
  });
}

function startAutoPlay() {
  isPlaying = true;
  const playBtn = document.getElementById('simPlayBtn');
  if (playBtn) {
    playBtn.textContent = '⏸ Pause';
    playBtn.classList.add('sim-btn-active');
  }

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
  if (playBtn) {
    playBtn.textContent = '▶ Auto-Play';
    playBtn.classList.remove('sim-btn-active');
  }
}

function renderStep() {
  const scenario = SCENARIOS[currentScenarioKey];
  const stepData = scenario[currentStepIdx];

  const currentSpan = document.getElementById('simStepCurrent');
  const totalSpan = document.getElementById('simStepTotal');
  const fillTrack = document.getElementById('simStepProgressFill');

  if (currentSpan) currentSpan.textContent = currentStepIdx + 1;
  if (totalSpan) totalSpan.textContent = scenario.length;
  if (fillTrack) {
    const pct = ((currentStepIdx + 1) / scenario.length) * 100;
    fillTrack.style.width = `${pct}%`;
  }

  // Terminal Output
  const termCmd = document.getElementById('simTermCmd');
  const termStdout = document.getElementById('simTermStdout');
  if (termCmd) termCmd.textContent = stepData.cmd;
  if (termStdout) termStdout.textContent = stepData.stdout;

  // Desktop Canvas & Window
  const winTitle = document.getElementById('simWinTitle');
  const docH1 = document.getElementById('docH1');
  const docH2 = document.getElementById('docH2');
  const docP = document.getElementById('docP');

  if (winTitle) winTitle.textContent = stepData.winTitle;
  if (docH1) docH1.textContent = stepData.doc.h1;
  if (docH2) docH2.textContent = stepData.doc.h2;
  if (docP) docP.textContent = stepData.doc.p;

  // Mouse Cursor positioning & Ripple animation
  const cursor = document.getElementById('simCursor');
  if (cursor) {
    cursor.style.top = `${stepData.cursor.y}px`;
    cursor.style.left = `${stepData.cursor.x}px`;
  }

  const ripple = document.getElementById('clickRipple');
  if (ripple) {
    ripple.classList.remove('animate');
    void ripple.offsetWidth; // Trigger reflow
    ripple.classList.add('animate');
  }

  // Telemetry & MCP inspector
  const routerDecision = document.getElementById('simRouterDecision');
  const mcpPacket = document.getElementById('simMcpPacket');
  const promptTokens = document.getElementById('simPromptTokens');
  const visualTokens = document.getElementById('simVisualTokens');
  const duration = document.getElementById('simDuration');
  const groundTruth = document.getElementById('simGroundTruth');

  if (routerDecision) routerDecision.textContent = stepData.router;
  if (mcpPacket) mcpPacket.textContent = stepData.mcp;
  if (promptTokens) promptTokens.textContent = stepData.tokens.prompt;
  if (visualTokens) visualTokens.textContent = stepData.tokens.visual;
  if (duration) duration.textContent = stepData.tokens.duration;
  if (groundTruth) groundTruth.textContent = stepData.tokens.groundTruth;
}

/* ==============================================================================
 * 4. ARCHITECTURE TABS
 * ============================================================================== */

function initArchTabs() {
  const tabs = document.querySelectorAll('.arch-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');

      const targetId = `tab-${tab.getAttribute('data-tab')}`;
      document.querySelectorAll('.arch-panel').forEach(p => p.classList.remove('active'));
      const activePanel = document.getElementById(targetId);
      if (activePanel) activePanel.classList.add('active');
    });
  });
}

/* ==============================================================================
 * 5. INTERACTIVE CONFIGURATION BUILDER
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
  const tabCli = document.getElementById('tabCli');

  let activeFormat = 'yaml';

  maxSteps?.addEventListener('input', () => {
    if (stepVal) stepVal.textContent = maxSteps.value;
    updateConfig();
  });

  maxCost?.addEventListener('input', () => {
    if (costVal) costVal.textContent = parseFloat(maxCost.value).toFixed(2);
    updateConfig();
  });

  [...sandboxRadios, providerSelect, mcpStorytold, mcpFilesystem, mcpBrowser, injDefense, frameDiffing].forEach(el => {
    el?.addEventListener('change', updateConfig);
  });

  tabYaml?.addEventListener('click', () => {
    activeFormat = 'yaml';
    [tabYaml, tabPython, tabCli].forEach(t => t?.classList.remove('active'));
    tabYaml.classList.add('active');
    updateConfig();
  });

  tabPython?.addEventListener('click', () => {
    activeFormat = 'python';
    [tabYaml, tabPython, tabCli].forEach(t => t?.classList.remove('active'));
    tabPython.classList.add('active');
    updateConfig();
  });

  tabCli?.addEventListener('click', () => {
    activeFormat = 'cli';
    [tabYaml, tabPython, tabCli].forEach(t => t?.classList.remove('active'));
    tabCli.classList.add('active');
    updateConfig();
  });

  copyBtn?.addEventListener('click', () => {
    const code = document.getElementById('configOutput')?.textContent || '';
    navigator.clipboard.writeText(code).then(() => {
      copyBtn.textContent = '✔ Copied!';
      copyBtn.classList.add('btn-copied');
      setTimeout(() => {
        copyBtn.textContent = '📋 Copy';
        copyBtn.classList.remove('btn-copied');
      }, 2000);
    });
  });

  function updateConfig() {
    const sandboxEl = document.querySelector('input[name="cfgSandbox"]:checked');
    const sandbox = sandboxEl ? sandboxEl.value : 'docker';
    const providerVal = providerSelect?.value || 'anthropic:claude-3-7-sonnet-20250219';
    const [provider, model] = providerVal.split(':');
    const steps = maxSteps?.value || '30';
    const cost = maxCost?.value || '5';
    const hasStorytold = mcpStorytold?.checked ?? true;
    const hasFilesystem = mcpFilesystem?.checked ?? true;
    const hasBrowser = mcpBrowser?.checked ?? false;
    const hasInj = injDefense?.checked ?? true;
    const hasDiff = frameDiffing?.checked ?? true;

    const outputEl = document.getElementById('configOutput');
    if (!outputEl) return;

    if (activeFormat === 'yaml') {
      outputEl.textContent = `# Nexus Computer Use Harness Configuration
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
  storytold_enabled: ${hasStorytold}
  filesystem_enabled: ${hasFilesystem}
  browser_enabled: ${hasBrowser}

guardrails:
  max_steps: ${steps}
  max_cost_usd: ${cost}.00
  command_timeout_seconds: 30
  prompt_injection_defense: ${hasInj}
  frame_diffing: ${hasDiff}
  loop_detection_window: 4
`;
    } else if (activeFormat === 'python') {
      outputEl.textContent = `import asyncio
from harness import HarnessConfig, AgentOrchestrator
from harness.config import SandboxType, LLMProviderType

async def main():
    config = HarnessConfig.load_from_env()
    config.sandbox.sandbox_type = SandboxType.${sandbox.toUpperCase()}
    config.provider = LLMProviderType.${provider.toUpperCase()}
    config.model_name = "${model}"
    config.guardrails.max_steps = ${steps}
    config.guardrails.max_cost_usd = ${cost}.00
    config.mcp.storytold_enabled = ${hasStorytold}

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
    } else {
      outputEl.textContent = `# Run via NexusCUH CLI
nexus run \\
  --task "Process data and verify with ground truth" \\
  --provider ${provider} \\
  --sandbox ${sandbox} \\
  --workspace ./workspace
`;
    }
  }

  updateConfig();
}

/* ==============================================================================
 * 6. COPY CODE BUTTONS FOR ALL CODE BLOCKS
 * ============================================================================== */

function initCopyCodeButtons() {
  document.querySelectorAll('.copy-code-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const code = btn.getAttribute('data-code');
      if (!code) return;
      navigator.clipboard.writeText(code).then(() => {
        const originalText = btn.textContent;
        btn.textContent = '✔ Copied';
        setTimeout(() => {
          btn.textContent = originalText;
        }, 1800);
      });
    });
  });
}

/* ==============================================================================
 * 7. BACK TO TOP BUTTON
 * ============================================================================== */

function initBackToTop() {
  const btn = document.getElementById('backToTop');
  if (!btn) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }, { passive: true });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ==============================================================================
 * 8. PERFORMANCE CHARTS (RESPONSIVE CHART.JS)
 * ============================================================================== */

function initCharts() {
  const isMobile = window.innerWidth < 640;
  const fontSize = isMobile ? 10 : 12;

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
            backgroundColor: 'rgba(239, 68, 68, 0.75)',
            borderColor: '#ef4444',
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: 'NexusCUH (Hybrid MCP + Shell)',
            data: [380, 720, 1850, 610],
            backgroundColor: 'rgba(99, 102, 241, 0.9)',
            borderColor: '#6366f1',
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#94a3b8',
              font: { size: fontSize, family: "'Inter', sans-serif" },
              boxWidth: 12
            }
          },
          tooltip: {
            backgroundColor: '#0f1422',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1'
          }
        },
        scales: {
          x: {
            ticks: {
              color: '#94a3b8',
              font: { size: fontSize },
              maxRotation: isMobile ? 35 : 0
            },
            grid: { color: 'rgba(255,255,255,0.05)' }
          },
          y: {
            ticks: {
              color: '#94a3b8',
              font: { size: fontSize }
            },
            grid: { color: 'rgba(255,255,255,0.05)' }
          }
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
        labels: ['New Doc', 'Insert Head', 'Insert Body', 'Save File', 'Parity Check'],
        datasets: [
          {
            label: 'GUI Clicks (s)',
            data: [4.2, 3.8, 5.1, 4.5, 3.9],
            backgroundColor: 'rgba(245, 158, 11, 0.75)',
            borderColor: '#f59e0b',
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: 'StoryTold MCP (s)',
            data: [0.012, 0.015, 0.014, 0.019, 0.009],
            backgroundColor: 'rgba(16, 185, 129, 0.9)',
            borderColor: '#10b981',
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#94a3b8',
              font: { size: fontSize, family: "'Inter', sans-serif" },
              boxWidth: 12
            }
          },
          tooltip: {
            backgroundColor: '#0f1422',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1'
          }
        },
        scales: {
          x: {
            ticks: {
              color: '#94a3b8',
              font: { size: fontSize },
              maxRotation: isMobile ? 35 : 0
            },
            grid: { color: 'rgba(255,255,255,0.05)' }
          },
          y: {
            type: 'logarithmic',
            ticks: {
              color: '#94a3b8',
              font: { size: fontSize }
            },
            grid: { color: 'rgba(255,255,255,0.05)' }
          }
        }
      }
    });
  }
}
