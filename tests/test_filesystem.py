"""
Unit tests for FileSystemTool.
"""

import tempfile

import pytest

from harness.sandbox.local_sandbox import LocalSandbox
from harness.tools.filesystem import FileSystemTool


@pytest.fixture
def fs_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = LocalSandbox(workspace_dir=tmpdir)
        sb.start()
        tool = FileSystemTool(sandbox=sb)
        yield tool
        sb.stop()


@pytest.mark.asyncio
async def test_filesystem_write_and_read(fs_tool: FileSystemTool):
    write_res = await fs_tool.execute(action="write", path="notes.txt", content="Sample Line 1\n")
    assert not write_res.is_error

    read_res = await fs_tool.execute(action="read", path="notes.txt")
    assert not read_res.is_error
    assert read_res.content == "Sample Line 1\n"


@pytest.mark.asyncio
async def test_filesystem_str_replace(fs_tool: FileSystemTool):
    await fs_tool.execute(action="write", path="config.yaml", content="timeout: 30\nmode: debug\n")
    replace_res = await fs_tool.execute(
        action="str_replace",
        path="config.yaml",
        old_str="mode: debug",
        new_str="mode: production",
    )
    assert not replace_res.is_error

    read_res = await fs_tool.execute(action="read", path="config.yaml")
    assert "mode: production" in read_res.content


@pytest.mark.asyncio
async def test_filesystem_checksum(fs_tool: FileSystemTool):
    await fs_tool.execute(action="write", path="data.bin", content="DeterministicContent")
    chk_res = await fs_tool.execute(action="checksum", path="data.bin")
    assert not chk_res.is_error
    assert len(chk_res.content) == 64  # SHA-256 hex length
