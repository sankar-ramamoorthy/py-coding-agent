"""Tests for the skill approval gate (ISS-003): a proposed skill's module code
must never execute before an approved, hash-matching ledger entry exists."""

from pathlib import Path

import pytest

from py_mono.skill.base import SkillRegistry, SKILLS_DIR
from py_mono.skill import approval_ledger
from py_mono.agent.agent import Agent
from py_mono.session.session_manager import SessionManager


MARKER_SKILL_PY = '''
from pathlib import Path
Path(r"{marker_file}").write_text("executed", encoding="utf-8")

from py_mono.skill.base import Skill, SkillContext

class DemoSkill(Skill):
    def name(self):
        return "{name}"
    def description(self):
        return "demo"
    def run(self, request, context):
        return "ran"
'''

FORBIDDEN_SKILL_PY = '''
import os
os.system("echo hi")
from pathlib import Path
Path(r"{marker_file}").write_text("executed", encoding="utf-8")

from py_mono.skill.base import Skill

class BadSkill(Skill):
    def name(self):
        return "{name}"
    def description(self):
        return "demo"
    def run(self, request, context):
        return "ran"
'''


def write_skill(tmp_path: Path, name: str, status: str, skill_py_template: str = MARKER_SKILL_PY) -> Path:
    """Writes a skill under tmp_path and returns the marker-file path that its
    skill.py will create IF (and only if) it actually executes."""
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True)
    marker_file = tmp_path / f"{name}.executed"
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: demo\nstatus: {status}\n---\n# demo\n",
        encoding="utf-8",
    )
    (skill_dir / "skill.py").write_text(
        skill_py_template.format(name=name, marker_file=str(marker_file).replace("\\", "\\\\")),
        encoding="utf-8",
    )
    return marker_file


# ---------------------------------------------------------------------------
# User Story 1: proposed skill code never executes at load time
# ---------------------------------------------------------------------------

def test_proposed_skill_does_not_execute_at_load(tmp_path):
    marker = write_skill(tmp_path, "proposed_demo", "proposed")

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()

    assert not marker.exists()
    assert registry.get("proposed_demo") is None


def test_proposed_skill_metadata_still_listed(tmp_path):
    write_skill(tmp_path, "proposed_demo", "proposed")

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()

    listed = {s["name"]: s for s in registry.list_skills()}
    assert "proposed_demo" in listed
    assert listed["proposed_demo"]["status"] == "proposed"
    assert listed["proposed_demo"]["has_code"] is True


def test_approved_skill_with_matching_ledger_executes(tmp_path):
    marker = write_skill(tmp_path, "approved_demo", "approved")

    ledger_path = approval_ledger.ledger_path_for(tmp_path)
    ledger = {}
    approval_ledger.record_approval(
        ledger, "approved_demo", tmp_path / "approved_demo" / "skill.py"
    )
    approval_ledger.save_ledger(ledger, ledger_path)

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()

    assert not marker.exists()
    assert registry.get("approved_demo") is not None
    result = Agent(
        SessionManager(default_provider="ollama"),
        tools=[],
        skill_registry=registry,
        debug=False,
    )._handle_skill_run("/skill approved_demo")
    assert "ran" in result
    assert marker.exists()


def test_approved_skill_without_ledger_entry_auto_seeds_and_executes(tmp_path):
    """No ledger entry yet, but status is already approved -> auto-seed covers
    the 8 pre-existing skills scenario."""
    marker = write_skill(tmp_path, "already_approved", "approved")

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()

    assert not marker.exists()
    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(tmp_path))
    assert ledger["already_approved"]["seeded"] is True


# ---------------------------------------------------------------------------
# User Story 2: approval re-validates, expires on later edits
# ---------------------------------------------------------------------------

def test_reload_respects_the_same_gate(tmp_path):
    marker = write_skill(tmp_path, "reload_demo", "proposed")

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()
    assert not marker.exists()
    assert registry.get("reload_demo") is None

    # flip to approved on disk + record approval, then reload
    skill_md = tmp_path / "reload_demo" / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8").replace("status: proposed", "status: approved"),
        encoding="utf-8",
    )
    ledger_path = approval_ledger.ledger_path_for(tmp_path)
    ledger = approval_ledger.load_ledger(ledger_path)
    approval_ledger.record_approval(ledger, "reload_demo", tmp_path / "reload_demo" / "skill.py")
    approval_ledger.save_ledger(ledger, ledger_path)

    registry.reload_skill("reload_demo")
    assert registry.get("reload_demo") is not None
    assert not marker.exists()
    result = Agent(
        SessionManager(default_provider="ollama"),
        tools=[],
        skill_registry=registry,
        debug=False,
    )._handle_skill_run("/skill reload_demo")
    assert "ran" in result
    assert marker.exists()


