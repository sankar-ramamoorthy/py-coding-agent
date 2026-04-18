import json

from py_mono.skill.base import Skill, SkillContext


class ListallpySkill(Skill):
    def name(self) -> str:
        return "listallpy"

    def description(self) -> str:
        return "list all python programs in current directory"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            list_files = context.agent_tools.get("list_files")
            if not list_files:
                return "[listallpy] Error: list_files tool not available"

            result = list_files.run(path=".")
            entries = json.loads(result)

            py_files = [
                entry["name"]
                for entry in entries
                if entry.get("type") == "file" and entry.get("name", "").endswith(".py")
            ]

            return "\n".join(py_files) if py_files else "No Python files found."
        except Exception as e:
            return f"[listallpy] Error: {e}"
