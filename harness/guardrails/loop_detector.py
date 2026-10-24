"""
Cycle and Loop Detector for Computer Use Agent ReAct Loops.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from typing import Any, Dict, Optional, Tuple


class LoopDetector:
    """
    Monitors agent action sequences and environment state hashes to detect
    repetitive failure cycles and infinite loops.
    """

    def __init__(self, window_size: int = 4, max_consecutive_repeats: int = 3):
        self.window_size = window_size
        self.max_consecutive_repeats = max_consecutive_repeats
        self.action_history: deque[Tuple[str, str, Optional[str]]] = deque(maxlen=window_size)

    def record_step(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        state_hash: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Record an action step and verify whether a repetitive loop has been triggered.
        Returns (is_loop_detected, warning_message).
        """
        args_str = json.dumps(tool_args, sort_keys=True)
        args_hash = hashlib.md5(args_str.encode("utf-8")).hexdigest()

        self.action_history.append((tool_name, args_hash, state_hash))

        if len(self.action_history) < self.max_consecutive_repeats:
            return False, None

        # Check for consecutive identical actions
        recent = list(self.action_history)[-self.max_consecutive_repeats :]
        first_tool, first_args, _ = recent[0]

        all_identical = all(
            tool == first_tool and args == first_args for tool, args, _ in recent
        )

        if all_identical:
            # Check if environment state also remained static
            states = [s for _, _, s in recent if s is not None]
            state_stagnant = len(states) >= 2 and len(set(states)) == 1

            detail = (
                f"Action '{first_tool}' with identical arguments repeated {self.max_consecutive_repeats} times "
                f"without forward progress."
            )
            if state_stagnant:
                detail += " Environment state remained completely unchanged."

            return True, f"Loop Detected: {detail} You must choose an alternative approach or inspect errors."

        return False, None

    def reset(self) -> None:
        self.action_history.clear()
