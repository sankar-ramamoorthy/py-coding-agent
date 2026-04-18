from pathlib import Path

from py_mono.tools import create_tool as create_tool_module


def test_create_tool_writes_file_for_valid_name(tmp_path, monkeypatch):
    monkeypatch.setattr(create_tool_module, "TOOLS_DIR", tmp_path / "dynamic_tools")

    result = create_tool_module.create_tool("sample_tool", "x = 1\n")

    created = tmp_path / "dynamic_tools" / "sample_tool.py"
    assert created.exists()
    assert created.read_text(encoding="utf-8") == "x = 1\n"
    assert str(created.resolve()) in result


def test_create_tool_rejects_invalid_module_name(tmp_path, monkeypatch):
    monkeypatch.setattr(create_tool_module, "TOOLS_DIR", tmp_path / "dynamic_tools")

    result = create_tool_module.create_tool("../escape", "x = 1\n")

    assert "Error: tool name must be a valid Python identifier" in result
    assert not any(tmp_path.rglob("*.py"))


def test_create_tool_tool_declares_required_parameters():
    parameters = create_tool_module.create_tool_tool.parameters

    assert parameters["required"] == ["name", "code"]
    assert parameters["properties"]["name"]["type"] == "string"
    assert parameters["properties"]["code"]["type"] == "string"
