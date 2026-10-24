"""
Unit tests for Multi-Modal Verification subsystem.
"""

import tempfile

import pytest

from harness.sandbox.local_sandbox import LocalSandbox
from harness.verification.assertions import (
    FileContentRegexAssertion,
    FileExistsAssertion,
    FileJsonAssertion,
)
from harness.verification.verifier import MultiModalVerifier


@pytest.fixture
def sandbox():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = LocalSandbox(workspace_dir=tmpdir)
        sb.start()
        yield sb
        sb.stop()


@pytest.mark.asyncio
async def test_file_exists_assertion(sandbox: LocalSandbox):
    sandbox.write_file("output.txt", "data")
    assert_passed = FileExistsAssertion("output.txt")
    passed, msg = await assert_passed.evaluate(sandbox)
    assert passed

    assert_failed = FileExistsAssertion("nonexistent.txt")
    passed2, _ = await assert_failed.evaluate(sandbox)
    assert not passed2


@pytest.mark.asyncio
async def test_file_json_assertion(sandbox: LocalSandbox):
    sandbox.write_file("data.json", '{"status": "success", "count": 42}')

    assert_pass = FileJsonAssertion("data.json", {"status": "success", "count": 42})
    passed, _ = await assert_pass.evaluate(sandbox)
    assert passed

    assert_fail = FileJsonAssertion("data.json", {"status": "error"})
    passed2, _ = await assert_fail.evaluate(sandbox)
    assert not passed2


@pytest.mark.asyncio
async def test_multi_modal_verifier_aggregation(sandbox: LocalSandbox):
    sandbox.write_file("metrics.txt", "ACCURACY: 99.4%\nLATENCY: 12ms\n")

    verifier = MultiModalVerifier([
        FileExistsAssertion("metrics.txt"),
        FileContentRegexAssertion("metrics.txt", r"ACCURACY: 99\.4%"),
    ])

    report = await verifier.verify(sandbox)
    assert report.passed
    assert report.total_assertions == 2
    assert report.passed_count == 2
    assert report.failed_count == 0
