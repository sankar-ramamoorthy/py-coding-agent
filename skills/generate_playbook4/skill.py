from py_mono.skill.base import Skill, SkillContext
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class GeneratePlaybook4Skill(Skill):

    def name(self) -> str:
        return "generate-playbook4"

    def description(self) -> str:
        return "generate a Markdown playbook( aka skill.md). The playbook guides reasoning (not execution) and only creates a valid markdown .md file. The playbook has to provide structured guidance. The playbook will be provided the issue about which to reason by the user"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            write_tool = context.agent_tools.get("write_file")
            playbook_content = f"""---
name: generated-playbook
description: reasoning playbook for {request}
status: proposed
allowed_tools: read_file, write_file, edit_file, list_files, get_current_datetime
---

# Reasoning Playbook for {request}

## Issue Summary
{request}

## Step-by-Step Reasoning

1. **Understand the Problem**
   - Read any relevant files in the workspace
   - Identify key components mentioned in the issue

2. **Analyze Requirements**
   - List what needs to be accomplished
   - Note any constraints or limitations

3. **Design Approach**
   - Outline a solution strategy
   - Consider alternative approaches

4. **Implementation Notes**
   - Describe what files would need to be modified
   - Explain the reasoning behind each change

5. **Verification Plan**
   - Explain how to verify the solution
   - List expected outcomes

## Next Steps
- Review this playbook
- Execute the plan step by step
- Update the playbook based on findings
"""
            write_tool.run(path="skill.md", content=playbook_content)
            return "Generated reasoning playbook at skill.md"
        except Exception as e:
            return f"[generate-playbook4] Error: {e}"