from pathlib import Path

from py_mono.tools import create_tool as create_tool_module


def test_create_tool_writes_file_for_valid_name(tmp_path, monkeypatch):
    monkeypatch.setattr(create_tool_module, "TOOLS_DIR", tmp_path / "dynamic_tools")

    # create_tool wraps the given code in an auto-generated Tool(...) schema
    # (name/description/parameters inferred from the function signature) — it
    # requires a `def`, it does not write arbitrary code verbatim.
    result = create_tool_module.create_tool("sample_tool", "def sample_tool(x):\n    return x\n")

    created = tmp_path / "dynamic_tools" / "sample_tool.py"
    assert created.exists()
    assert "def sample_tool(x):\n    return x\n" in created.read_text(encoding="utf-8")
    assert str(created.resolve()) in result


def test_create_tool_rejects_invalid_module_name(tmp_path, monkeypatch):
    monkeypatch.setattr(create_tool_module, "TOOLS_DIR", tmp_path / "dynamic_tools")

    result = create_tool_module.create_tool("../escape", "def f(): pass\n")

    assert "Error: tool name must be a valid Python identifier" in result
    assert not any(tmp_path.rglob("*.py"))


def test_create_tool_tool_declares_required_parameters():
    parameters = create_tool_module.create_tool_tool.parameters

    assert parameters["required"] == ["name", "code"]
    assert parameters["properties"]["name"]["type"] == "string"
    assert parameters["properties"]["code"]["type"] == "string"


# ---------------------------------------------------------------------------
# ISS-003: static safety validation before writing to disk
# ---------------------------------------------------------------------------

def test_create_tool_refuses_forbidden_pattern_code(tmp_path, monkeypatch):
    monkeypatch.setattr(create_tool_module, "TOOLS_DIR", tmp_path / "dynamic_tools")

    code = "def my_func(x):\n    import os\n    os.system('echo hi')\n    return x\n"
    result = create_tool_module.create_tool("unsafe_tool", code)

    assert "safety check" in result.lower()
    assert not (tmp_path / "dynamic_tools" / "unsafe_tool.py").exists()


def test_create_tool_writes_clean_code_successfully(tmp_path, monkeypatch):
    monkeypatch.setattr(create_tool_module, "TOOLS_DIR", tmp_path / "dynamic_tools")

    code = "def my_func(x):\n    return x\n"
    result = create_tool_module.create_tool("clean_tool", code)

    created = tmp_path / "dynamic_tools" / "clean_tool.py"
    assert created.exists()
    assert "created with schema" in result.lower()
