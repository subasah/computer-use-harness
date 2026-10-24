"""
Deterministic Snapshot and State Restoration Manager for Sandboxes.
"""

from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Optional


class StateManager:
    """
    Manages snapshots of sandbox directories to enable deterministic resets
    before and after benchmark evaluation runs.
    """

    def __init__(self, workspace_path: str | Path):
        self.workspace_path = Path(workspace_path).resolve()
        self.snapshot_tar_path: Optional[Path] = None
        self._temp_dir: Optional[str] = None

    def create_snapshot(self) -> Path:
        """Capture the current workspace state as a compressed snapshot archive."""
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="nexus_snapshot_")

        self.snapshot_tar_path = Path(self._temp_dir) / "pristine_state.tar.gz"

        # Ensure directory exists before archiving
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        with tarfile.open(self.snapshot_tar_path, "w:gz") as tar:
            for item in self.workspace_path.iterdir():
                tar.add(item, arcname=item.name)

        return self.snapshot_tar_path

    def restore_snapshot(self) -> None:
        """Wipe current workspace state and restore from the snapshot archive."""
        if not self.snapshot_tar_path or not self.snapshot_tar_path.exists():
            # If no snapshot exists, simply clear the workspace directory
            self.clear_workspace()
            return

        self.clear_workspace()

        with tarfile.open(self.snapshot_tar_path, "r:gz") as tar:
            try:
                tar.extractall(path=self.workspace_path, filter="data")
            except TypeError:
                tar.extractall(path=self.workspace_path)

    def clear_workspace(self) -> None:
        """Remove all files and directories in the workspace."""
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            return

        for item in self.workspace_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink()
                except OSError:
                    pass

    def cleanup(self) -> None:
        """Tear down temporary snapshot directories."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
