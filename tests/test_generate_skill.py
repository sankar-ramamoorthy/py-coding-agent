import importlib.util
from pathlib import Path

from py_mono.skill import approval_ledger
from py_mono.agent.agent import Agent
from py_mono.skill.base import SkillContext, SkillRegistry


SKILL_MD = """---
name: echo-request
description: Echo the request.
status: proposed
allowed_tools: []
---
# echo-request

Return the request text.
"""


VALID_SKILL_PY = '''
from py_mono.skill.base import Skill, SkillContext

class EchoRequestSkill(Skill):
    def name(self):
        return "echo-request"

    def description(self):
        return "Echo the request."

    def run(self, request, context):
        return request
'''


FAILING_SMOKE_SKILL_PY = '''
from py_mono.skill.base import Skill, SkillContext

class EchoRequestSkill(Skill):
    def name(self):
        return "echo-request"

    def description(self):
        return "Echo the request."

    def run(self, request, context):
        raise RuntimeError("cannot run")
'''


class StubProvider:
    model_name = "stub-model"

    def __init__(self, responses):
        self._responses = list(responses)
        self.messages = []

    def generate(self, messages, tools=None):
        self.messages.append(messages)
        return {"text": self._responses.pop(0)}


class StubSessionManager:
    def __init__(self, responses):
        self.provider = StubProvider(responses)

    def get_active_provider(self):
        return self.provider


def load_generate_skill_module():
    path = Path("skills/generate_skill/skill.py")
    spec = importlib.util.spec_from_file_location("generate_skill_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_context(responses):
    return SkillContext(
        workspace_root=Path("."),
        agent_tools={},
        session_manager=StubSessionManager(responses),
    )


def write_approved_existing_skill(skills_dir: Path, name: str = "echo-request") -> Path:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Echo old.\nstatus: approved\nallowed_tools: []\n---\n# old\n",
        encoding="utf-8",
    )
    (skill_dir / "skill.py").write_text(
        f'''
from py_mono.skill.base import Skill, SkillContext

class EchoRequestSkill(Skill):
    def name(self):
        return "{name}"

    def description(self):
        return "Echo old."

    def run(self, request, context):
        return "old"
''',
        encoding="utf-8",
    )
    ledger = {}
    approval_ledger.record_approval(ledger, name, skill_dir / "skill.py")
    approval_ledger.save_ledger(ledger, approval_ledger.ledger_path_for(skills_dir))
    return skill_dir


def test_generate_skill_success_reports_lifecycle_and_remains_proposed(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)

    result = module.GenerateSkill().run(
        "/skill generate_skill echo-request | Return the request text unchanged.",
        make_context([SKILL_MD, VALID_SKILL_PY]),
    )

    assert "Lifecycle:" in result
    assert "Critique: passed" in result
    assert "Generate: passed" in result
    assert "Validate: passed" in result
    assert "Test: passed" in result
    assert "Propose: passed" in result
    assert "Status: proposed" in result
    assert "Approve: /approve echo-request" in result

    skill_md = (tmp_path / "echo-request" / "SKILL.md").read_text(encoding="utf-8")
    assert "status: proposed" in skill_md


def test_generate_skill_success_does_not_write_approval_ledger(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)

    module.GenerateSkill().run(
        "/skill generate_skill echo-request | Return the request text unchanged.",
        make_context([SKILL_MD, VALID_SKILL_PY]),
    )

    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(tmp_path))
    assert "echo-request" not in ledger


def test_generate_skill_smoke_failure_blocks_approval_ready_response(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)

    result = module.GenerateSkill().run(
        "/skill generate_skill echo-request | Return the request text unchanged.",
        make_context([SKILL_MD, FAILING_SMOKE_SKILL_PY]),
    )

    assert "Test: failed" in result
    assert "RuntimeError: cannot run" in result
    assert "Propose: skipped" in result
    assert "Approve: /approve echo-request" not in result
    assert "Status: proposed" not in result


