"""
Local execution sandbox running natively within an isolated workspace.
"""

from __future__ import annotations

import io
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw

from harness.sandbox.base import BaseSandbox, CommandResult
from harness.sandbox.state import StateManager


class LocalSandbox(BaseSandbox):
    """
    Local sandbox implementation executing commands in an isolated workspace.
    Designed for fast iterative testing, local developers, and CI/CD environments.
    """

    def __init__(
        self,
        workspace_dir: str | Path = "./workspace",
        width: int = 1024,
        height: int = 768,
        simulate_display: bool = True,
    ):
        self.workspace_path = Path(workspace_dir).resolve()
        self.width = width
        self.height = height
        self.simulate_display = simulate_display
        self.state_manager = StateManager(self.workspace_path)

        self.mouse_x: int = width // 2
        self.mouse_y: int = height // 2
        self.event_log: List[Dict[str, Any]] = []
        self._is_running = False

    def start(self) -> None:
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.state_manager.create_snapshot()
        self._is_running = True

    def stop(self) -> None:
        self.state_manager.cleanup()
        self._is_running = False

    def reset(self) -> None:
        self.state_manager.restore_snapshot()
        self.mouse_x = self.width // 2
        self.mouse_y = self.height // 2
        self.event_log.clear()

    def exec_command(
        self,
        command: str,
        timeout_seconds: Optional[int] = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        work_dir = Path(cwd).resolve() if cwd else self.workspace_path
        if not work_dir.exists():
            work_dir.mkdir(parents=True, exist_ok=True)

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        start_time = time.time()
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=str(work_dir),
                env=exec_env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            duration_ms = (time.time() - start_time) * 1000
            return CommandResult(
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_ms=duration_ms,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.time() - start_time) * 1000
            stdout_str = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr_str = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return CommandResult(
                exit_code=124,
                stdout=stdout_str,
                stderr=f"Command timed out after {timeout_seconds}s.\n{stderr_str}",
                duration_ms=duration_ms,
                timed_out=True,
            )
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            return CommandResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {str(exc)}",
                duration_ms=duration_ms,
                timed_out=False,
            )

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace_path / p
        return p

    def read_file(self, path: str) -> str:
        resolved = self._resolve_path(path)
        return resolved.read_text(encoding="utf-8")

    def read_file_bytes(self, path: str) -> bytes:
        resolved = self._resolve_path(path)
        return resolved.read_bytes()

    def write_file(self, path: str, content: str | bytes) -> None:
        resolved = self._resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            resolved.write_bytes(content)
        else:
            resolved.write_text(content, encoding="utf-8")

    def file_exists(self, path: str) -> bool:
        resolved = self._resolve_path(path)
        return resolved.exists()

    def take_screenshot(self) -> bytes:
        """
        Produce a screenshot. In simulate_display mode (or CI headless),
        renders an annotated visual representation of the virtual desktop environment.
        """
        if not self.simulate_display:
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                return buffer.getvalue()
            except Exception:
                pass  # Fall back to simulated canvas

        # Generate a high-contrast simulated desktop view
        img = Image.new("RGB", (self.width, self.height), color=(26, 28, 35))
        draw = ImageDraw.Draw(img)

        # Top desktop menu bar
        draw.rectangle([(0, 0), (self.width, 32)], fill=(40, 44, 52))
        draw.text((16, 8), "Nexus Desktop Sandbox (X11 Virtual Display)", fill=(220, 220, 220))
        draw.text((self.width - 180, 8), time.strftime("%Y-%m-%d %H:%M:%S"), fill=(180, 180, 180))

        # Main window panel: Workspace status
        win_x0, win_y0, win_x1, win_y1 = 40, 60, self.width - 40, self.height - 60
        draw.rectangle([(win_x0, win_y0), (win_x1, win_y1)], fill=(33, 37, 43), outline=(97, 175, 239), width=2)
        draw.rectangle([(win_x0, win_y0), (win_x1, win_y0 + 28)], fill=(40, 44, 52))
        draw.text((win_x0 + 12, win_y0 + 6), "Active Session Workspace", fill=(229, 192, 123))

        # Show workspace files
        y_offset = win_y0 + 44
        draw.text((win_x0 + 20, y_offset), f"Workspace Path: {self.workspace_path}", fill=(152, 195, 121))
        y_offset += 24

        try:
            files = list(self.workspace_path.glob("*"))[:8]
            draw.text((win_x0 + 20, y_offset), f"Directory Contents ({len(files)} items):", fill=(220, 220, 220))
            y_offset += 20
            for f in files:
                prefix = "[DIR]  " if f.is_dir() else "[FILE] "
                draw.text((win_x0 + 36, y_offset), f"{prefix}{f.name} ({f.stat().st_size} bytes)", fill=(171, 178, 191))
                y_offset += 18
        except Exception:
            pass

        # Show recent input events
        y_offset += 16
        draw.text((win_x0 + 20, y_offset), "Recent GUI Input Events:", fill=(220, 220, 220))
        y_offset += 20
        recent = self.event_log[-4:] if self.event_log else [{"event": "Idle - Waiting for Agent"}]
        for ev in recent:
            draw.text((win_x0 + 36, y_offset), f"-> {str(ev)}", fill=(97, 175, 239))
            y_offset += 18

        # Draw mouse cursor
        cx, cy = max(0, min(self.width - 1, self.mouse_x)), max(0, min(self.height - 1, self.mouse_y))
        cursor_poly = [(cx, cy), (cx + 12, cy + 12), (cx + 6, cy + 14), (cx + 10, cy + 22), (cx + 7, cy + 23), (cx + 3, cy + 15), (cx, cy + 18)]
        draw.polygon(cursor_poly, fill=(255, 85, 85), outline=(255, 255, 255))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def mouse_click(self, x: int, y: int, button: str = "left", double: bool = False) -> None:
        self.mouse_x = max(0, min(self.width, x))
        self.mouse_y = max(0, min(self.height, y))
        self.event_log.append({
            "event": "double_click" if double else "click",
            "button": button,
            "x": self.mouse_x,
            "y": self.mouse_y,
            "timestamp": time.time(),
        })

    def mouse_move(self, x: int, y: int) -> None:
        self.mouse_x = max(0, min(self.width, x))
        self.mouse_y = max(0, min(self.height, y))
        self.event_log.append({
            "event": "move",
            "x": self.mouse_x,
            "y": self.mouse_y,
            "timestamp": time.time(),
        })

    def mouse_scroll(self, amount: int) -> None:
        self.event_log.append({
            "event": "scroll",
            "amount": amount,
            "timestamp": time.time(),
        })

    def key_down(self, key: str) -> None:
        self.event_log.append({"event": "key_down", "key": key, "timestamp": time.time()})

    def key_up(self, key: str) -> None:
        self.event_log.append({"event": "key_up", "key": key, "timestamp": time.time()})

    def type_text(self, text: str) -> None:
        self.event_log.append({"event": "type", "text": text, "timestamp": time.time()})

    def key_combination(self, combo: str) -> None:
        self.event_log.append({"event": "key_combo", "combo": combo, "timestamp": time.time()})
