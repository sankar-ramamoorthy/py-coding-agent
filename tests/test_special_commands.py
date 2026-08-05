"""Tests for Agent._is_special_command / _handle_special_command dispatch
(ISS-010: bare '/provider' with no argument silently fell through to the LLM
instead of showing usage)."""

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
