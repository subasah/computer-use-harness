"""
Sandbox abstraction layer for isolated agent execution.
"""

from harness.sandbox.base import BaseSandbox, CommandResult
from harness.sandbox.docker_sandbox import DockerSandbox
from harness.sandbox.local_sandbox import LocalSandbox
from harness.sandbox.state import StateManager

__all__ = ["BaseSandbox", "CommandResult", "LocalSandbox", "DockerSandbox", "StateManager"]
