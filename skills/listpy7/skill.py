from py_mono.skill.base import Skill, SkillContext

class Listpy7Skill(Skill):

    def name(self) -> str:
        return "listpy7"

    def description(self) -> str:
        return "list all python programs in '.'"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            tool = context.agent_tools.get("shell")
            if not tool:
                return "Error: shell tool not available"

            result = tool.run(command="find . -type f -name \"*.py\"")

            if not result:
                return "No Python files found in the workspace."

            return result
        except Exception as e:
            return f"[listpy7] Error: {e}"