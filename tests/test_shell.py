"""
Unit tests for ShellTool and windowed output pagination.
"""

import tempfile

import pytest

from harness.sandbox.local_sandbox import LocalSandbox
from harness.tools.shell import ShellTool


@pytest.fixture
def shell_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = LocalSandbox(workspace_dir=tmpdir)
        sb.start()
        tool = ShellTool(sandbox=sb, max_output_chars=500, head_lines=5, tail_lines=5)
        yield tool
        sb.stop()


@pytest.mark.asyncio
async def test_shell_tool_simple_execution(shell_tool: ShellTool):
    result = await shell_tool.execute(command="echo 'Testing shell tool'")
    assert not result.is_error
    assert "Testing shell tool" in result.content
    assert result.metadata["exit_code"] == 0


@pytest.mark.asyncio
async def test_shell_tool_truncation(shell_tool: ShellTool):
    # Generate 100 lines of output which exceeds 500 characters
    cmd = "python3 -c 'for i in range(100): print(f\"Line {i}: data data data data data\")'"
    result = await shell_tool.execute(command=cmd)

    assert not result.is_error
    assert result.metadata["truncated"] is True
    assert "NexusCUH Output Windowed" in result.content
    assert "Line 0:" in result.content  # Head preserved
    assert "Line 99:" in result.content  # Tail preserved


@pytest.mark.asyncio
async def test_shell_tool_empty_command(shell_tool: ShellTool):
    result = await shell_tool.execute(command="  ")
    assert result.is_error
    assert "Empty command" in result.content
