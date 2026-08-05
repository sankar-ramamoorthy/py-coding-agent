"""Tests for OllamaProvider's base_url parameterization (dual-backend support), and for the
thinking-model empty-response fix (specs/005-fix-ollama-thinking-response/)."""

import logging
from unittest.mock import patch, MagicMock

import py_mono.config as config
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


# --- specs/005-fix-ollama-thinking-response: thinking-model empty-response fix ---


def _mock_response(payload: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = payload
    return mock_response


def test_generate_sends_num_predict_and_num_ctx():
    """US1: every request must carry an explicit response budget, not rely on server defaults."""
    provider = OllamaProvider(model_name="some-model", base_url="http://custom:11434")
    mock_response = _mock_response({"message": {"content": "hi", "tool_calls": None}})

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response) as mock_post:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        payload = mock_post.call_args.kwargs["json"]
        assert payload["options"]["num_predict"] == config.OLLAMA_NUM_PREDICT
        assert payload["options"]["num_ctx"] == config.OLLAMA_NUM_CTX


def test_generate_unaffected_for_non_thinking_model_payload():
    """US1/FR-002: the payload shape must not branch on model name — same options for all models."""
    provider = OllamaProvider(model_name="granite4:350m", base_url="http://custom:11434")
    mock_response = _mock_response({"message": {"content": "hi", "tool_calls": None}})

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response) as mock_post:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        payload = mock_post.call_args.kwargs["json"]
        assert payload["options"]["num_predict"] == config.OLLAMA_NUM_PREDICT
        assert payload["options"]["num_ctx"] == config.OLLAMA_NUM_CTX
        assert payload["model"] == "granite4:350m"


def test_generate_logs_thinking_field_when_present(caplog):
    """US2/FR-005: a populated `thinking` field must be visible in debug output when present."""
    provider = OllamaProvider(model_name="qwen3.5:4b", base_url="http://custom:11434")
    mock_response = _mock_response({
        "message": {"content": "", "thinking": "reasoning about the request", "tool_calls": None},
        "done_reason": "length",
    })

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response), \
         patch("builtins.print") as mock_print:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "reasoning about the request" in printed


def test_generate_no_error_when_thinking_field_absent():
    """US2: a response with no `thinking` key (non-thinking model shape) must not raise."""
    provider = OllamaProvider(model_name="granite4:350m", base_url="http://custom:11434")
    mock_response = _mock_response({"message": {"content": "hi", "tool_calls": None}})

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response):
        result = provider.generate(messages=[{"role": "user", "content": "hello"}])
        assert result["text"] == "hi"


def test_generate_sends_think_false_by_default():
    """US3/FR-001: default behavior disables thinking — confirmed to eliminate reasoning
    token cost entirely for models with native Ollama thinking support (e.g. qwen3.5:4b),
    and confirmed harmless/ignored on non-thinking models. See research.md."""
    provider = OllamaProvider(model_name="qwen3.5:4b", base_url="http://custom:11434")
    mock_response = _mock_response({"message": {"content": "hi", "tool_calls": None}})

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response) as mock_post:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        payload = mock_post.call_args.kwargs["json"]
        assert payload["think"] is False


def test_generate_omits_think_when_thinking_explicitly_enabled(monkeypatch):
    """US3: OLLAMA_ENABLE_THINKING=true must not unconditionally suppress reasoning — the
    num_predict/num_ctx safety net (T004) is what protects this path instead."""
    monkeypatch.setattr("py_mono.llm.ollama_provider.OLLAMA_ENABLE_THINKING", True)
    provider = OllamaProvider(model_name="qwen3.5:4b", base_url="http://custom:11434")
    mock_response = _mock_response({"message": {"content": "hi", "tool_calls": None}})

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response) as mock_post:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        payload = mock_post.call_args.kwargs["json"]
        assert "think" not in payload
        # Safety net must still be present even when thinking is explicitly enabled.
        assert payload["options"]["num_predict"] == config.OLLAMA_NUM_PREDICT


def test_generate_uses_configured_request_timeout():
    """A thinking-capable model that ignores OLLAMA_ENABLE_THINKING=false can take several
    minutes to exhaust its budget — the old hardcoded 300s timeout raised ReadTimeout instead
    of a clean empty-response result. See research.md."""
    provider = OllamaProvider(model_name="some-model", base_url="http://custom:11434")
    mock_response = _mock_response({"message": {"content": "hi", "tool_calls": None}})

    with patch("py_mono.llm.ollama_provider.requests.post", return_value=mock_response) as mock_post:
        provider.generate(messages=[{"role": "user", "content": "hello"}])
        assert mock_post.call_args.kwargs["timeout"] == config.OLLAMA_REQUEST_TIMEOUT
