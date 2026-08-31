"""Tests for Agent._is_special_command / _handle_special_command dispatch
(ISS-010: bare '/provider' with no argument silently fell through to the LLM
instead of showing usage)."""

import json
from pathlib import Path

from py_mono.agent.agent import Agent
from py_mono.session.session_manager import SessionManager
from py_mono.skill.base import SkillRegistry


def make_agent(tmp_path: Path) -> Agent:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    registry = SkillRegistry(skills_dir=skills_dir)
    registry.load()
    session_manager = SessionManager(default_provider="ollama")
    return Agent(session_manager, tools=[], skill_registry=registry)


def make_agent_with_registry(skills_dir: Path) -> Agent:
    registry = SkillRegistry(skills_dir=skills_dir)
    registry.load()
    session_manager = SessionManager(default_provider="ollama")
    return Agent(session_manager, tools=[], skill_registry=registry)


def write_skill_with_candidate_report(skills_dir: Path, name: str = "demo-skill") -> Path:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Demo skill.\nstatus: approved\n---\n# Demo\n",
        encoding="utf-8",
    )
    candidate_dir = skill_dir / ".candidate"
    candidate_dir.mkdir()
    (candidate_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Demo update.\nstatus: proposed\n---\n# Demo\n",
        encoding="utf-8",
    )
    (candidate_dir / "skill.py").write_text("# candidate\n", encoding="utf-8")
    report = {
        "skill_name": name,
        "mode": "regenerate",
        "status": "proposed",
        "timestamp": "2026-08-31T12:00:00+00:00",
        "skill_path": str(skill_dir),
        "candidate_path": str(candidate_dir),
        "stages": [
            {"stage": "Critique", "status": "passed", "message": "Spec accepted."},
            {"stage": "Test", "status": "passed", "message": "Smoke test passed."},
        ],
        "smoke_test": {
            "status": "passed",
            "request": "/skill demo-skill smoke-test",
            "output_preview": "ok",
            "failure_reason": "",
        },
        "baseline": {"available": True, "reason": ""},
        "diffs": [
            {
                "artifact": "SKILL.md",
                "changed": True,
                "baseline_available": True,
                "diff_text": "-old\n+new",
            }
        ],
        "failure_context": None,
        "next_steps": ["Review:  /tmp/candidate", f"Approve: /approve {name}"],
    }
    (candidate_dir / "lifecycle_report.json").write_text(
        json.dumps(report),
        encoding="utf-8",
    )
    (candidate_dir / "lifecycle_report.md").write_text(
        "# Lifecycle Report: demo-skill\n",
        encoding="utf-8",
    )
    return skill_dir


def test_bare_provider_is_recognized_as_special_command(tmp_path):
    agent = make_agent(tmp_path)
    assert agent._is_special_command("/provider") is True


def test_bare_provider_shows_usage(tmp_path):
    agent = make_agent(tmp_path)
    assert agent._handle_special_command("/provider") == "Usage: /provider <provider> [model]"


def test_provider_with_trailing_space_only_still_shows_usage(tmp_path):
    """Regression guard: '/provider ' (trailing space, no name) already showed
    usage before this fix and must continue to."""
    agent = make_agent(tmp_path)
    assert agent._is_special_command("/provider ") is True
    assert agent._handle_special_command("/provider ") == "Usage: /provider <provider> [model]"


def test_providers_plural_is_unaffected(tmp_path):
    """'/providers' must not be confused with bare '/provider'."""
    agent = make_agent(tmp_path)
    assert agent._is_special_command("/providers") is True
    result = agent._handle_special_command("/providers")
    assert result.startswith("Active provider:")


def test_provider_with_valid_argument_still_switches(tmp_path):
    agent = make_agent(tmp_path)
    result = agent._handle_special_command("/provider ollama")
    assert "Unknown provider" not in result
    assert "Usage:" not in result


def test_skill_review_is_recognized_as_special_command(tmp_path):
    agent = make_agent(tmp_path)
    assert agent._is_special_command("/skill review demo-skill") is True


def test_skill_review_summarizes_candidate_lifecycle_report(tmp_path):
    skills_dir = tmp_path / "skills"
    write_skill_with_candidate_report(skills_dir)
    agent = make_agent_with_registry(skills_dir)

    result = agent._handle_special_command("/skill review demo-skill")

    assert "Review: demo-skill" in result
    assert "Candidate:" in result
    assert "Status: proposed" in result
    assert "Mode: regenerate" in result
    assert "Critique: passed" in result
    assert "Smoke test:" in result
    assert "SKILL.md: changed" in result
    assert "Approve: /approve demo-skill" in result


def test_skill_review_falls_back_to_markdown_when_json_is_corrupt(tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = write_skill_with_candidate_report(skills_dir)
    candidate_dir = skill_dir / ".candidate"
    (candidate_dir / "lifecycle_report.json").write_text("{not json", encoding="utf-8")
    (candidate_dir / "lifecycle_report.md").write_text(
        "# Lifecycle Report: demo-skill\n\nMarkdown fallback.",
        encoding="utf-8",
    )
    agent = make_agent_with_registry(skills_dir)

    result = agent._handle_special_command("/skill review demo-skill")

    assert "Lifecycle report JSON unavailable" in result
    assert "Markdown fallback." in result
    assert "Approve: /approve demo-skill" in result


def test_skill_list_marks_pending_candidate(tmp_path):
    skills_dir = tmp_path / "skills"
    write_skill_with_candidate_report(skills_dir)
    agent = make_agent_with_registry(skills_dir)

    result = agent._handle_special_command("/skill list")

    assert "Pending candidate: yes" in result
    assert "Review with: /skill review demo_skill" in result


def test_skill_help_points_to_candidate_review(tmp_path):
    skills_dir = tmp_path / "skills"
    write_skill_with_candidate_report(skills_dir)
    agent = make_agent_with_registry(skills_dir)

    result = agent._handle_special_command("/skill help demo-skill")

    assert "--- SKILL.md: demo-skill ---" in result
    assert "Pending candidate: yes" in result
    assert "Review candidate: /skill review demo-skill" in result
