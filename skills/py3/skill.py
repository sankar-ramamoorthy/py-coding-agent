from py_mono.skill.base import Skill, SkillContext
from pathlib import Path
from typing import List

class Py3Skill(Skill):

    def name(self) -> str:
        return "py3"

    def description(self) -> str:
        return "list all python programs in ."

    def run(self, request: str, context: SkillContext) -> str:
        try:
            tool = context.agent_tools.get("list_files")
            if not tool:
                return "Error: list_files tool not available"

            result = tool.run({ "path": "." })
            files = result.get("files", [])

            py_files = [f for f in files if Path(f).suffix == ".py"]
            if not py_files:
                return "No .py files found in the current directory."

            return str(py_files)
        except Exception as e:
            return f"[py3] Error: {e}"