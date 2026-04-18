import json
from pathlib import Path

from py_mono.skill.base import SkillContext
from py_mono.tools.tool import Tool
from skills.listallpy.skill import ListallpySkill


def test_listallpy_parses_list_files_json_and_filters_python_files():
    payload = json.dumps(
        [
            {"type": "file", "name": "main.py"},
            {"type": "file", "name": "README.md"},
            {"type": "dir", "name": "pkg", "children": []},
            {"type": "file", "name": "util.py"},
        ]
    )

    tools = {
        "list_files": Tool("list_files", "list files", lambda path=".": payload),
    }
    context = SkillContext(workspace_root=Path("."), agent_tools=tools, session_manager=None)

    result = ListallpySkill().run("/skill listallpy", context)

    assert result == "main.py\nutil.py"


def test_listallpy_reports_no_python_files_when_none_exist():
    payload = json.dumps(
        [
            {"type": "file", "name": "README.md"},
            {"type": "dir", "name": "pkg", "children": []},
        ]
    )

    tools = {
        "list_files": Tool("list_files", "list files", lambda path=".": payload),
    }
    context = SkillContext(workspace_root=Path("."), agent_tools=tools, session_manager=None)

    result = ListallpySkill().run("/skill listallpy", context)

    assert result == "No Python files found."
