# Contributing to NexusCUH

We welcome contributions to **Nexus Computer Use Harness**! Whether you are adding new Model Context Protocol (MCP) servers, writing benchmark tasks, improving sandboxing backends, or strengthening safety guardrails, here is how to get started.

---

## Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/subasah/computer-use-harness.git
   cd computer-use-harness
   ```

2. **Create a Virtual Environment with uv**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. **Verify the Test Suite**:
   ```bash
   pytest -v
   ruff check .
   ```

---

## Architectural Principles to Uphold

1. **Ground-Truth Verification**: Every new benchmark task MUST specify ground-truth assertions (file exists, regex match, JSON schema, or MCP AST state). Do not rely solely on agent self-declarations or exit codes.
2. **Deterministic Resets**: All sandbox backends must support `reset()` returning the workspace to an identical starting state.
3. **Safety First**: Commands must pass through `SecurityPolicy` and outputs through `PromptInjectionDetector`.

---

## Adding a New Benchmark Task

1. Create a new task class in `harness/eval/tasks/task_<name>.py`:
   ```python
   from harness.sandbox.base import BaseSandbox
   from harness.verification.assertions import BaseAssertion, FileExistsAssertion

   class MyCustomTask:
       name = "task_custom_feature"
       category = "data_engineering"
       instruction = "Process input data and produce reports/output.csv"

       def setup(self, sandbox: BaseSandbox) -> None:
           sandbox.write_file("input/raw.csv", "id,val\n1,100\n")

       def get_assertions(self) -> list[BaseAssertion]:
           return [FileExistsAssertion("reports/output.csv")]
   ```
2. Register the task in `harness/eval/tasks/__init__.py`.
3. Add a unit test in `tests/test_eval.py`.

---

## Pull Request Guidelines

- Format and lint code with `ruff check --fix .`.
- Ensure all 25+ pytest test cases pass.
- Maintain documentation integrity and type annotations (`mypy`).
