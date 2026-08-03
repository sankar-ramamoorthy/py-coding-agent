"""Tests for the shell tool's opt-in gating and timeout (ISS-002)."""

from unittest.mock import patch, MagicMock

import subprocess

import pytest

from py_mono.tools import shell as shell_module
from py_mono.main import build_base_tools


def test_build_base_tools_excludes_shell_by_default():
    tools = build_base_tools(enable_shell=False)
    assert "shell" not in {t.name for t in tools}


def test_build_base_tools_includes_shell_when_enabled():
    tools = build_base_tools(enable_shell=True)
    assert "shell" in {t.name for t in tools}


def test_build_base_tools_none_reads_env_config(monkeypatch):
    monkeypatch.setattr("py_mono.main.ENABLE_SHELL_TOOL", False)
    tools = build_base_tools(enable_shell=None)
    assert "shell" not in {t.name for t in tools}

    monkeypatch.setattr("py_mono.main.ENABLE_SHELL_TOOL", True)
    tools = build_base_tools(enable_shell=None)
    assert "shell" in {t.name for t in tools}


def test_build_base_tools_always_includes_other_base_tools():
    tools = build_base_tools(enable_shell=False)
    names = {t.name for t in tools}
    assert {"read_file", "write_file", "edit_file", "install_package", "create_tool", "list_files"} <= names


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "True", "TRUE", "  yes  "])
def test_enable_shell_tool_parses_truthy_values(value, monkeypatch):
    monkeypatch.setenv("ENABLE_SHELL_TOOL", value)
    import importlib
    from py_mono import config as config_module
    importlib.reload(config_module)
    assert config_module.ENABLE_SHELL_TOOL is True


def test_enable_shell_tool_defaults_false(monkeypatch):
    monkeypatch.delenv("ENABLE_SHELL_TOOL", raising=False)
    import importlib
    from py_mono import config as config_module
    importlib.reload(config_module)
    assert config_module.ENABLE_SHELL_TOOL is False


def test_timeout_is_passed_to_subprocess_run():
    with patch.object(shell_module.subprocess, "run") as mock_run:
        mock_run.return_value = MagicMock(stdout="ok", stderr="", returncode=0)
        shell_module.run_shell("echo hi")

    _, kwargs = mock_run.call_args
    assert kwargs["timeout"] == shell_module.DEFAULT_SHELL_TIMEOUT_SECONDS


def test_timeout_expired_returns_tool_error():
    with patch.object(
        shell_module.subprocess, "run",
        side_effect=subprocess.TimeoutExpired(cmd="sleep 999", timeout=30),
    ):
        result = shell_module.run_shell("sleep 999")

    assert "timed out" in result.lower()


def test_forbidden_pattern_still_blocked_regression():
    # Regression test, not a security guarantee: confirms existing blocklist
    # behavior is unchanged by this fix, not that it constitutes real sandboxing.
    result = shell_module.run_shell("sudo rm -rf /")
    assert "[SECURITY] Command blocked" in result


def test_description_states_not_a_sandbox():
    assert "NOT a security boundary" in shell_module.shell_tool.description
    assert "does not sandbox command content" in shell_module.shell_tool.description
