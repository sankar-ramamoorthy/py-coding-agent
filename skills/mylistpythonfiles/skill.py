from py_mono.skill.base import Skill, SkillContext
class MylistpythonfilesSkill(Skill):
    """List all Python (.py) files in the current workspace directory"""

    def name(self):
        return "mylistpythonfiles"

    def description(self):
        return "List all python files in current folder"

    def run(self, request: str, context: SkillContext):
        try:
            workspace = context.workspace_root
            files = [
                f.name
                for f in workspace.glob("*.py")
                if f.is_file() and f != workspace / "__init__.py"
            ]
            if not files:
                return "No Python files found in current directory"
            return "\n".join(files)
        except Exception as e:
            return f"[mylistpythonfiles] Error: {e}"