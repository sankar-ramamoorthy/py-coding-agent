from py_mono.skill.base import Skill, SkillContext, SKILLS_DIR
from pathlib import Path

"""
an **interactive, enhanced Generate Skill dev skill**.

It  **prompts the user for multiple pieces of info**, scaffolds `parse_request` and `perform_task` helpers, and pre-fills comments for each step. This generates **production-ready skeleton skills** in one command.
##  How It Works

1. Invoke via CLI:

/skill interactive-generate-skill my-new-skill | A short description of what the skill does

2. Creates folder:

skills/my-new-skill/
├── SKILL.md
├── skill.py

3. Pre-fills:

* `parse_request()` helper for structured input
* `perform_task()` helper for main workflow
* Comments for step-by-step guidance

4. Skill is **discoverable** in `/skill help` and safe for devs:

* `status: proposed` prevents accidental production use
* Scaffold is fully compatible with agent's SkillRegistry

"""

# Advanced template strings
SKILL_MD_TEMPLATE = """---
name: {skill_name}
description: {description}
status: proposed
---
"""

SKILL_PY_TEMPLATE = """from py_mono.skill.base import Skill, SkillContext
from typing import Dict, Any

class {class_name}(Skill):

    def name(self) -> str:
        return "{skill_name}"

    def description(self) -> str:
        return "{description}"

    def run(self, request: str, context: SkillContext) -> str:
        \"""
        Main execution method.
        Steps:
        1. Parse input
        2. Call optional helper tools
        3. Execute main workflow
        4. Format output
        \"""
        parsed_input = self.parse_request(request)

        # Step 2: Optional tools
        # Example: result_from_tool = context.tools.get('tool_name', lambda x: x)(parsed_input)

        # Step 3: Main workflow
        result, details = self.perform_task(parsed_input)

        # Step 4: Format output
        output: Dict[str, Any] = {{
            "result": result,
            "details": details
        }}
        return str(output)

    # --- Helper methods ---

    def parse_request(self, request: str) -> Dict[str, Any]:
        # TODO: Implement parsing logic
        return {{"raw": request}}

    def perform_task(self, parsed_input: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        # TODO: Implement main task logic
        result = f"Processed: {{parsed_input.get('raw')}}"
        details = {{"steps_completed": 1}}
        return result, details
"""

class InteractiveGenerateSkill(Skill):

    def name(self) -> str:
        return "interactive-generate-skill"

    def description(self) -> str:
        return "Interactive skill generator: scaffold a fully structured skill for development"

    def run(self, request: str, context: SkillContext) -> str:
        """
        request format:
        skill_name | description
        """
        try:
            # Step 1: Parse user input for skill_name and description
            parts = request.split("|", 1)
            if len(parts) != 2:
                return "Usage: /skill interactive-generate-skill <skill_name> | <description>"

            skill_name = parts[0].strip()
            description = parts[1].strip()

            folder_name = skill_name.lower().replace(" ", "-")
            class_name = "".join(word.capitalize() for word in folder_name.split("-"))

            #skill_path = Path("skills") / folder_name
            skill_path = SKILLS_DIR / skill_name
            if skill_path.exists():
                return f"❌ Skill '{folder_name}' already exists."

            skill_path.mkdir(parents=True, exist_ok=False)

            # Step 2: Write SKILL.md
            (skill_path / "SKILL.md").write_text(
                SKILL_MD_TEMPLATE.format(skill_name=folder_name, description=description),
                encoding="utf-8"
            )

            # Step 3: Write skill.py with interactive scaffolds
            (skill_path / "skill.py").write_text(
                SKILL_PY_TEMPLATE.format(class_name=class_name, skill_name=folder_name, description=description),
                encoding="utf-8"
            )

            return (
                f"✅ Skill '{folder_name}' scaffolded at {skill_path.resolve()}\n"
                "Skeleton includes parse_request() and perform_task() helpers for structured workflow."
            )

        except Exception as e:
            return f"❌ Error creating skill: {e}"
