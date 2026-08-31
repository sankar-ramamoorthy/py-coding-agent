# py_mono/skill/base.py
"""
Core skills framework for py-coding-agent.

Defines:
    Skill         — abstract base class for all skills
    SkillContext  — shared context passed to every skill at runtime
    SkillRegistry — discovers and manages skills from the skills/ directory

Skills live under:
    skills/<skill_name>/
        SKILL.md    — human-readable spec (required)
        skill.py    — optional Python implementation (Skill subclass)

See ADR-010 for architecture details.
"""

from __future__ import annotations

import importlib.util
import logging
from abc import ABC, abstractmethod
from pathlib import Path
import yaml
from typing import Dict, List, Optional, TypedDict, TYPE_CHECKING

from py_mono.skill import approval_ledger
from py_mono.skill.diffing import has_candidate

if TYPE_CHECKING:
    from py_mono.session.session_manager import SessionManager
    from py_mono.tools.tool import Tool

logger = logging.getLogger(__name__)

# Root of the skills directory — sits alongside py_mono/ at project root
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


class ListedSkill(TypedDict):
    name: str
    description: str
    status: str
    has_code: bool
    has_candidate: bool


# ---------------------------------------------------------------------------
# SkillContext
# ---------------------------------------------------------------------------

class SkillContext:
    """
    Shared context passed to every skill at runtime.

    Provides access to:
    - workspace_root  : sandboxed workspace path
    - session_manager : active provider / model info
    - agent_tools     : dict of tool_name → Tool (so skills can call tools)
    """

    def __init__(
        self,
        workspace_root: Path,
        agent_tools: Dict[str, 'Tool'],
        session_manager: Optional['SessionManager'] = None,
    ):
        self.workspace_root = workspace_root
        self.session_manager = session_manager
        self.agent_tools = agent_tools
        self.calling_skill: Optional[str] = None  # track parent skill

    def normalize(self, name: str) -> str:
        """Canonical normalization for skill names."""
        return name.strip().lower().replace("-", "_")

    def __repr__(self) -> str:
        return (
            f"<SkillContext workspace={self.workspace_root} "
            f"tools={list(self.agent_tools.keys())}>"
        )


# ---------------------------------------------------------------------------
# Skill (abstract base)
# ---------------------------------------------------------------------------

class Skill(ABC):
    """Abstract base class for all agent skills."""

    @abstractmethod
    def name(self) -> str:
        """Return the unique skill name (e.g. 'bug_fix')."""
        ...

    @abstractmethod
    def description(self) -> str:
        """Return a one-line description for /skill list."""
        ...

    @abstractmethod
    def run(
        self,
        request: str,
        context: SkillContext,
    ) -> str:
        """Execute the skill and return human-readable result."""
        ...

    def can_handle(self, request: str, context: SkillContext) -> bool:
        text = request.strip()
        norm_name = context.normalize(self.name())

        # CLI mode
        if text.startswith("/skill "):
            parts = text.split(maxsplit=2)
            if len(parts) >= 2:
                return context.normalize(parts[1]) == norm_name
            return False

        # Internal mode (future-proof: chaining / orchestration)
        return context.normalize(text).startswith(norm_name)

    def __repr__(self) -> str:
        return f"<Skill name={self.name()}>"


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------

