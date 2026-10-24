"""
Shell tool providing stateful, windowed, and secure command execution in the sandbox.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from harness.sandbox.base import BaseSandbox, CommandResult
from harness.tools.base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """
    Executes terminal commands inside the sandbox with output windowing,
    timeout guardrails, and persistent working directory tracking.
    """

    name = "shell"
    description = (
        "Run commands in a bash shell inside the sandbox. Supports directory navigation, "
        "file manipulation, process execution, and builds. Output is automatically windowed "
        "if it exceeds token limits."
    )

    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash shell command line to execute.",
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Maximum execution time before timeout in seconds (default: 30).",
                "default": 30,
            },
            "cwd": {
                "type": "string",
                "description": "Optional working directory to execute the command from.",
            },
        },
        "required": ["command"],
    }

    def __init__(
        self,
        sandbox: BaseSandbox,
        max_output_chars: int = 8000,
        head_lines: int = 50,
        tail_lines: int = 50,
    ):
        self.sandbox = sandbox
        self.max_output_chars = max_output_chars
        self.head_lines = head_lines
        self.tail_lines = tail_lines
        self.current_cwd: Optional[str] = None
        self.env_vars: Dict[str, str] = {}

    def _truncate_output(self, raw_output: str) -> tuple[str, bool]:
        """
        Intelligently window massive command outputs, preserving head and tail lines
        along with precise truncation metrics to prevent context blowup.
        """
        if len(raw_output) <= self.max_output_chars:
            return raw_output, False

        lines = raw_output.splitlines(keepends=True)
        total_lines = len(lines)

        if total_lines <= (self.head_lines + self.tail_lines):
            # Line count is small, but individual lines are massive
            truncated = raw_output[: self.max_output_chars // 2] + "\n... [Output Truncated] ...\n" + raw_output[-self.max_output_chars // 2 :]
            return truncated, True

        head_part = "".join(lines[: self.head_lines])
        tail_part = "".join(lines[-self.tail_lines :])
        omitted_lines = total_lines - (self.head_lines + self.tail_lines)
        omitted_chars = len(raw_output) - (len(head_part) + len(tail_part))

        banner = (
            f"\n\n[... NexusCUH Output Windowed: Omitted {omitted_lines} lines "
            f"({omitted_chars} bytes) to protect context window ...]\n\n"
        )
        return head_part + banner + tail_part, True

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command", "").strip()
        timeout = kwargs.get("timeout_seconds", 30)
        target_cwd = kwargs.get("cwd") or self.current_cwd

        if not command:
            return ToolResult(content="Error: Empty command string provided.", is_error=True)

        # Execute in sandbox
        result: CommandResult = self.sandbox.exec_command(
            command=command,
            timeout_seconds=timeout,
            cwd=target_cwd,
            env=self.env_vars,
        )

        combined_output = ""
        if result.stdout:
            combined_output += result.stdout
        if result.stderr:
            if combined_output:
                combined_output += "\n--- STDERR ---\n"
            combined_output += result.stderr

        formatted_output, truncated = self._truncate_output(combined_output)

        status_msg = f"[Exit Code: {result.exit_code} | Duration: {result.duration_ms:.1f}ms]"
        if result.timed_out:
            status_msg += f" [TIMEOUT: Exceeded {timeout}s]"

        final_content = f"{status_msg}\n{formatted_output}" if formatted_output.strip() else status_msg

        return ToolResult(
            content=final_content,
            is_error=not result.is_success,
            metadata={
                "exit_code": result.exit_code,
                "duration_ms": result.duration_ms,
                "timed_out": result.timed_out,
                "truncated": truncated,
            },
        )
