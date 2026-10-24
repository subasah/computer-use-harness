"""
Master Agent Orchestrator: Unified ReAct Loop, Context Budgeting, and Safe Execution.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.agent.providers import BaseLLMProvider, LLMResponse, MockProvider
from harness.agent.router import CognitiveToolRouter
from harness.config import HarnessConfig
from harness.guardrails.budget import BudgetEnforcer
from harness.guardrails.injection import PromptInjectionDetector
from harness.guardrails.loop_detector import LoopDetector
from harness.guardrails.security import SecurityPolicy
from harness.mcp.server_manager import MCPServerManager
from harness.sandbox.base import BaseSandbox
from harness.sandbox.docker_sandbox import DockerSandbox
from harness.sandbox.local_sandbox import LocalSandbox
from harness.tools.base import BaseTool, ToolResult
from harness.tools.filesystem import FileSystemTool
from harness.tools.gui import GUITool
from harness.tools.shell import ShellTool
from harness.verification.verifier import MultiModalVerifier, VerificationReport

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Production-grade Computer Use Agent Orchestrator.
    Coordinates sandbox environments, Model Context Protocol (MCP) integrations,
    multimodal tool execution, safety guardrails, and ground-truth verification.
    """

    def __init__(
        self,
        config: HarnessConfig,
        provider: Optional[BaseLLMProvider] = None,
        sandbox: Optional[BaseSandbox] = None,
        verifier: Optional[MultiModalVerifier] = None,
    ):
        self.config = config
        self.provider = provider or MockProvider()

        # Initialize Sandbox
        if sandbox:
            self.sandbox = sandbox
        elif config.sandbox.sandbox_type == "docker":
            self.sandbox = DockerSandbox(
                image_name=config.sandbox.docker_image,
                container_name=config.sandbox.docker_container_name,
                display=config.sandbox.display,
                width=config.sandbox.resolution.width,
                height=config.sandbox.resolution.height,
                workspace_dir=config.sandbox.workspace_dir,
                vnc_port=config.sandbox.vnc_port,
                novnc_port=config.sandbox.novnc_port,
            )
        else:
            self.sandbox = LocalSandbox(
                workspace_dir=config.sandbox.workspace_dir,
                width=config.sandbox.resolution.width,
                height=config.sandbox.resolution.height,
            )

        # Initialize MCP Manager
        self.mcp_manager = MCPServerManager(config.mcp, workspace_dir=config.sandbox.workspace_dir)

        # Initialize Tools
        self.tools: Dict[str, BaseTool] = {}
        self._init_built_in_tools()

        # Initialize Guardrails
        self.security_policy = SecurityPolicy(blocked_patterns=config.guardrails.blocked_commands)
        self.injection_detector = PromptInjectionDetector()
        self.loop_detector = LoopDetector(window_size=config.guardrails.loop_detection_window)
        self.budget_enforcer = BudgetEnforcer(
            max_steps=config.guardrails.max_steps,
            max_cost_usd=config.guardrails.max_cost_usd,
        )

        self.verifier = verifier or MultiModalVerifier()
        self.router = CognitiveToolRouter(list(self.tools.values()))

        # Trace & Run History
        self.run_history: List[Dict[str, Any]] = []

    def _init_built_in_tools(self) -> None:
        shell_tool = ShellTool(self.sandbox)
        gui_tool = GUITool(
            self.sandbox,
            target_width=self.config.sandbox.resolution.width,
            target_height=self.config.sandbox.resolution.height,
        )
        fs_tool = FileSystemTool(self.sandbox)

        for t in [shell_tool, gui_tool, fs_tool]:
            self.tools[t.name] = t

    async def initialize(self) -> None:
        """Boot up sandbox and start MCP servers."""
        self.sandbox.start()
        await self.mcp_manager.start_all()

        # Register MCP tools dynamically
        for mcp_tool in self.mcp_manager.get_agent_tools():
            self.tools[mcp_tool.name] = mcp_tool

        # Refresh cognitive router with all combined tools
        self.router = CognitiveToolRouter(list(self.tools.values()))

    async def shutdown(self) -> None:
        """Tear down all processes and release resources."""
        await self.mcp_manager.stop_all()
        self.sandbox.stop()

    def _build_system_prompt(self, task_instruction: str) -> str:
        guidance = self.router.get_tool_routing_guidance()
        return (
            "You are an expert Autonomous Computer-Use Agent operating inside an isolated sandbox.\n"
            "Your objective is to complete the specified task reliably, efficiently, and safely.\n\n"
            f"{guidance}\n\n"
            "OPERATING GUIDELINES:\n"
            "- Always verify task outcomes with ground truth (files, databases, MCP states).\n"
            "- Do not guess coordinates when an MCP API tool or shell script can perform the action directly.\n"
            "- When an error occurs, analyze the error message and pivot to a recovery strategy.\n"
            "- Signal task completion when all verification criteria are met.\n\n"
            f"PRIMARY TASK OBJECTIVE:\n{task_instruction}"
        )

    def _prune_context_images(self, messages: List[Dict[str, Any]], keep_latest_n: int = 1) -> None:
        """
        Prune older image frames from conversation history to stay strictly within
        visual token budgets while retaining recent spatial context.
        """
        image_count = 0
        # Traverse messages backwards
        for msg in reversed(messages):
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image":
                        image_count += 1
                        if image_count > keep_latest_n:
                            # Replace image with lightweight token-saving reference
                            item["type"] = "text"
                            item.pop("source", None)
                            item["text"] = "[Historical frame pruned to save context window tokens]"

    async def run_task(self, task_instruction: str) -> Dict[str, Any]:
        """
        Execute an end-to-end computer use task through the ReAct loop.
        """
        system_prompt = self._build_system_prompt(task_instruction)
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": task_instruction}
        ]

        active_tools_schema = [t.to_anthropic_schema() for t in self.tools.values()]
        run_start_time = time.time()
        self.run_history.clear()
        self.loop_detector.reset()

        logger.info(f"Starting Task: {task_instruction[:80]}...")
        task_completed = False
        termination_reason = "in_progress"

        while not task_completed:
            step_num = self.budget_enforcer.current_step + 1

            # 1. Query LLM Provider
            llm_resp: LLMResponse = await self.provider.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                tools=active_tools_schema,
            )

            # Record budget usage
            budget_exceeded, reason = self.budget_enforcer.record_step(
                prompt_tokens=llm_resp.prompt_tokens,
                completion_tokens=llm_resp.completion_tokens,
            )

            if budget_exceeded:
                termination_reason = reason or "Budget exceeded"
                logger.warning(f"Termination: {termination_reason}")
                break

            # If no tool calls requested, agent declared completion or stopped
            if not llm_resp.tool_calls:
                task_completed = True
                termination_reason = "Agent declared completion"
                self.run_history.append({
                    "step": step_num,
                    "agent_text": llm_resp.text,
                    "tool_calls": [],
                })
                break

            # Add Assistant turn to history
            assistant_content: List[Dict[str, Any]] = []
            if llm_resp.text:
                assistant_content.append({"type": "text", "text": llm_resp.text})
            for tc in llm_resp.tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            messages.append({"role": "assistant", "content": assistant_content})

            # 2. Execute requested tool calls with Guardrail checks
            tool_results_blocks: List[Dict[str, Any]] = []

            for tc in llm_resp.tool_calls:
                tool_name = tc.name
                tool_args = tc.arguments
                step_log: Dict[str, Any] = {
                    "step": step_num,
                    "tool_name": tool_name,
                    "arguments": tool_args,
                }

                # Guardrail A: Security Command Policy
                if tool_name == "shell" and "command" in tool_args:
                    is_safe, sec_reason = self.security_policy.validate_command(tool_args["command"])
                    if not is_safe:
                        res = ToolResult(
                            content=f"Security Violation: {sec_reason}",
                            is_error=True,
                        )
                        tool_results_blocks.extend(res.to_anthropic_content(tc.id))
                        step_log["result"] = res.content
                        step_log["is_error"] = True
                        self.run_history.append(step_log)
                        continue

                # Guardrail B: Loop Detection
                is_loop, loop_warning = self.loop_detector.record_step(tool_name, tool_args)
                if is_loop:
                    res = ToolResult(content=f"Harness Warning: {loop_warning}", is_error=True)
                    tool_results_blocks.extend(res.to_anthropic_content(tc.id))
                    step_log["result"] = res.content
                    step_log["is_error"] = True
                    self.run_history.append(step_log)
                    continue

                # Dispatch tool
                tool = self.tools.get(tool_name)
                if not tool:
                    res = ToolResult(content=f"Error: Tool '{tool_name}' not found.", is_error=True)
                else:
                    try:
                        res = await tool.execute(**tool_args)
                        # Guardrail C: Prompt Injection Sanitization
                        if res.content and self.config.guardrails.prompt_injection_defense:
                            res.content = self.injection_detector.sanitize_observation(res.content)
                        if res.image_bytes:
                            self.budget_enforcer.total_image_frames += 1
                    except Exception as exc:
                        res = ToolResult(content=f"Tool Execution Exception: {str(exc)}", is_error=True)

                step_log["result"] = res.content
                step_log["is_error"] = res.is_error
                step_log["has_image"] = res.image_bytes is not None
                self.run_history.append(step_log)

                tool_results_blocks.extend(res.to_anthropic_content(tc.id))

            # Add User / Tool Result turn to messages
            messages.append({"role": "user", "content": tool_results_blocks})

            # Prune old images to conserve context tokens
            self._prune_context_images(messages, keep_latest_n=1)

        # 3. Ground-truth Post-Run Verification
        verification_report: VerificationReport = await self.verifier.verify(self.sandbox, self.mcp_manager)

        total_duration = time.time() - run_start_time
        summary = {
            "success": verification_report.passed,
            "termination_reason": termination_reason,
            "duration_seconds": round(total_duration, 2),
            "verification": verification_report.to_dict(),
            "budget": self.budget_enforcer.get_summary(),
            "steps_count": len(self.run_history),
            "run_history": self.run_history,
        }

        if self.config.record_runs:
            self._persist_run_log(summary)

        return summary

    def _persist_run_log(self, summary: Dict[str, Any]) -> None:
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        filename = log_dir / f"run_{int(time.time())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