def test_post_approval_edit_invalidates_approval(tmp_path):
    marker = write_skill(tmp_path, "tamper_demo", "approved")

    ledger_path = approval_ledger.ledger_path_for(tmp_path)
    ledger = {}
    skill_py = tmp_path / "tamper_demo" / "skill.py"
    approval_ledger.record_approval(ledger, "tamper_demo", skill_py)
    approval_ledger.save_ledger(ledger, ledger_path)

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()
    assert not marker.exists()

    # tamper: edit skill.py after approval, without re-approving
    skill_py.write_text(skill_py.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

    registry.reload_skill("tamper_demo")
    assert not marker.exists()
    assert registry.get("tamper_demo") is None


def test_auto_seed_trusts_pre_existing_approved_content_without_revalidation(tmp_path):
    """Documents the accepted trade-off: auto-seed recognizes PRE-EXISTING
    'status: approved' skills without re-running validate_skill_py — so a
    skill that was hand-edited to 'approved' outside of /approve, even with
    a forbidden pattern, still gets seeded and executes. This is why
    /approve's own validation step (tested separately below) is the real
    safety gate for anything going through the normal approval flow —
    auto-seed exists only to avoid disrupting skills that predate this
    ledger, not as a substitute for review."""
    marker = write_skill(tmp_path, "forbidden_demo", "approved", FORBIDDEN_SKILL_PY)

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()

    assert not marker.exists()
    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(tmp_path))
    assert ledger["forbidden_demo"]["seeded"] is True


# ---------------------------------------------------------------------------
# Regression: the 8 real, already-approved skills are unaffected
# ---------------------------------------------------------------------------

def test_all_real_approved_skills_still_load():
    """Loads the ACTUAL skills/ directory (not a fixture) and confirms every
    currently-approved skill still loads after this fix — the auto-seed
    mechanism must leave zero disruption for pre-existing approved skills."""
    registry = SkillRegistry(skills_dir=SKILLS_DIR)
    registry.load()

    listed = {s["name"]: s for s in registry.list_skills()}
    approved_with_code = [
        name for name, s in listed.items()
        if s["status"] == "approved" and s["has_code"]
    ]

    assert approved_with_code, "expected at least one real approved skill with code"
    for name in approved_with_code:
        assert registry.get(name) is not None, f"'{name}' should have loaded (regression)"


# ---------------------------------------------------------------------------
# User Story 2 (continued): the real /approve path via Agent._handle_skill_approve
# ---------------------------------------------------------------------------

def make_agent(skills_dir: Path) -> Agent:
    registry = SkillRegistry(skills_dir=skills_dir)
    registry.load()
    session_manager = SessionManager(default_provider="ollama")
    return Agent(session_manager, tools=[], skill_registry=registry)


def test_approve_rejects_forbidden_pattern_code(tmp_path):
    marker = write_skill(tmp_path, "unsafe_skill", "proposed", FORBIDDEN_SKILL_PY)
    agent = make_agent(tmp_path)

    result = agent._handle_skill_approve("unsafe_skill")

    assert "failed validation" in result.lower()
    assert "not approved" in result.lower()
    skill_md = (tmp_path / "unsafe_skill" / "SKILL.md").read_text(encoding="utf-8")
    assert "status: proposed" in skill_md
    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(tmp_path))
    assert "unsafe_skill" not in ledger
    assert not marker.exists()


def test_approve_succeeds_for_clean_code_and_then_executes(tmp_path):
    marker = write_skill(tmp_path, "clean_skill", "proposed")
    agent = make_agent(tmp_path)

    result = agent._handle_skill_approve("clean_skill")

    assert "approved and ready" in result.lower()
    assert "not approved" not in result.lower()
    assert "failed validation" not in result.lower()
    skill_md = (tmp_path / "clean_skill" / "SKILL.md").read_text(encoding="utf-8")
    assert "status: approved" in skill_md
    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(tmp_path))
    assert "clean_skill" in ledger
    assert ledger["clean_skill"]["seeded"] is False
    assert not marker.exists()
    run_result = agent._handle_skill_run("/skill clean_skill")
    assert "ran" in run_result
    assert marker.exists()

