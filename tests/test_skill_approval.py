from pathlib import Path

import pytest

from py_mono.skill.approval import ApprovalError, run_skill_safe
from py_mono.skill.base import Skill, SkillContext
from py_mono.tools.tool import Tool


class StubRegistry:
    def __init__(self, skill, metadata):
        self._skill = skill
        self._metadata = metadata

    def _norm(self, name: str) -> str:
        return name.strip().lower().replace("-", "_")

    def get(self, name: str):
        if self._norm(name) == self._norm(self._skill.name()):
            return self._skill
        return None


class UsesAllowedToolSkill(Skill):
    def name(self) -> str:
        return "allowed_only"

    def description(self) -> str:
        return "uses only allowed tool"

    def run(self, request: str, context: SkillContext) -> str:
        return context.agent_tools["list_files"].run(path=".")


class UsesBlockedToolSkill(Skill):
    def name(self) -> str:
        return "blocked_tool"

    def description(self) -> str:
        return "tries to use blocked tool"

    def run(self, request: str, context: SkillContext) -> str:
        return context.agent_tools["read_file"].run(path="x.py")


class DirectFuncSkill(Skill):
    def name(self) -> str:
        return "direct_func"

    def description(self) -> str:
        return "tries to use tool.func directly"

    def run(self, request: str, context: SkillContext) -> str:
        tool = context.agent_tools["list_files"]
        return tool.func(path=".")


def make_context():
    tools = {
        "list_files": Tool("list_files", "list files", lambda path=".": "ok"),
        "read_file": Tool("read_file", "read file", lambda path=".": "data"),
    }
    return SkillContext(workspace_root=Path("."), agent_tools=tools, session_manager=None)


def test_allowed_tools_only_checked_on_actual_access():
    skill = UsesAllowedToolSkill()
    registry = StubRegistry(
        skill,
        {
            "allowed_only": {
                "status": "approved",
                "allowed_tools": ["list_files"],
            }
        },
    )

    result = run_skill_safe(registry, "allowed_only", "/skill allowed_only", make_context())

    assert result == "ok"


def test_disallowed_tool_access_is_blocked_when_used():
    skill = UsesBlockedToolSkill()
    registry = StubRegistry(
        skill,
        {
            "blocked_tool": {
                "status": "approved",
                "allowed_tools": ["list_files"],
            }
        },
    )

    with pytest.raises(RuntimeError, match="not allowed to use the tool 'read_file'"):
        run_skill_safe(registry, "blocked_tool", "/skill blocked_tool", make_context())


def test_direct_tool_func_access_is_forbidden():
    skill = DirectFuncSkill()
    registry = StubRegistry(
        skill,
        {
            "direct_func": {
                "status": "approved",
                "allowed_tools": ["list_files"],
            }
        },
    )

    with pytest.raises(RuntimeError, match="Direct tool.func\\(\\) usage is forbidden"):
        run_skill_safe(registry, "direct_func", "/skill direct_func", make_context())


def test_unapproved_skill_is_still_blocked():
    skill = UsesAllowedToolSkill()
    registry = StubRegistry(
        skill,
        {
            "allowed_only": {
                "status": "proposed",
                "allowed_tools": ["list_files"],
            }
        },
    )

    with pytest.raises(ApprovalError, match="is not approved for execution"):
        run_skill_safe(registry, "allowed_only", "/skill allowed_only", make_context())


# ---------------------------------------------------------------------------
# ISS-013: run_skill_safe logs one telemetry record per run
# ---------------------------------------------------------------------------

class FailingSkill(Skill):
    def name(self) -> str:
        return "failing_skill"

    def description(self) -> str:
        return "always raises"

    def run(self, request: str, context: SkillContext) -> str:
        raise ValueError("boom")


def test_successful_run_logs_a_telemetry_record(monkeypatch):
    skill = UsesAllowedToolSkill()
    registry = StubRegistry(
        skill,
        {"allowed_only": {"status": "approved", "allowed_tools": ["list_files"]}},
    )

    logged = []
    monkeypatch.setattr(
        "py_mono.skill.approval.log_skill_run",
        lambda skill, provider, model, duration_ms, success, **kwargs: logged.append(
            (skill, provider, model, success, kwargs)
        ),
    )

    run_skill_safe(registry, "allowed_only", "/skill allowed_only", make_context())

    assert len(logged) == 1
    assert logged[0][0] == "allowed_only"
    assert logged[0][3] is True
    assert logged[0][4]["request"] == "/skill allowed_only"
    assert logged[0][4]["failure_reason"] == ""


