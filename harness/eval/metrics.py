"""
Evaluation metrics collection and benchmark summary analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TaskMetric:
    task_name: str
    category: str
    success: bool
    steps: int
    duration_seconds: float
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    verification_details: Dict[str, Any] = field(default_factory=dict)
    termination_reason: str = "completed"


@dataclass
class BenchmarkSummary:
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    pass_rate_percentage: float
    avg_steps: float
    avg_duration_seconds: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    tasks: List[TaskMetric] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "pass_rate_percentage": round(self.pass_rate_percentage, 1),
            "avg_steps": round(self.avg_steps, 2),
            "avg_duration_seconds": round(self.avg_duration_seconds, 2),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "tasks": [
                {
                    "name": t.task_name,
                    "category": t.category,
                    "success": t.success,
                    "steps": t.steps,
                    "duration": t.duration_seconds,
                    "cost": t.estimated_cost_usd,
                    "reason": t.termination_reason,
                }
                for t in self.tasks
            ],
        }