def test_generate_skill_regeneration_writes_candidate_and_shows_diff(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)
    skill_dir = write_approved_existing_skill(tmp_path)

    result = module.GenerateSkill().run(
        "/skill generate_skill echo-request | Return the request text unchanged.",
        make_context([SKILL_MD, VALID_SKILL_PY]),
    )

    assert "Regeneration diff:" in result
    assert "--- SKILL.md ---" in result
    assert "--- skill.py ---" in result
    assert "Status: proposed" in result
    assert "Review:  " in result
    assert ".candidate" in result
    assert (skill_dir / "skill.py").read_text(encoding="utf-8").find('return "old"') != -1
    assert (skill_dir / ".candidate" / "skill.py").exists()


def test_generate_skill_regeneration_reports_missing_baseline(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)
    skill_dir = tmp_path / "echo-request"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (skill_dir / "skill.py").write_text(VALID_SKILL_PY, encoding="utf-8")

    result = module.GenerateSkill().run(
        "/skill generate_skill echo-request | Return the request text unchanged.",
        make_context([SKILL_MD, VALID_SKILL_PY]),
    )

    assert "Regeneration diff:" in result
    assert "Baseline unavailable" in result
    assert "No approved baseline" in result


def test_approve_promotes_regeneration_candidate_and_records_ledger(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)
    skill_dir = write_approved_existing_skill(tmp_path)
    module.GenerateSkill().run(
        "/skill generate_skill echo-request | Return the request text unchanged.",
        make_context([SKILL_MD, VALID_SKILL_PY]),
    )

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()
    agent = Agent(StubSessionManager([]), tools=[], skill_registry=registry, debug=False)
    result = agent._handle_skill_approve("echo-request")

    assert "approved and ready" in result
    assert not (skill_dir / ".candidate").exists()
    assert 'return request' in (skill_dir / "skill.py").read_text(encoding="utf-8")
    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(tmp_path))
    assert approval_ledger.is_approved(ledger, "echo-request", skill_dir / "skill.py")
    registry.reload_skill("echo-request")
    assert registry.get("echo-request") is not None


def test_approve_rejects_invalid_candidate_without_overwriting_original(tmp_path):
    skill_dir = write_approved_existing_skill(tmp_path)
    candidate_dir = skill_dir / ".candidate"
    candidate_dir.mkdir()
    (candidate_dir / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (candidate_dir / "skill.py").write_text("not valid python", encoding="utf-8")
    original_code = (skill_dir / "skill.py").read_text(encoding="utf-8")

    registry = SkillRegistry(skills_dir=tmp_path)
    registry.load()
    agent = Agent(StubSessionManager([]), tools=[], skill_registry=registry, debug=False)
    result = agent._handle_skill_approve("echo-request")

    assert "failed validation" in result
    assert (skill_dir / "skill.py").read_text(encoding="utf-8") == original_code
    assert (candidate_dir / "skill.py").exists()


def test_generate_skill_evolve_requires_failure_context(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)
    monkeypatch.setattr(module, "latest_failure_context", lambda skill_name: None)
    write_approved_existing_skill(tmp_path)

    result = module.GenerateSkill().run(
        "/skill generate_skill --evolve echo-request",
        make_context([]),
    )

    assert "No usable failure context" in result


def test_generate_skill_evolve_uses_failure_context_and_lifecycle(tmp_path, monkeypatch):
    module = load_generate_skill_module()
    monkeypatch.setattr(module, "SKILLS_DIR", tmp_path)
    write_approved_existing_skill(tmp_path)

    class FailureContext:
        def to_prompt_text(self):
            return "Recent failure for skill 'echo-request': boom"

    monkeypatch.setattr(module, "latest_failure_context", lambda skill_name: FailureContext())
    context = make_context([SKILL_MD, VALID_SKILL_PY])

    result = module.GenerateSkill().run(
        "/skill generate_skill --evolve echo-request",
        context,
    )

    assert "Failure context:" in result
    assert "boom" in result
    assert "Lifecycle:" in result
    assert "Regeneration diff:" in result
    assert ".candidate" in result
    first_prompt = context.session_manager.provider.messages[0][0]["content"]
    assert "Recent failure for skill 'echo-request': boom" in first_prompt