class SkillRegistry:
    """
    Discovers and manages skills from the skills/ directory.

    Canonical rule:
        ALL skill names are stored internally as lowercase with underscores.
    """

    def __init__(self, skills_dir: Path = SKILLS_DIR):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Skill] = {}       # key = normalized name
        self._metadata: Dict[str, dict] = {}      # key = normalized name
        self._has_code: Dict[str, bool] = {}      # key = normalized name; True if skill.py exists on disk

    # -------------------------
    # Normalization
    # -------------------------
    def _norm(self, name: str) -> str:
        """Canonical normalization for all skill names."""
        return name.strip().lower().replace("-", "_")

    # -------------------------
    # Load / reload
    # -------------------------
    def load(self) -> None:
        self._skills.clear()
        self._metadata.clear()
        self._has_code.clear()

        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        ledger_path = approval_ledger.ledger_path_for(self.skills_dir)
        ledger = approval_ledger.load_ledger(ledger_path)
        ledger_dirty = False

        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            skill_py = skill_dir / "skill.py"

            if not skill_md.exists():
                logger.debug(f"Skipping {skill_dir.name} — no SKILL.md found")
                continue

            meta = self._parse_skill_md(skill_md)
            raw_name = meta.get("name", skill_dir.name)
            name = self._norm(raw_name)
            ledger_names = (name, str(raw_name), skill_dir.name)
            meta["name"] = name
            self._metadata[name] = meta
            self._has_code[name] = skill_py.exists()

            if skill_py.exists():
                status = str(meta.get("status", "proposed")).lower()

                if status == "approved" and not any(ledger_name in ledger for ledger_name in ledger_names):
                    # Pre-existing approved skill, ledger doesn't know it yet —
                    # recognize its current state once, visibly marked as a
                    # seed event rather than a real review.
                    approval_ledger.record_approval(ledger, name, skill_py, seeded=True)
                    ledger_dirty = True
                    logger.info(
                        f"🌱 Auto-seeded approval ledger for '{name}' "
                        f"(pre-existing approved skill, not a review)"
                    )

                if status == "approved" and any(
                    approval_ledger.is_approved(ledger, ledger_name, skill_py)
                    for ledger_name in ledger_names
                ):
                    skill = self._load_skill_py(skill_py, name)
                    if skill:
                        self._skills[name] = skill
                        logger.info(f"✅ Loaded skill '{name}' (status=approved)")
                else:
                    logger.info(
                        f"🔒 Skill '{name}' has skill.py but is not approved/ledger-matched "
                        f"(status={meta.get('status','proposed')}) — not executed"
                    )
            else:
                logger.info(f"📋 Discovered skill spec '{name}' (SKILL.md only)")

        if ledger_dirty:
            approval_ledger.save_ledger(ledger, ledger_path)

    def reload_skill(self, skill_name: str) -> bool:
        name = self._norm(skill_name)
        skill_dir = self._skill_dir_for(skill_name)
        skill_md = skill_dir / "SKILL.md"
        skill_py = skill_dir / "skill.py"

        if not skill_md.exists():
            logger.warning(f"Cannot reload '{name}' — SKILL.md missing")
            return False

        meta = self._parse_skill_md(skill_md)
        raw_name = meta.get("name", skill_dir.name)
        ledger_names = (name, str(raw_name), skill_dir.name)
        meta["name"] = name
        self._metadata[name] = meta
        self._has_code[name] = skill_py.exists()

        if skill_py.exists():
            ledger_path = approval_ledger.ledger_path_for(self.skills_dir)
            ledger = approval_ledger.load_ledger(ledger_path)
            status = str(meta.get("status", "proposed")).lower()

            if status == "approved" and not any(ledger_name in ledger for ledger_name in ledger_names):
                approval_ledger.record_approval(ledger, name, skill_py, seeded=True)
                approval_ledger.save_ledger(ledger, ledger_path)
                logger.info(
                    f"🌱 Auto-seeded approval ledger for '{name}' "
                    f"(pre-existing approved skill, not a review)"
                )

            if status == "approved" and any(
                approval_ledger.is_approved(ledger, ledger_name, skill_py)
                for ledger_name in ledger_names
            ):
                skill = self._load_skill_py(skill_py, name)
                if skill:
                    self._skills[name] = skill
                    logger.info(f"🔄 Reloaded skill '{name}'")
                    return True
                else:
                    self._skills.pop(name, None)
                    logger.warning(f"Failed to reload skill '{name}'")
                    return False
            else:
                self._skills.pop(name, None)
                logger.info(
                    f"🔒 Skill '{name}' not approved/ledger-matched — unloaded "
                    f"(status={meta.get('status','proposed')})"
                )
                return True
        else:
            self._skills.pop(name, None)
            logger.info(f"🔄 Reloaded spec-only skill '{name}'")
            return True

    # -------------------------
    # Accessors
    # -------------------------
    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(self._norm(name))

    def is_approved(self, name: str) -> bool:
        meta = self._metadata.get(self._norm(name), {})
        return meta.get("status", "proposed").lower() == "approved"

    def get_executable(self, name: str) -> Optional[Skill]:
        name = self._norm(name)
        if not self.is_approved(name):
            return None
        return self._skills.get(name)

    def list_skills(self) -> List[ListedSkill]:
        results: List[ListedSkill] = []
        for name, meta in self._metadata.items():
            skill = self._skills.get(name)
            results.append({
                "name": name,
                "description": skill.description() if skill else meta.get("description", "(no description)"),
                "status": meta.get("status", "proposed"),
                # has_code reflects whether skill.py exists on disk, not whether
                # it's currently loaded — a proposed or hash-mismatched skill
                # still has code, it's just not executing yet (see ISS-003).
                "has_code": self._has_code.get(name, False),
                "has_candidate": has_candidate(self._skill_dir_for(name)),
            })
        return results

    def get_skill_md(self, name: str) -> Optional[str]:
        skill_dir = self._skill_dir_for(name)
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text(encoding="utf-8")
        return None

    def skill_dir_for(self, skill_name: str) -> Path:
        return self._skill_dir_for(skill_name)

    # -------------------------
    # Helpers
    # -------------------------
    def _skill_dir_for(self, skill_name: str) -> Path:
        raw_dir = self.skills_dir / skill_name
        if raw_dir.exists():
            return raw_dir
        normalized_dir = self.skills_dir / self._norm(skill_name)
        if normalized_dir.exists():
            return normalized_dir
        hyphenated_dir = self.skills_dir / self._norm(skill_name).replace("_", "-")
        if hyphenated_dir.exists():
            return hyphenated_dir
        return normalized_dir

    def _parse_skill_md(self, skill_md: Path) -> dict:
        try:
            text = skill_md.read_text(encoding="utf-8")
            if not text.startswith("---"):
                return {"name": self._norm(skill_md.parent.name)}

            lines = text.splitlines()
            start = 1
            end = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    end = i
                    break
            if end is None:
                return {"name": self._norm(skill_md.parent.name)}

            yaml_text = "\n".join(lines[start:end])
            meta = yaml.safe_load(yaml_text) or {}
            if "name" not in meta:
                meta["name"] = self._norm(skill_md.parent.name)
            else:
                meta["name"] = self._norm(str(meta["name"]))
            return meta
        except Exception as e:
            logger.warning(f"Could not parse SKILL.md front-matter: {e}")
            return {"name": self._norm(skill_md.parent.name)}

    def _load_skill_py(self, skill_py: Path, skill_name: str) -> Optional[Skill]:
        try:
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}.skill", skill_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr in vars(module).values():
                if isinstance(attr, type) and issubclass(attr, Skill) and attr is not Skill:
                    return attr()
        except Exception as e:
            logger.error(f"Failed to load skill.py for '{skill_name}': {e}")
        return None

    def __repr__(self) -> str:
        return f"<SkillRegistry skills={list(self._skills.keys())}>"
