"""Tests for py_mono/skill/fitness.py (ISS-014): a model/task fitness check
driven by the telemetry log (ISS-013), not a hardcoded list of "bad"
models."""

from py_mono.skill.fitness import check_model_fitness
from py_mono.skill.telemetry import log_skill_run


def _log(log_path, skill="generate_skill", provider="OllamaProvider", model="qwen3.5:4b", success=True):
    log_skill_run(skill, provider, model, 100.0, success, log_path=log_path)


def test_no_warning_with_fewer_than_min_samples(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    _log(log_path, success=False)
    _log(log_path, success=False)  # only 2 records, MIN_SAMPLES is 3

    assert check_model_fitness("generate_skill", "OllamaProvider", "qwen3.5:4b", log_path=log_path) is None


def test_no_warning_when_failure_rate_below_threshold(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    for success in (True, True, True, True, False):  # 1/5 = 20% failure
        _log(log_path, success=success)

    assert check_model_fitness("generate_skill", "OllamaProvider", "qwen3.5:4b", log_path=log_path) is None


def test_warning_when_failure_rate_at_threshold(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    for success in (True, False, False):  # 2/3 = 67% failure
        _log(log_path, success=success)

    warning = check_model_fitness("generate_skill", "OllamaProvider", "qwen3.5:4b", log_path=log_path)
    assert warning is not None
    assert "generate_skill" in warning
    assert "OllamaProvider" in warning
    assert "qwen3.5:4b" in warning
    assert "2/3" in warning


def test_only_matching_skill_provider_model_combination_counts(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    # Plenty of failures, but for a different skill/provider/model - must not
    # contaminate the combination actually being checked.
    for _ in range(5):
        _log(log_path, skill="other_skill", success=False)
    for _ in range(5):
        _log(log_path, provider="LiteLLMProvider", success=False)
    for _ in range(5):
        _log(log_path, model="qwen2.5-coder:7b-instruct-q5_K_M", success=False)

    assert check_model_fitness("generate_skill", "OllamaProvider", "qwen3.5:4b", log_path=log_path) is None


def test_only_recent_window_is_considered(tmp_path):
    log_path = tmp_path / "skill_runs.jsonl"
    # 5 old failures, then 5 recent successes - RECENT_WINDOW is 5, so only
    # the recent successes should count.
    for _ in range(5):
        _log(log_path, success=False)
    for _ in range(5):
        _log(log_path, success=True)

    assert check_model_fitness("generate_skill", "OllamaProvider", "qwen3.5:4b", log_path=log_path) is None


def test_no_telemetry_file_returns_none(tmp_path):
    assert check_model_fitness(
        "generate_skill", "OllamaProvider", "qwen3.5:4b", log_path=tmp_path / "does_not_exist.jsonl"
    ) is None
