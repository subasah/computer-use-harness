"""
Containerized Sandbox using Docker with Xvfb virtual display, XFCE desktop, and xdotool.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

from harness.sandbox.base import BaseSandbox, CommandResult


class DockerSandbox(BaseSandbox):
    """
    Production Docker sandbox providing full system isolation, virtual X11 display,
    desktop window manager, and programmatic GUI manipulation tools.
    """

    def __init__(
        self,
        image_name: str = "nexus-computer-use-sandbox:latest",
        container_name: str = "nexus_sandbox_runtime",
        display: str = ":99",
        width: int = 1024,
        height: int = 768,
        workspace_dir: str | Path = "./workspace",
        vnc_port: int = 5900,
        novnc_port: int = 6080,
    ):
        self.image_name = image_name
        self.container_name = container_name
        self.display = display
        self.width = width
        self.height = height
        self.workspace_path = Path(workspace_dir).resolve()
        self.vnc_port = vnc_port
        self.novnc_port = novnc_port
        self._is_running = False

    def is_docker_available(self) -> bool:
        """Check if Docker CLI daemon is accessible."""
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def start(self) -> None:
        """Start or ensure the sandbox Docker container is active."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        if not self.is_docker_available():
            raise RuntimeError(
                "Docker daemon is not reachable. Please start Docker Desktop or use LocalSandbox."
            )

        # Check if container is already running
        inspect_res = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", self.container_name],
            capture_output=True,
            text=True,
        )
        if inspect_res.returncode == 0 and inspect_res.stdout.strip() == "true":
            self._is_running = True
            return

        # Remove stopped container if it exists
        subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)

        # Launch container
        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "-p", f"{self.vnc_port}:5900",
            "-p", f"{self.novnc_port}:6080",
            "-v", f"{self.workspace_path}:/home/sandboxuser/workspace",
            "-e", f"DISPLAY={self.display}",
            "-e", f"RESOLUTION={self.width}x{self.height}x24",
            self.image_name,
        ]

        run_res = subprocess.run(cmd, capture_output=True, text=True)
        if run_res.returncode != 0:
            raise RuntimeError(f"Failed to launch Docker sandbox container: {run_res.stderr}")

        # Wait briefly for Xvfb and window manager to initialize
        time.sleep(2.0)
        self._is_running = True

    def stop(self) -> None:
        """Stop and tear down the Docker container."""
        if self._is_running:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self._is_running = False

    def reset(self) -> None:
        """Reset workspace and restart the X11 session."""
        self.exec_command("rm -rf /home/sandboxuser/workspace/*")
        # Reset mouse cursor to screen center
        self.mouse_move(self.width // 2, self.height // 2)

    def exec_command(
        self,
        command: str,
        timeout_seconds: Optional[int] = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        work_dir = cwd or "/home/sandboxuser/workspace"
        env_args = []
        if env:
            for k, v in env.items():
                env_args.extend(["-e", f"{k}={v}"])

        docker_cmd = [
            "docker", "exec",
            "-i",
            "-w", work_dir,
            "-e", f"DISPLAY={self.display}",
            *env_args,
            self.container_name,
            "bash", "-c", command,
        ]

        start_time = time.time()
        try:
            res = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            duration_ms = (time.time() - start_time) * 1000
            return CommandResult(
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
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

    def read_file(self, path: str) -> str:
        res = self.exec_command(f"cat '{path}'")
        if res.exit_code != 0:
            raise FileNotFoundError(f"File '{path}' could not be read: {res.stderr}")
        return res.stdout

    def read_file_bytes(self, path: str) -> bytes:
        temp_dest = f"/tmp/nexus_cp_{int(time.time() * 1000)}"
        subprocess.run(["docker", "cp", f"{self.container_name}:{path}", temp_dest], check=True)
        data = Path(temp_dest).read_bytes()
        os.remove(temp_dest)
        return data

    def write_file(self, path: str, content: str | bytes) -> None:
        parent = os.path.dirname(path)
        if parent:
            self.exec_command(f"mkdir -p '{parent}'")
        temp_src = f"/tmp/nexus_src_{int(time.time() * 1000)}"
        if isinstance(content, str):
            Path(temp_src).write_text(content, encoding="utf-8")
        else:
            Path(temp_src).write_bytes(content)
        subprocess.run(["docker", "cp", temp_src, f"{self.container_name}:{path}"], check=True)
        os.remove(temp_src)

    def file_exists(self, path: str) -> bool:
        res = self.exec_command(f"test -e '{path}'")
        return res.exit_code == 0

    def take_screenshot(self) -> bytes:
        """Capture screenshot inside container using scrot or ImageMagick import."""
        container_tmp = f"/tmp/screen_{int(time.time() * 1000)}.png"
        res = self.exec_command(f"scrot '{container_tmp}' || import -window root '{container_tmp}'")
        if res.exit_code != 0:
            # Fallback using xwd and convert
            self.exec_command(f"xwd -root -silent -display {self.display} | convert xwd:- '{container_tmp}'")

        data = self.read_file_bytes(container_tmp)
        self.exec_command(f"rm -f '{container_tmp}'")
        return data

    def mouse_click(self, x: int, y: int, button: str = "left", double: bool = False) -> None:
        btn_num = 1 if button == "left" else (3 if button == "right" else 2)
        click_type = "click --repeat 2 --delay 100" if double else "click"
        self.exec_command(f"xdotool mousemove --sync {x} {y} {click_type} {btn_num}")

    def mouse_move(self, x: int, y: int) -> None:
        self.exec_command(f"xdotool mousemove --sync {x} {y}")

    def mouse_scroll(self, amount: int) -> None:
        # xdotool mouse button 4 is scroll up, 5 is scroll down
        btn = 4 if amount > 0 else 5
        repeats = abs(amount)
        self.exec_command(f"xdotool click --repeat {repeats} {btn}")

    def key_down(self, key: str) -> None:
        self.exec_command(f"xdotool keydown {key}")

    def key_up(self, key: str) -> None:
        self.exec_command(f"xdotool keyup {key}")

    def type_text(self, text: str) -> None:
        escaped = text.replace("'", "'\\''")
        self.exec_command(f"xdotool type --delay 12 '{escaped}'")

    def key_combination(self, combo: str) -> None:
        # Transform combos like 'ctrl+s' to 'ctrl+s' for xdotool
        self.exec_command(f"xdotool key {combo}")
