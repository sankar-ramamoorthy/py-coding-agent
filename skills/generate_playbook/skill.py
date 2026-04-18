"""
generate_playbook — LLM-powered playbook generator.

Creates a Markdown reasoning playbook using a single LLM call.

Usage:
    /skill generate_playbook <category> | <description>

NOTE: generate_playbook only produces a .md playbook file. 
No Python code is created by this workflow.    
"""

import logging
import re
from pathlib import Path
from typing import Optional

from py_mono.skill.base import Skill, SkillContext

logger = logging.getLogger(__name__)

PLAYBOOKS_DIR = Path(__file__).parent.parent.parent / "playbooks"


class GeneratePlaybook(Skill):

    def name(self) -> str:
        return "generate_playbook"

    def description(self) -> str:
        return "Generate a reasoning playbook (Markdown)"

    def run(self, request: str, context: SkillContext) -> str:
        parsed = self._parse_request(request)
        if isinstance(parsed, str):
            return parsed

        category, description = parsed

        # ------------------------------------------------------------------
        # Build output path
        # ------------------------------------------------------------------
        category_dir = PLAYBOOKS_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        #filename = description.lower().replace(" ", "_")[:40] + ".md"
        slug = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")
        filename = slug[:50] + ".md"

        path = category_dir / filename

        if path.exists():
            return f"❌ Playbook already exists: {path}"

        # ------------------------------------------------------------------
        # LLM call
        # ------------------------------------------------------------------
        content = self._call_llm(context, category, description)
        if not content:
            return "❌ Failed to generate playbook."

        # Basic validation
        if not self._is_valid_markdown(content):
            return "❌ Generated content is not valid Markdown structure."

        # Save
        path.write_text(content, encoding="utf-8")
        logger.debug(f"Generated playbook content:\n{content}")

        return (
            f"✅ Playbook created\n\n"
            f"Location: {path}\n\n"
            f"Next step: use it in reasoning retrieval"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_request(self, request: str):
        prefix = "/skill generate_playbook"
        raw = request.strip()

        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()

        parts = raw.split("|", 1)
        if len(parts) != 2:
            return (
                "Usage: /skill generate_playbook <category> | <description>\n"
                "Example: /skill generate_playbook testing | pytest guide"
            )

        category = parts[0].strip().lower()
        description = parts[1].strip()

        if not category:
            return "❌ Category cannot be empty."
        if not description:
            return "❌ Description cannot be empty."

        return category, description

    def _call_llm(self, context: SkillContext, category: str, description: str) -> Optional[str]:
        try:
            provider = context.session_manager.get_active_provider()

            prompt = f"""
You are generating a reasoning playbook for a coding agent.

Output ONLY Markdown.
No explanations. No code fences.

Category: {category}
Description: {description}

Structure:

# Title

## When to use
## Steps
## Examples
## Pitfalls

Keep it concise and practical.
"""

            response = provider.generate(
                messages=[{"role": "user", "content": prompt}],
                tools=None,
            )

            text = response.get("text", "").strip()
            return text if text else None

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _is_valid_markdown(self, text: str) -> bool:
        required_sections = [
            "#",
            "## When to use",
            "## Steps",
        ]
        return all(section in text for section in required_sections)