def test_failed_run_still_logs_a_telemetry_record(monkeypatch):
    skill = FailingSkill()
    registry = StubRegistry(
        skill,
        {"failing_skill": {"status": "approved", "allowed_tools": ["list_files"]}},
    )

    logged = []
    monkeypatch.setattr(
        "py_mono.skill.approval.log_skill_run",
        lambda skill, provider, model, duration_ms, success, **kwargs: logged.append(
            (skill, provider, model, success, kwargs)
        ),
    )

    with pytest.raises(RuntimeError, match="execution failed"):
        run_skill_safe(registry, "failing_skill", "/skill failing_skill", make_context())

    assert len(logged) == 1
    assert logged[0][0] == "failing_skill"
    assert logged[0][3] is False
    assert logged[0][4]["request"] == "/skill failing_skill"
    assert logged[0][4]["failure_reason"] == "boom"


def test_run_with_no_session_manager_does_not_crash(monkeypatch):
    """make_context() already uses session_manager=None; this just makes the
    intent explicit as a regression guard."""
    skill = UsesAllowedToolSkill()
    registry = StubRegistry(
        skill,
        {"allowed_only": {"status": "approved", "allowed_tools": ["list_files"]}},
    )

    logged = []
    monkeypatch.setattr(
        "py_mono.skill.approval.log_skill_run",
        lambda skill, provider, model, duration_ms, success, **kwargs: logged.append(
            (provider, model)
        ),
    )

    context = make_context()
    assert context.session_manager is None

    run_skill_safe(registry, "allowed_only", "/skill allowed_only", context)

    assert logged == [("<unknown>", "<unknown>")]


# ---------------------------------------------------------------------------
# ISS-014: run_skill_safe prepends a fitness warning when one is returned
# ---------------------------------------------------------------------------

def test_fitness_warning_is_prepended_to_a_successful_result(monkeypatch):
    skill = UsesAllowedToolSkill()
    registry = StubRegistry(
        skill,
        {"allowed_only": {"status": "approved", "allowed_tools": ["list_files"]}},
    )

    monkeypatch.setattr("py_mono.skill.approval.log_skill_run", lambda *a, **k: None)
    monkeypatch.setattr(
        "py_mono.skill.approval.check_model_fitness",
        lambda skill, provider, model: "⚠️ Fitness warning: test warning",
    )

    result = run_skill_safe(registry, "allowed_only", "/skill allowed_only", make_context())

    assert result.startswith("⚠️ Fitness warning: test warning")
    assert result.endswith("ok")  # the skill's real result is still present


def test_no_fitness_warning_prefix_when_none_returned(monkeypatch):
    skill = UsesAllowedToolSkill()
    registry = StubRegistry(
        skill,
        {"allowed_only": {"status": "approved", "allowed_tools": ["list_files"]}},
    )

    monkeypatch.setattr("py_mono.skill.approval.log_skill_run", lambda *a, **k: None)
    monkeypatch.setattr("py_mono.skill.approval.check_model_fitness", lambda skill, provider, model: None)

    result = run_skill_safe(registry, "allowed_only", "/skill allowed_only", make_context())

    assert result == "ok"


def test_fitness_warning_is_not_shown_on_a_failed_run(monkeypatch):
    """A fitness warning is only useful attached to a result the caller
    actually receives - a failed run raises instead, so there's no result to
    prepend it to."""
    skill = FailingSkill()
    registry = StubRegistry(
        skill,
        {"failing_skill": {"status": "approved", "allowed_tools": ["list_files"]}},
    )

    monkeypatch.setattr("py_mono.skill.approval.log_skill_run", lambda *a, **k: None)
    monkeypatch.setattr(
        "py_mono.skill.approval.check_model_fitness",
        lambda skill, provider, model: "⚠️ Fitness warning: test warning",
    )

    with pytest.raises(RuntimeError, match="execution failed"):
        run_skill_safe(registry, "failing_skill", "/skill failing_skill", make_context())
