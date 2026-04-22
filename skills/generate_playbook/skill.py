"""
generate_playbook — LLM-powered playbook generator.

Creates a Markdown reasoning playbook with YAML front-matter for PlaybookRegistry.

Usage:
    /skill generate_playbook category:<name> | description:<text> | keywords:<csv> | dry_run:<true|false>

ADR-016 compliant: uses write_file tool only. No subprocess, no network.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple, List
import yaml

from py_mono.skill.base import Skill, SkillContext

logger = logging.getLogger(__name__)

PLAYBOOKS_DIR = Path(__file__).parent.parent.parent / "playbooks"

class GeneratePlaybook(Skill):

    def name(self) -> str:
        return "generate_playbook"

    def description(self) -> str:
        return "Generate a reasoning playbook Markdown file with YAML front-matter"

    def run(self, request: str, context: SkillContext) -> str:
        parsed = self._parse_request(request)
        if isinstance(parsed, str):
            return parsed

        category, description, keywords, dry_run = parsed

        # ------------------------------------------------------------------
        # Build output path + safety checks
        # ------------------------------------------------------------------
        if ".." in category or "/" in category:
            return "❌ Category cannot contain path separators."

        category_dir = PLAYBOOKS_DIR / category
        slug = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")[:50]
        filename = f"{slug}.md"
        path = category_dir / filename

        if path.exists():
            return f"❌ Playbook already exists: {path}"

        # ------------------------------------------------------------------
        # LLM call
        # ------------------------------------------------------------------
        content = self._call_llm(context, category, description, keywords)
        if not content:
            return "❌ Failed to generate playbook."

        # ------------------------------------------------------------------
        # Validate front-matter + structure
        # ------------------------------------------------------------------
        valid, err = self._validate_playbook(content)
        if not valid:
            return f"❌ Generated playbook invalid: {err}"

        if dry_run:
            return (
                f"[DRY RUN] Would create {path}\n\n"
                "=== Content Preview ===\n"
                f"{content[:800]}{'...' if len(content) > 800 else ''}"
            )

        # ------------------------------------------------------------------
        # Write file
        # ------------------------------------------------------------------
        category_dir.mkdir(parents=True, exist_ok=True)
        write_file = context.agent_tools.get("write_file")
        if not write_file:
            return "[generate_playbook] Tool 'write_file' not found in agent_tools."

        result = write_file.func({"path": str(path), "content": content})
        if "Error" in str(result):
            return f"Failed to write playbook:\n{result}"

        logger.debug(f"Generated playbook:\n{content}")
        return (
            f"✅ Playbook created\n\n"
            f"Location: {path}\n"
            f"Keywords: {', '.join(keywords)}\n\n"
            f"Next: /clear and test with a prompt that matches keywords."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_request(self, request: str) -> str | Tuple[str, str, List[str], bool]:
        raw = request.strip()
        if raw.startswith("/skill generate_playbook"):
            raw = raw[len("/skill generate_playbook"):].strip()

        category = self._extract_str(raw, "category:")
        description = self._extract_str(raw, "description:")
        keywords_str = self._extract_str(raw, "keywords:")
        dry_run = self._extract_str(raw, "dry_run:") == "true"

        if not category:
            return ("Usage: /skill generate_playbook category:<name> | "
                    "description:<text> | keywords:<csv> | dry_run:<true|false>\n"
                    "Example: /skill generate_playbook category:testing | "
                    "description:pytest guide | keywords:test,pytest,assert | dry_run:false")

        if not description:
            return "❌ Description cannot be empty."

        keywords = [k.strip() for k in keywords_str.split(",")] if keywords_str else []
        if not keywords:
            # Auto-generate from description if not provided
            keywords = re.findall(r"\b\w{4,}\b", description.lower())[:5]

        return category, description, keywords, dry_run

    def _extract_str(self, text: str, key: str) -> Optional[str]:
        pattern = rf"{key}(?P<value>.*?)(?:\s+\w+:|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group("value").strip() if match else None

    def _call_llm(self, context: SkillContext, category: str, description: str, keywords: List[str]) -> Optional[str]:
        try:
            provider = context.session_manager.get_active_provider()
            keywords_csv = ", ".join(keywords)

            prompt = f"""You are generating a reasoning playbook for a coding agent's PlaybookRegistry.

Output ONLY Markdown with YAML front-matter. No explanations. No code fences.

Rules:
1. Front-matter must include: name, description, keywords, triggers, category, priority
2. Body must include: # Title, ## When to use, ## Steps, ## Examples, ## Pitfalls
3. Steps must be actionable: use `read_file`, `write_file`, `shell`, or other skills. No vague advice.
4. No executable code. This guides reasoning only.

Input:
Category: {category}
Description: {description}
Keywords: {keywords_csv}

Template:
---
name: <slug-from-description>
description: <one-line-summary>
keywords: [{keywords_csv}]
triggers: ["<user-phrase-1>", "<user-phrase-2>"]
category: {category}
priority: medium
---

# <Title>

## When to use
<2-3 bullet points on trigger conditions>

## Steps
### Step 0: Gate Check
### Step 1: <Action>
...

## Examples
Input: <example-user-request>
Output: <expected-agent-behavior>

## Pitfalls
<common mistakes>

Generate it now.
"""

            response = provider.generate(
                messages=[{"role": "user", "content": prompt}],
                tools=None,
            )
            return response.get("text", "").strip() or None

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _validate_playbook(self, text: str) -> Tuple[bool, str]:
        # Check YAML front-matter
        if not text.startswith("---"):
            return False, "Missing YAML front-matter"

        try:
            parts = text.split("---", 2)
            if len(parts) < 3:
                return False, "Malformed YAML front-matter"
            yaml.safe_load(parts[1]) # Will raise if invalid
            body = parts[2]
        except Exception as e:
            return False, f"Invalid YAML: {e}"

        # Check required sections
        required = ["#", "## When to use", "## Steps"]
        missing = [s for s in required if s not in body]
        if missing:
            return False, f"Missing sections: {missing}"

        # Check for code execution anti-patterns
        banned = ["```python", "subprocess.run", "os.system", "!pip install"]
        found = [b for b in banned if b in body]
        if found:
            return False, f"Contains executable code: {found}"

        return True, ""