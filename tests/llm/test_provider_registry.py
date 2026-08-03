"""Tests for provider_registry.py's dual Ollama backend resolution."""

import pytest
from unittest.mock import patch

from py_mono.llm.provider_registry import get_provider, REGISTRY
from py_mono.llm.ollama_provider import OllamaProvider


def test_registry_lists_all_expected_names():
    assert set(REGISTRY.keys()) == {
        "ollama", "ollama-remote", "ollama-local", "ollama-auto", "litellm",
    }


def test_bare_ollama_unchanged(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://legacy-url:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "legacy-model")
    provider = get_provider("ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.base_url == "http://legacy-url:11434"
    assert provider.model_name == "legacy-model"


def test_bare_ollama_ignores_new_remote_local_env_vars(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.setenv("OLLAMA_REMOTE_URL", "http://should-not-be-used:11434")
    provider = get_provider("ollama")
    assert provider.base_url == "http://host.docker.internal:11434"


def test_ollama_remote_uses_env_defaults(monkeypatch):
    monkeypatch.delenv("OLLAMA_REMOTE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_REMOTE_MODEL", raising=False)
    provider = get_provider("ollama-remote")
    assert provider.base_url == "http://100.105.24.12:11434"
    assert provider.model_name == "qwen3.5:4b"


def test_ollama_remote_respects_env_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_REMOTE_URL", "http://custom-remote:11434")
    monkeypatch.setenv("OLLAMA_REMOTE_MODEL", "custom-model")
    provider = get_provider("ollama-remote")
    assert provider.base_url == "http://custom-remote:11434"
    assert provider.model_name == "custom-model"


def test_ollama_remote_explicit_model_overrides_env_default(monkeypatch):
    monkeypatch.setenv("OLLAMA_REMOTE_MODEL", "qwen3.5:4b")
    provider = get_provider("ollama-remote", model="qwen3:4b")
    assert provider.model_name == "qwen3:4b"


def test_ollama_local_uses_env_defaults(monkeypatch):
    monkeypatch.delenv("OLLAMA_LOCAL_URL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCAL_MODEL", raising=False)
    provider = get_provider("ollama-local")
    assert provider.base_url == "http://host.docker.internal:11434"
    assert provider.model_name == "Qwen3:4b"


def test_ollama_local_explicit_model_overrides_env_default():
    provider = get_provider("ollama-local", model="qwen2.5:latest")
    assert provider.model_name == "qwen2.5:latest"


def test_explicit_backends_never_probe_reachability():
    with patch("py_mono.llm.provider_registry.is_ollama_reachable") as mock_probe:
        get_provider("ollama-remote")
        get_provider("ollama-local")
        get_provider("ollama")
        mock_probe.assert_not_called()


def test_ollama_auto_resolves_to_remote_when_reachable(monkeypatch):
    with patch("py_mono.llm.provider_registry.is_ollama_reachable", return_value=True) as mock_probe:
        provider = get_provider("ollama-auto")
        assert provider.base_url == "http://100.105.24.12:11434"
        assert provider.model_name == "qwen3.5:4b"
        mock_probe.assert_called_once()


def test_ollama_auto_falls_back_to_local_when_remote_unreachable():
    with patch("py_mono.llm.provider_registry.is_ollama_reachable", return_value=False):
        provider = get_provider("ollama-auto")
        assert provider.base_url == "http://host.docker.internal:11434"
        assert provider.model_name == "Qwen3:4b"


def test_ollama_auto_probes_no_real_network():
    """Guard against accidentally hitting the real network in this test suite."""
    with patch("py_mono.llm.provider_registry.is_ollama_reachable") as mock_probe:
        mock_probe.return_value = False
        get_provider("ollama-auto")
        assert mock_probe.called


def test_unknown_provider_raises_value_error_listing_all_keys():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nonexistent-provider")
