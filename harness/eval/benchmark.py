"""
Evaluation Benchmark Runner for Computer Use Agent Suites.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from harness.agent.orchestrator import AgentOrchestrator
from harness.eval.metrics import BenchmarkSummary, TaskMetric
from harness.eval.tasks import ALL_TASKS
from harness.verification.verifier import MultiModalVerifier

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Executes a comprehensive benchmark suite across isolated tasks,
    enforcing deterministic snapshot rollbacks and gathering multi-modal metrics.
    """

    def __init__(self, orchestrator: AgentOrchestrator, tasks: Optional[List[Any]] = None):
        self.orchestrator = orchestrator
        self.tasks = tasks or ALL_TASKS

    async def run_suite(self) -> BenchmarkSummary:
        """Execute all tasks in the benchmark suite."""
        task_metrics: List[TaskMetric] = []

        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost_usd = 0.0
        total_duration = 0.0
        total_steps = 0
        successful_count = 0

        for task in self.tasks:
            logger.info(f"--- Running Benchmark Task: {task.name} ({task.category}) ---")

            # Reset sandbox to clean state
            self.orchestrator.sandbox.reset()

            # Seed task environment
            task.setup(self.orchestrator.sandbox)

            # Configure verifier with task assertions
            task_verifier = MultiModalVerifier(task.get_assertions())
            self.orchestrator.verifier = task_verifier

            # Reset budget counters for task
            self.orchestrator.budget_enforcer.current_step = 0
            self.orchestrator.budget_enforcer.total_prompt_tokens = 0
            self.orchestrator.budget_enforcer.total_completion_tokens = 0
            self.orchestrator.budget_enforcer.total_image_frames = 0

            # Execute task
            result = await self.orchestrator.run_task(task.instruction)

            is_success = result["success"]
            steps = result["steps_count"]
            duration = result["duration_seconds"]
            budget_info = result["budget"]

            if is_success:
                successful_count += 1

            total_steps += steps
            total_duration += duration
            total_prompt_tokens += budget_info["prompt_tokens"]
            total_completion_tokens += budget_info["completion_tokens"]
            total_cost_usd += budget_info["estimated_cost_usd"]

            metric = TaskMetric(
                task_name=task.name,
                category=task.category,
                success=is_success,
                steps=steps,
                duration_seconds=duration,
                prompt_tokens=budget_info["prompt_tokens"],
                completion_tokens=budget_info["completion_tokens"],
                estimated_cost_usd=budget_info["estimated_cost_usd"],
                verification_details=result["verification"],
                termination_reason=result["termination_reason"],
            )
            task_metrics.append(metric)

        total_tasks = len(self.tasks)
        pass_rate = (successful_count / total_tasks * 100.0) if total_tasks > 0 else 0.0
        avg_steps = (total_steps / total_tasks) if total_tasks > 0 else 0.0
        avg_duration = (total_duration / total_tasks) if total_tasks > 0 else 0.0

        return BenchmarkSummary(
            total_tasks=total_tasks,
            successful_tasks=successful_count,
            failed_tasks=total_tasks - successful_count,
            pass_rate_percentage=pass_rate,
            avg_steps=avg_steps,
            avg_duration_seconds=avg_duration,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_cost_usd=total_cost_usd,
            tasks=task_metrics,
        )
