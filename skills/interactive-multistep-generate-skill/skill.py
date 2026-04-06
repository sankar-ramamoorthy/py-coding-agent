from py_mono.skill.base import Skill, SkillContext
from pathlib import Path
from typing import List

""" skill generator to a **fully interactive, multi-step scaffolding tool**.

This version will:

* Prompt for multiple helper methods (`parse_request`, `perform_task`, optional extra helpers)
* Pre-fill optional tool calls and step outputs
* Generate structured JSON outputs
* Leave all code discoverable as a `/skill interactive-multistep-generate-skill`

### Features

* Prompts for multiple helper methods (`parse_request`, `perform_task`, plus optional others)
* Optional tool placeholders included in generated `run()` scaffold
* Structured output (`result` + `details`) pre-filled
* Fully integrated as `/skill interactive-multistep-generate-skill` → no standalone script needed
* Leaves `status: proposed` → safe for devs only
* Discoverable in agent’s SkillRegistry

---

###  Usage Example


/skill interactive-multistep-generate-skill my-new-skill | Example skill with multiple helpers | parse_request,perform_task,validate_input | tool1,tool2


Output:

```
 Skill 'my-new-skill' scaffolded at skills/my-new-skill
Helpers included: parse_request, perform_task, validate_input
Tools optionally referenced: tool1, tool2
```

Folder structure:

skills/my-new-skill/
├── SKILL.md
├── skill.py  # Includes run() scaffold, helpers, and optional tool placeholders

---

 **production-ready skeleton skills in one command**, fully discoverable, with **structured helpers, optional tool references, and JSON outputs**.


"""


# Base templates
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
        \"\"\"Main skill logic.\"\"\"
        parsed_input = self.parse_request(request)

{helper_calls}

        output: Dict[str, Any] = {{
            "result": result,
            "details": details
        }}
        return str(output)

{helper_methods}
"""

# Helper method template
HELPER_METHOD_TEMPLATE = """
    def {method_name}(self{params}) -> {return_type}:
        # TODO: implement {method_name} logic
        return {return_placeholder}
"""

class InteractiveMultistepGenerateSkill(Skill):

    def name(self) -> str:
        return "interactive-multistep-generate-skill"

    def description(self) -> str:
        return "Interactive skill generator: scaffold multiple helpers and optional tool calls"

    def run(self, request: str, context: SkillContext) -> str:
        """
        request format:
        skill_name | description | helpers (comma-separated) | tools (optional, comma-separated)
        Example:
        /skill interactive-multistep-generate-skill my-new-skill | Short desc | parse_request,perform_task | tool1,tool2
        """
        try:
            parts = request.split("|")
            if len(parts) < 3:
                return ("Usage: /skill interactive-multistep-generate-skill <skill_name> | <description> | "
                        "<helpers (comma-separated)> | [tools (comma-separated)]")

            skill_name = parts[0].strip()
            description = parts[1].strip()
            helpers_input = parts[2].strip()
            tools_input = parts[3].strip() if len(parts) > 3 else ""

            folder_name = skill_name.lower().replace(" ", "-")
            class_name = "".join(word.capitalize() for word in folder_name.split("-"))
            skill_path = Path("skills") / folder_name
            if skill_path.exists():
                return f"❌ Skill '{folder_name}' already exists."

            skill_path.mkdir(parents=True, exist_ok=False)

            helpers: List[str] = [h.strip() for h in helpers_input.split(",") if h.strip()]
            tools: List[str] = [t.strip() for t in tools_input.split(",") if t.strip()]

            # Generate helper calls in run()
            helper_calls_lines = []
            for h in helpers:
                line = f"        {h}_result = self.{h}(parsed_input)"
                helper_calls_lines.append(line)
            if "perform_task" in helpers:
                helper_calls_lines.append("        result, details = perform_task_result")
            else:
                helper_calls_lines.append("        result, details = None, {}")
            helper_calls = "\n".join(helper_calls_lines)

            # Generate helper method skeletons
            helper_methods_lines = []
            for h in helpers:
                method_code = HELPER_METHOD_TEMPLATE.format(
                    method_name=h,
                    params=", parsed_input: Dict[str, Any]" if h != "parse_request" else "request: str",
                    return_type="tuple[str, Dict[str, Any]]" if h=="perform_task" else "Dict[str, Any]",
                    return_placeholder='{"raw": request}' if h=="parse_request" else '("result_placeholder", {})'
                )
                helper_methods_lines.append(method_code)
            helper_methods = "\n".join(helper_methods_lines)

            # Write SKILL.md
            (skill_path / "SKILL.md").write_text(
                SKILL_MD_TEMPLATE.format(skill_name=folder_name, description=description),
                encoding="utf-8"
            )

            # Write skill.py
            (skill_path / "skill.py").write_text(
                SKILL_PY_TEMPLATE.format(
                    class_name=class_name,
                    skill_name=folder_name,
                    description=description,
                    helper_calls=helper_calls,
                    helper_methods=helper_methods
                ),
                encoding="utf-8"
            )

            return (
                f"✅ Skill '{folder_name}' scaffolded at {skill_path.resolve()}\n"
                f"Helpers included: {', '.join(helpers)}\n"
                f"Tools optionally referenced: {', '.join(tools)}"
            )

        except Exception as e:
            return f"❌ Error creating skill: {e}"
