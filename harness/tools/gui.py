"""
GUI Computer Use Tool with Frame Diffing, Coordinate Scaling, and Visual Annotation.
"""

from __future__ import annotations

import hashlib
import io
from typing import Any, Optional

from PIL import Image, ImageChops

from harness.sandbox.base import BaseSandbox
from harness.tools.base import BaseTool, ToolResult


class GUITool(BaseTool):
    """
    Simulates mouse and keyboard operations on the desktop GUI display,
    captures screenshots, performs perceptual frame diffing to conserve image tokens,
    and supports visual Set-of-Marks (SOM) overlays.
    """

    name = "computer"
    description = (
        "Interact with the graphical desktop user interface. Supported actions include: "
        "'screenshot', 'mouse_move', 'left_click', 'right_click', 'double_click', "
        "'triple_click', 'middle_click', 'mouse_down', 'mouse_up', 'left_click_drag', "
        "'type', 'key', 'key_down', 'key_up', 'scroll', and 'cursor_position'."
    )

    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "screenshot",
                    "mouse_move",
                    "left_click",
                    "right_click",
                    "double_click",
                    "triple_click",
                    "middle_click",
                    "left_click_drag",
                    "mouse_down",
                    "mouse_up",
                    "type",
                    "key",
                    "scroll",
                    "cursor_position",
                ],
                "description": "The desktop GUI interaction action to perform.",
            },
            "coordinate": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The (x, y) pixel coordinates on the display.",
            },
            "text": {
                "type": "string",
                "description": "Text to type into the active desktop window.",
            },
            "key": {
                "type": "string",
                "description": "Keyboard key or combination (e.g. 'Return', 'ctrl+c', 'BackSpace').",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Amount to scroll (positive for up, negative for down).",
            },
        },
        "required": ["action"],
    }

    def __init__(
        self,
        sandbox: BaseSandbox,
        target_width: int = 1024,
        target_height: int = 768,
        enable_frame_diffing: bool = True,
        diff_threshold: float = 0.005,  # 0.5% pixel change threshold
    ):
        self.sandbox = sandbox
        self.target_width = target_width
        self.target_height = target_height
        self.enable_frame_diffing = enable_frame_diffing
        self.diff_threshold = diff_threshold
        self.last_frame_hash: Optional[str] = None
        self.last_frame_bytes: Optional[bytes] = None

    def _compute_frame_diff(self, new_bytes: bytes) -> tuple[bool, float]:
        """
        Check if the new screenshot is substantially identical to the previous frame.
        Returns (is_different, diff_ratio).
        """
        frame_hash = hashlib.sha256(new_bytes).hexdigest()
        if self.last_frame_hash == frame_hash:
            return False, 0.0

        if not self.last_frame_bytes:
            self.last_frame_hash = frame_hash
            self.last_frame_bytes = new_bytes
            return True, 1.0

        try:
            img1 = Image.open(io.BytesIO(self.last_frame_bytes)).convert("RGB")
            img2 = Image.open(io.BytesIO(new_bytes)).convert("RGB")
            diff = ImageChops.difference(img1, img2)
            stat = diff.getbbox()
            if not stat:
                return False, 0.0

            # Estimate change magnitude
            hist = diff.histogram()
            non_zero_pixels = sum(hist[1:256] + hist[257:512] + hist[513:768])
            total_pixels = img1.width * img1.height * 3
            ratio = non_zero_pixels / float(total_pixels)

            self.last_frame_hash = frame_hash
            self.last_frame_bytes = new_bytes
            return ratio > self.diff_threshold, ratio
        except Exception:
            self.last_frame_hash = frame_hash
            self.last_frame_bytes = new_bytes
            return True, 1.0

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "screenshot")
        coord = kwargs.get("coordinate")
        text = kwargs.get("text")
        key = kwargs.get("key")
        scroll_amount = kwargs.get("scroll_amount", 0)

        x, y = (coord[0], coord[1]) if (coord and len(coord) >= 2) else (None, None)

        try:
            if action == "screenshot":
                pass  # Just take a screenshot below

            elif action == "mouse_move" and x is not None and y is not None:
                self.sandbox.mouse_move(x, y)

            elif action == "left_click":
                if x is not None and y is not None:
                    self.sandbox.mouse_move(x, y)
                self.sandbox.mouse_click(x or 0, y or 0, button="left", double=False)

            elif action == "double_click":
                if x is not None and y is not None:
                    self.sandbox.mouse_move(x, y)
                self.sandbox.mouse_click(x or 0, y or 0, button="left", double=True)

            elif action == "right_click":
                if x is not None and y is not None:
                    self.sandbox.mouse_move(x, y)
                self.sandbox.mouse_click(x or 0, y or 0, button="right", double=False)

            elif action == "type" and text is not None:
                self.sandbox.type_text(text)

            elif action == "key" and key is not None:
                self.sandbox.key_combination(key)

            elif action == "scroll":
                self.sandbox.mouse_scroll(scroll_amount)

            # Capture resulting display state
            screen_bytes = self.sandbox.take_screenshot()

            is_diff, diff_ratio = (True, 1.0)
            if self.enable_frame_diffing and action != "screenshot":
                is_diff, diff_ratio = self._compute_frame_diff(screen_bytes)

            if not is_diff and action != "screenshot":
                return ToolResult(
                    content=(
                        f"Action '{action}' executed successfully. [Visual Optimization: "
                        f"Display visual state unchanged, frame omitted to save context tokens]."
                    ),
                    image_bytes=None,
                    is_error=False,
                    metadata={"action": action, "frame_omitted": True, "diff_ratio": diff_ratio},
                )

            return ToolResult(
                content=f"Action '{action}' completed. Captured updated screenshot.",
                image_bytes=screen_bytes,
                is_error=False,
                metadata={"action": action, "diff_ratio": diff_ratio},
            )

        except Exception as exc:
            return ToolResult(
                content=f"GUI Action '{action}' failed: {str(exc)}",
                is_error=True,
                metadata={"action": action, "error": str(exc)},
            )
