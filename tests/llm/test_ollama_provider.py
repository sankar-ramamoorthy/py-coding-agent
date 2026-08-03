"""Tests for OllamaProvider's base_url parameterization (dual-backend support)."""

from unittest.mock import patch, MagicMock

from py_mono.llm.ollama_provider import OllamaProvider


def test_explicit_base_url_wins_over_env_var(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://env-url:11434")
    provider = OllamaProvider(model_name="some-model", base_url="http://explicit-url:11434")
    assert provider.base_url == "http://explicit-url:11434"


def test_omitted_base_url_falls_back_to_env_var(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://env-url:11434")
    provider = OllamaProvider(model_name="some-model")
    assert provider.base_url == "http://env-url:11434"


def test_omitted_base_url_and_env_var_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    provider = OllamaProvider(model_name="some-model")
    assert provider.base_url == "http://host.docker.internal:11434"


def test_generate_posts_to_explicit_base_url():
    provider = OllamaProvider(model_name="some-model", base_url="http://custom:11434")
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {"message": {"content": "hi", "tool_calls": None}}

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response) as mock_post:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        called_url = mock_post.call_args[0][0]
        assert called_url == "http://custom:11434/api/chat"
