from py_mono.skill.base import Skill, SkillContext
import logging
import re
from pathlib import Path
from typing import Optional
import json

logger = logging.getLogger(__name__)


class Listtxt1Skill(Skill):

    def name(self) -> str:
        return "listtxt1"

    def description(self) -> str:
        return "list all .txt files in directory specifid by user. skill shpuld take in oneoptional directory name parameter. defaulting t current directory. add print debug lines for tracing"

    def run(self, request: str, context: SkillContext) -> str:
        try:

            # Strip command prefix
            prefix = "/skill listtxt1"
            raw = request.strip()
            if raw.startswith(prefix):
                raw = raw[len(prefix):].strip()

            parts = raw.split()
            if len(parts) == 1:
                target_dir = parts[0]
            else:
                target_dir = "."
            print(f"[listtxt1] Scanning directory: {target_dir}")
            list_files_tool = context.agent_tools.get("list_files")
            if not list_files_tool:
                return "[listtxt1] Error: list_files tool not available"

            result = list_files_tool.run(path=target_dir)
            entries = json.loads(result)
            txt_files = [
                entry["name"]
                for entry in entries
                if entry.get("type") == "file" and entry.get("name", "").endswith(".txt")
            ]

            return "\n".join(txt_files) if txt_files else "No .txt files found."
        
        except Exception as e:
            return f"[listtxt1] Error: {e}"