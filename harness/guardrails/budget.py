"""
Resource Budget Enforcer: Steps, Tokens, Wall-Clock Time, and Financial Cost.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CostModel:
    prompt_token_cost_per_million: float = 3.00       # $3.00 / 1M prompt tokens (Claude 3.7 Sonnet)
    completion_token_cost_per_million: float = 15.00   # $15.00 / 1M completion tokens
    image_token_cost_per_frame: float = 0.0048         # ~$0.0048 per 1024x768 image frame (~1600 tokens)


class BudgetEnforcer:
    """
    Monitors and limits the operational budget of an agent run to prevent
    runaway loops, massive token consumption, and exorbitant API charges.
    """

    def __init__(
        self,
        max_steps: int = 30,
        max_cost_usd: float = 5.00,
        max_wall_time_seconds: float = 300.0,
        cost_model: Optional[CostModel] = None,
    ):
        self.max_steps = max_steps
        self.max_cost_usd = max_cost_usd
        self.max_wall_time_seconds = max_wall_time_seconds
        self.cost_model = cost_model or CostModel()

        self.current_step = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_image_frames = 0
        self.start_time = time.time()

    def record_step(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        image_frames: int = 0,
    ) -> Tuple[bool, Optional[str]]:
        """
        Record usage for a step and check if any budget threshold has been violated.
        Returns (is_exceeded, violation_reason).
        """
        self.current_step += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_image_frames += image_frames

        # Check step count
        if self.current_step > self.max_steps:
            return True, f"Budget Exceeded: Step limit ({self.max_steps}) reached."

        # Check wall-clock time
        elapsed = time.time() - self.start_time
        if elapsed > self.max_wall_time_seconds:
            return True, f"Budget Exceeded: Time limit ({self.max_wall_time_seconds}s) reached."

        # Check financial cost
        estimated_cost = self.calculate_cost()
        if estimated_cost > self.max_cost_usd:
            return True, f"Budget Exceeded: Estimated cost (${estimated_cost:.2f}) exceeded maximum (${self.max_cost_usd:.2f})."

        return False, None

    def calculate_cost(self) -> float:
        """Calculate total estimated cost in USD."""
        prompt_cost = (self.total_prompt_tokens / 1_000_000) * self.cost_model.prompt_token_cost_per_million
        completion_cost = (self.total_completion_tokens / 1_000_000) * self.cost_model.completion_token_cost_per_million
        image_cost = self.total_image_frames * self.cost_model.image_token_cost_per_frame
        return prompt_cost + completion_cost + image_cost

    def get_summary(self) -> dict:
        return {
            "steps": self.current_step,
            "max_steps": self.max_steps,
            "elapsed_seconds": round(time.time() - self.start_time, 2),
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "image_frames": self.total_image_frames,
            "estimated_cost_usd": round(self.calculate_cost(), 4),
        }
