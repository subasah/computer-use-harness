"""
Abstract base class and contract for execution sandboxes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CommandResult:
    """Execution outcome of a shell command."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    truncated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class BaseSandbox(ABC):
    """
    Abstract contract for an isolated execution sandbox.
    Supports command execution, file read/write, display/screenshot capture,
    and input event simulation (mouse/keyboard).
    """

    @abstractmethod
    def start(self) -> None:
        """Initialize and start the sandbox environment."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Tear down and release sandbox resources."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset sandbox filesystem and display to pristine snapshot state."""
        pass

    @abstractmethod
    def exec_command(
        self,
        command: str,
        timeout_seconds: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """Execute a shell command inside the sandbox."""
        pass

    @abstractmethod
    def read_file(self, path: str) -> str:
        """Read textual content of a file inside the sandbox."""
        pass

    @abstractmethod
    def read_file_bytes(self, path: str) -> bytes:
        """Read raw binary content of a file inside the sandbox."""
        pass

    @abstractmethod
    def write_file(self, path: str, content: str | bytes) -> None:
        """Write content to a file inside the sandbox."""
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file or directory exists inside the sandbox."""
        pass

    @abstractmethod
    def take_screenshot(self) -> bytes:
        """Capture the current visual state of the display as PNG bytes."""
        pass

    @abstractmethod
    def mouse_click(self, x: int, y: int, button: str = "left", double: bool = False) -> None:
        """Simulate a mouse click event at given coordinates."""
        pass

    @abstractmethod
    def mouse_move(self, x: int, y: int) -> None:
        """Simulate moving the mouse cursor to given coordinates."""
        pass

    @abstractmethod
    def mouse_scroll(self, amount: int) -> None:
        """Simulate scrolling the mouse wheel."""
        pass

    @abstractmethod
    def key_down(self, key: str) -> None:
        """Simulate pressing down a key."""
        pass

    @abstractmethod
    def key_up(self, key: str) -> None:
        """Simulate releasing a key."""
        pass

    @abstractmethod
    def type_text(self, text: str) -> None:
        """Simulate typing a string of text."""
        pass

    @abstractmethod
    def key_combination(self, combo: str) -> None:
        """Simulate a keyboard shortcut (e.g. 'ctrl+s', 'alt+tab')."""
        pass
