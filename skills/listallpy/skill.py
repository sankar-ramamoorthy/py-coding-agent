from py_mono.skill.base import Skill, SkillContext
import json
import logging

logger = logging.getLogger(__name__)

class ListallpySkill(Skill):

    def name(self) -> str:
        return "listallpy"

    def description(self) -> str:
        return "list all python programs *.py in the current directory"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            list_files = context.agent_tools["list_files"]
            entries = json.loads(list_files.run(path="."))
            file_names = [
                entry["name"]
                for entry in entries
                if entry.get("type") == "file" and entry.get("name", "").endswith(".py")
            ]
            return "\n".join(file_names) or "No Python files found."
        except Exception as e:
            return f"[listallpy] Error: {e}"