import json

from py_mono.skill.diffing import build_artifact_diff
from py_mono.skill.lifecycle import (
    STATUS_FAILED,
    STATUS_PASSED,
    STAGE_GENERATE,
    STAGE_TEST,
    SkillLifecycleRun,
    SmokeTestResult,
)
from py_mono.skill.reporting import (
    REPORT_JSON,
    REPORT_MD,
    build_lifecycle_report_record,
    render_lifecycle_report_markdown,
    write_lifecycle_report,
)


class FailureContext:
    request = "/skill echo-request bad input"
    failure_reason = "RuntimeError: boom"
    provider = "litellm"
    model = "stub-model"
    timestamp = "2026-08-31T12:00:00+00:00"


def test_write_lifecycle_report_persists_markdown_and_json(tmp_path):
    lifecycle = SkillLifecycleRun("echo-request")
    lifecycle.add(STAGE_GENERATE, STATUS_PASSED, "Generated files.")
    lifecycle.add(STAGE_TEST, STATUS_PASSED, "Smoke test passed.")
    smoke = SmokeTestResult(
        status=STATUS_PASSED,
        request="/skill echo-request smoke-test",
        output_preview="ok",
    )
    diff = build_artifact_diff(
        "skill.py",
        "return 'old'\n",
        "return 'new'\n",
        baseline_available=True,
    )

    result = write_lifecycle_report(
        report_dir=tmp_path,
        skill_name="echo-request",
        mode="regenerate",
        status="proposed",
        lifecycle=lifecycle,
        skill_path=tmp_path.parent / "echo-request",
        candidate_path=tmp_path,
        smoke_test=smoke,
        diffs=[diff],
        failure_context=FailureContext(),
        next_steps=["Review:  /tmp/candidate", "Approve: /approve echo-request"],
    )

    assert result.ok
    markdown = (tmp_path / REPORT_MD).read_text(encoding="utf-8")
    data = json.loads((tmp_path / REPORT_JSON).read_text(encoding="utf-8"))
    assert "# Lifecycle Report: echo-request" in markdown
    assert "## Smoke Test" in markdown
    assert "## Failure Context" in markdown
    assert "```diff" in markdown
    assert data["skill_name"] == "echo-request"
    assert data["mode"] == "regenerate"
    assert data["status"] == "proposed"
    assert data["smoke_test"]["output_preview"] == "ok"
    assert data["failure_context"]["failure_reason"] == "RuntimeError: boom"
    assert data["diffs"][0]["artifact"] == "skill.py"


def test_lifecycle_report_records_failed_smoke_test():
    lifecycle = SkillLifecycleRun("echo-request")
    lifecycle.add(STAGE_TEST, STATUS_FAILED, "Smoke test failed.", ["RuntimeError: cannot run"])
    smoke = SmokeTestResult(
        status=STATUS_FAILED,
        request="/skill echo-request smoke-test",
        failure_reason="RuntimeError: cannot run",
    )

    record = build_lifecycle_report_record(
        skill_name="echo-request",
        mode="create",
        status="failed",
        lifecycle=lifecycle,
        skill_path="/skills/echo-request",
        candidate_path=None,
        smoke_test=smoke,
        diffs=[],
        failure_context=None,
        next_steps=["Retry generation after adjusting the skill description."],
    )
    markdown = render_lifecycle_report_markdown(record)

    assert record["smoke_test"]["status"] == STATUS_FAILED
    assert record["smoke_test"]["failure_reason"] == "RuntimeError: cannot run"
    assert "Failure reason: RuntimeError: cannot run" in markdown
    assert "Retry generation" in markdown
