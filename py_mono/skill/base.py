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
from typing import Any, Dict, List, Optional,TypedDict
from typing import TYPE_CHECKING
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


    def __repr__(self) -> str:
        return (
            f"<SkillContext workspace={self.workspace_root} "
            f"tools={list(self.agent_tools.keys())}>"
        )


# ---------------------------------------------------------------------------
# Skill (abstract base)
# ---------------------------------------------------------------------------

class Skill(ABC):
    """
    Abstract base class for all agent skills.

    Subclasses must implement:
        name()        → unique skill identifier  (e.g. 'bug_fix')
        description() → one-line description shown in /skill list
        run()         → execute the skill, return human-readable result

    Optionally override:
        can_handle()  → return True if this skill should handle the request
                        (default: matches on skill name prefix)
    """

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
        """
        Execute the skill.

        Args:
            request : full user request string (e.g. '/skill bug_fix ...')
            context : SkillContext with workspace, session, and tools

        Returns:
            str: human-readable result or error message
        """
        ...

    def can_handle(self, request: str, context: SkillContext) -> bool:
        """
        Return True if this skill can handle the given request.
        Default: matches if request starts with /skill <name>.
        Override for more sophisticated matching.
        """
        text = request.strip()
        if not text.startswith("/skill "):
            return False
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            return False
        return parts[1].lower() == self.name().lower()

    def __repr__(self) -> str:
        return f"<Skill name={self.name()}>"


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------

class SkillRegistry:
    """
    Discovers and manages skills from the skills/ directory.

    Discovery rules:
    - Scans skills/<skill_name>/SKILL.md for existence (required).
    - If skills/<skill_name>/skill.py exists and defines a Skill subclass,
      it is loaded and registered.
    - Skills with status: proposed in SKILL.md front-matter are NOT executed
      without explicit approval (dry_run only).

    Usage:
        registry = SkillRegistry()
        registry.load()
        skill = registry.get("bug_fix")
        result = skill.run(request, context)
    """

    def __init__(self, skills_dir: Path = SKILLS_DIR):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Skill] = {}
        self._metadata: Dict[str, dict] = {}   # name → parsed SKILL.md front-matter

    def load(self) -> None:
        """
        Scan skills/ directory and load all valid skills.
        Called once at agent startup.
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            skill_py = skill_dir / "skill.py"

            if not skill_md.exists():
                logger.debug(f"Skipping {skill_dir.name} — no SKILL.md found")
                continue

            # Parse SKILL.md front-matter for metadata
            meta = self._parse_skill_md(skill_md)
            skill_name = meta.get("name", skill_dir.name)
            self._metadata[skill_name] = meta

            # Load skill.py if present
            if skill_py.exists():
                skill = self._load_skill_py(skill_py, skill_name)
                if skill:
                    self._skills[skill.name()] = skill
                    status = meta.get("status", "proposed")
                    logger.info(
                        f"✅ Loaded skill '{skill.name()}' "
                        f"(status={status})"
                    )
            else:
                logger.info(
                    f"📋 Discovered skill spec '{skill_name}' "
                    f"(SKILL.md only, no skill.py)"
                )

    def get(self, name: str) -> Optional[Skill]:
        """Return a skill by name, or None if not found."""
        return self._skills.get(name)

    def list_skills(self) -> List[ListedSkill]:
        """
            Return a list of all discovered skills with name, description, status.
            Includes SKILL.md-only skills (no skill.py).
        """
        results: List[ListedSkill] = []

        # Skills with Python implementation
        for name, skill in self._skills.items():
            meta = self._metadata.get(name, {})
            results.append({
                "name": name,
                "description": skill.description(),
                "status": meta.get("status", "proposed"),
                "has_code": True,
            })

        # SKILL.md-only skills (spec exists but no skill.py yet)
        for name, meta in self._metadata.items():
            if name not in self._skills:
                results.append({
                    "name": name,
                    "description": meta.get("description", "(no description)"),
                    "status": meta.get("status", "proposed"),
                    "has_code": False,
                })

        return results #sorted(results, key=lambda x: x["name"])

    def get_skill_md(self, name: str) -> Optional[str]:
        """Return the raw SKILL.md content for a skill, or None."""
        skill_dir = self.skills_dir / name
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text(encoding="utf-8")
        return None

    def is_approved(self, name: str) -> bool:
        """Return True if the skill is approved for execution."""
        meta = self._metadata.get(name, {})
        return meta.get("status", "proposed").lower() == "approved"

    def _parse_skill_md(self, skill_md: Path) -> dict:
        """
        Parse optional YAML front-matter from SKILL.md.
        """
        try:
            text = skill_md.read_text(encoding="utf-8")
            if not text.startswith("---"):
                return {"name": skill_md.parent.name}

            lines = text.splitlines()
            start = 1
            end = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    end = i
                    break
            if end is None:
                return {"name": skill_md.parent.name}

            yaml_text = "\n".join(lines[start:end])
            meta = yaml.safe_load(yaml_text) or {}

            # Fallback name
            if "name" not in meta:
                meta["name"] = skill_md.parent.name

            return meta

        except Exception as e:
            logger.warning(f"Could not parse SKILL.md front-matter: {e}")
        return {"name": skill_md.parent.name}

    def _load_skill_py(self, skill_py: Path, skill_name: str) -> Optional[Skill]:
        """
        Dynamically import skill.py and find the first Skill subclass.
        """
        try:
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}.skill", skill_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr in vars(module).values():
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Skill)
                    and attr is not Skill
                ):
                    return attr() # assumes no‑args __init__; otherwise pull from meta

        except Exception as e:
            logger.error(f"Failed to load skill.py for '{skill_name}': {e}")

        return None

    def __repr__(self) -> str:
        return f"<SkillRegistry skills={list(self._skills.keys())}>"
    def get_executable(self, name: str) -> Optional[Skill]:
        """
        Return a skill if it exists and is approved.
        Otherwise return None.
        """
        if not self.is_approved(name):
            return None
        return self.get(name)

