"""
Unit tests for Sandbox subsystem.
"""

import tempfile

import pytest

from harness.sandbox.local_sandbox import LocalSandbox


@pytest.fixture
def sandbox():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = LocalSandbox(workspace_dir=tmpdir, width=800, height=600)
        sb.start()
        yield sb
        sb.stop()


def test_sandbox_file_operations(sandbox: LocalSandbox):
    test_file = "test_dir/hello.txt"
    sandbox.write_file(test_file, "Hello, NexusCUH!")

    assert sandbox.file_exists(test_file)
    assert sandbox.read_file(test_file) == "Hello, NexusCUH!"


def test_sandbox_exec_command_success(sandbox: LocalSandbox):
    res = sandbox.exec_command("echo 'Agent Sandbox Active'")
    assert res.exit_code == 0
    assert "Agent Sandbox Active" in res.stdout
    assert not res.timed_out


def test_sandbox_exec_command_timeout(sandbox: LocalSandbox):
    res = sandbox.exec_command("sleep 3", timeout_seconds=1)
    assert res.timed_out
    assert res.exit_code == 124


def test_sandbox_screenshot(sandbox: LocalSandbox):
    img_bytes = sandbox.take_screenshot()
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 100
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_sandbox_gui_events(sandbox: LocalSandbox):
    sandbox.mouse_click(100, 200, button="left")
    sandbox.type_text("Hello World")

    assert len(sandbox.event_log) == 2
    assert sandbox.event_log[0]["event"] == "click"
    assert sandbox.event_log[0]["x"] == 100
    assert sandbox.event_log[0]["y"] == 200
    assert sandbox.event_log[1]["event"] == "type"
    assert sandbox.event_log[1]["text"] == "Hello World"


def test_sandbox_snapshot_reset(sandbox: LocalSandbox):
    sandbox.write_file("file1.txt", "Initial file")
    sandbox.state_manager.create_snapshot()

    sandbox.write_file("file2.txt", "Ephemeral file")
    assert sandbox.file_exists("file2.txt")

    sandbox.reset()
    assert sandbox.file_exists("file1.txt")
    assert not sandbox.file_exists("file2.txt")
