"""Tests for SessionManager's handling of the new dual Ollama backend names."""

from unittest.mock import patch

from py_mono.session.session_manager import SessionManager


def test_construction_with_ollama_remote_resolves_correct_backend(monkeypatch):
    monkeypatch.delenv("OLLAMA_REMOTE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_REMOTE_MODEL", raising=False)
    session = SessionManager(default_provider="ollama-remote")
    assert session.provider_name == "ollama-remote"
    assert session.provider.base_url == "http://100.105.24.12:11434"
    assert session.provider.model_name == "qwen3.5:4b"


def test_construction_with_ollama_local_resolves_correct_backend(monkeypatch):
    monkeypatch.delenv("OLLAMA_LOCAL_URL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCAL_MODEL", raising=False)
    session = SessionManager(default_provider="ollama-local")
    assert session.provider_name == "ollama-local"
    assert session.provider.base_url == "http://host.docker.internal:11434"
    assert session.provider.model_name == "Qwen3:4b"


def test_switch_provider_updates_backend_and_model():
    session = SessionManager(default_provider="ollama-remote")
    session.switch_provider("ollama-local", model="qwen2.5:latest")
    assert session.provider_name == "ollama-local"
    assert session.provider.base_url == "http://host.docker.internal:11434"
    assert session.provider.model_name == "qwen2.5:latest"


def test_switch_provider_model_override_does_not_persist():
    session = SessionManager(default_provider="ollama-remote", model="qwen3:4b")
    assert session.provider.model_name == "qwen3:4b"
    # switching back to ollama-remote with no explicit model reverts to its own default
    session.switch_provider("ollama-remote")
    assert session.provider.model_name == "qwen3.5:4b"


def test_construction_with_ollama_auto_probes_once(monkeypatch):
    monkeypatch.delenv("OLLAMA_REMOTE_URL", raising=False)
    with patch("py_mono.llm.provider_registry.is_ollama_reachable", return_value=False):
        session = SessionManager(default_provider="ollama-auto")
        assert session.provider.base_url == "http://host.docker.internal:11434"
