"""Tests for dynamic-tool gating and static validation (ISS-003)."""

from py_mono.tools.tool_loader import load_dynamic_tools


VALID_TOOL_PY = '''
from py_mono.tools.tool import Tool

def my_func(x):
    return x

my_tool = Tool(name="my_tool", description="demo", func=my_func, parameters={
    "type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]
})
'''

FORBIDDEN_TOOL_PY = '''
import os
os.system("echo hi")

from py_mono.tools.tool import Tool

def my_func(x):
    return x

my_tool = Tool(name="my_tool", description="demo", func=my_func, parameters={
    "type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]
})
'''

SYNTAX_ERROR_TOOL_PY = "def broken(:\n    pass\n"


def test_valid_dynamic_tool_loads(tmp_path):
    (tmp_path / "my_tool.py").write_text(VALID_TOOL_PY, encoding="utf-8")

    tools = load_dynamic_tools(str(tmp_path))

    assert [t.name for t in tools] == ["my_tool"]


def test_forbidden_pattern_file_is_skipped(tmp_path):
    (tmp_path / "bad_tool.py").write_text(FORBIDDEN_TOOL_PY, encoding="utf-8")

    tools = load_dynamic_tools(str(tmp_path))

    assert tools == []


def test_syntax_error_file_is_skipped(tmp_path):
    (tmp_path / "broken_tool.py").write_text(SYNTAX_ERROR_TOOL_PY, encoding="utf-8")

    tools = load_dynamic_tools(str(tmp_path))

    assert tools == []


def test_valid_and_forbidden_files_together_only_valid_loads(tmp_path):
    (tmp_path / "good.py").write_text(VALID_TOOL_PY, encoding="utf-8")
    (tmp_path / "bad.py").write_text(FORBIDDEN_TOOL_PY, encoding="utf-8")

    tools = load_dynamic_tools(str(tmp_path))

    assert [t.name for t in tools] == ["my_tool"]


def test_missing_folder_returns_empty_list(tmp_path):
    missing = tmp_path / "does_not_exist"
    assert load_dynamic_tools(str(missing)) == []


# ---------------------------------------------------------------------------
# ENABLE_DYNAMIC_TOOLS gating (main.py / agent.py call sites)
# ---------------------------------------------------------------------------

def test_enable_dynamic_tools_defaults_false(monkeypatch):
    monkeypatch.delenv("ENABLE_DYNAMIC_TOOLS", raising=False)
    import importlib
    from py_mono import config as config_module
    importlib.reload(config_module)
    assert config_module.ENABLE_DYNAMIC_TOOLS is False


def test_enable_dynamic_tools_parses_truthy_values(monkeypatch):
    monkeypatch.setenv("ENABLE_DYNAMIC_TOOLS", "true")
    import importlib
    from py_mono import config as config_module
    importlib.reload(config_module)
    assert config_module.ENABLE_DYNAMIC_TOOLS is True
