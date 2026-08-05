from py_mono.skill.base import Skill, SkillContext
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class ListallpySkill(Skill):

    def name(self) -> str:
        return "listallpy"

    def description(self) -> str:
        return "list all python programs *.py in the current directory"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            workspace = Path(context.workspace_root)
            py_files = [f for f in workspace.rglob("*.py") if f.is_file()]
            file_names = [f.name for f in py_files]
            return "\n".join(file_names) or "No Python files found."
        except Exception as e:
            return f"[listallpy] Error: {e}"