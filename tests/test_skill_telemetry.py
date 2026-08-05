"""Tests for py_mono/skill/telemetry.py (ISS-013): a minimal, flat per-run
log shared by Milestone 6's model/task fitness check (ISS-014) and
Milestone 7's failure-driven evolution."""

import json
from pathlib import Path

from py_mono.skill.telemetry import log_skill_run, read_skill_runs


def test_log_skill_run_writes_one_json_line(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"

    log_skill_run("bug_fix", "OllamaProvider", "qwen3.5:4b", 123.456, True, log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["skill"] == "bug_fix"
    assert record["provider"] == "OllamaProvider"
    assert record["model"] == "qwen3.5:4b"
    assert record["duration_ms"] == 123.46
    assert record["success"] is True
    assert "timestamp" in record


def test_log_skill_run_appends_without_truncating(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"

    log_skill_run("bug_fix", "OllamaProvider", "qwen3.5:4b", 10.0, True, log_path=log_path)
    log_skill_run("doc_sync", "OllamaProvider", "qwen3.5:4b", 20.0, False, log_path=log_path)

    records = read_skill_runs(log_path)
    assert [r["skill"] for r in records] == ["bug_fix", "doc_sync"]
    assert records[1]["success"] is False


def test_log_skill_run_creates_parent_directory(tmp_path):
    log_path = tmp_path / "nested" / "dir" / "skill_runs.jsonl"

    log_skill_run("hello", "LiteLLMProvider", "gpt-4o", 1.0, True, log_path=log_path)

    assert log_path.exists()


def test_read_skill_runs_returns_empty_list_when_file_missing(tmp_path):
    assert read_skill_runs(tmp_path / "does_not_exist.jsonl") == []


def test_read_skill_runs_skips_corrupt_lines(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    log_path.write_text(
        '{"skill": "a", "provider": "p", "model": "m", "duration_ms": 1.0, "success": true}\n'
        "not valid json\n"
        '{"skill": "b", "provider": "p", "model": "m", "duration_ms": 2.0, "success": true}\n',
        encoding="utf-8",
    )

    records = read_skill_runs(log_path)
    assert [r["skill"] for r in records] == ["a", "b"]
