"""
Unit tests for GUITool and visual frame diffing.
"""

import tempfile

import pytest

from harness.sandbox.local_sandbox import LocalSandbox
from harness.tools.gui import GUITool


@pytest.fixture
def gui_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = LocalSandbox(workspace_dir=tmpdir, width=800, height=600)
        sb.start()
        tool = GUITool(sandbox=sb, enable_frame_diffing=True)
        yield tool
        sb.stop()


@pytest.mark.asyncio
async def test_gui_tool_screenshot(gui_tool: GUITool):
    res = await gui_tool.execute(action="screenshot")
    assert not res.is_error
    assert res.image_bytes is not None
    assert len(res.image_bytes) > 100


@pytest.mark.asyncio
async def test_gui_tool_mouse_and_typing(gui_tool: GUITool):
    res = await gui_tool.execute(action="left_click", coordinate=[150, 250])
    assert not res.is_error

    res_type = await gui_tool.execute(action="type", text="Automated Input")
    assert not res_type.is_error
