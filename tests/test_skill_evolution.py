from py_mono.skill.evolution import latest_failure_context
from py_mono.skill.telemetry import log_skill_run


def test_latest_failure_context_returns_most_recent_failed_run(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    log_skill_run(
        "demo-skill",
        "Provider",
        "model-a",
        10.0,
        False,
        request="/skill demo-skill old",
        failure_reason="old failure",
        log_path=log_path,
    )
    log_skill_run(
        "demo-skill",
        "Provider",
        "model-b",
        12.0,
        False,
        request="/skill demo-skill new",
        failure_reason="new failure",
        log_path=log_path,
    )

    context = latest_failure_context("demo-skill", log_path=log_path)

    assert context is not None
    assert context.request == "/skill demo-skill new"
    assert context.failure_reason == "new failure"
    assert "new failure" in context.to_prompt_text()


def test_latest_failure_context_ignores_successes_and_empty_failures(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    log_skill_run("demo-skill", "Provider", "model-a", 10.0, True, log_path=log_path)
    log_skill_run("demo-skill", "Provider", "model-a", 10.0, False, log_path=log_path)

    assert latest_failure_context("demo-skill", log_path=log_path) is None


def test_latest_failure_context_returns_none_when_missing(tmp_path):
    assert latest_failure_context("demo-skill", log_path=tmp_path / "missing.jsonl") is None


def test_latest_failure_context_matches_normalized_skill_names(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    log_skill_run(
        "demo_skill",
        "Provider",
        "model-a",
        10.0,
        False,
        request="/skill demo-skill input",
        failure_reason="normalized failure",
        log_path=log_path,
    )

    context = latest_failure_context("demo-skill", log_path=log_path)

    assert context is not None
    assert context.skill_name == "demo_skill"
    assert context.failure_reason == "normalized failure"
