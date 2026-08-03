"""Tests for the Ollama reachability probe used by the "ollama-auto" backend."""

from unittest.mock import patch, MagicMock

import requests

from py_mono.llm.ollama_connectivity import is_ollama_reachable


def test_reachable_returns_true_on_2xx():
    mock_response = MagicMock()
    mock_response.ok = True
    with patch("py_mono.llm.ollama_connectivity.requests.get", return_value=mock_response) as mock_get:
        assert is_ollama_reachable("http://somehost:11434") is True
        mock_get.assert_called_once_with("http://somehost:11434/api/tags", timeout=2.0)


def test_unreachable_returns_false_on_non_2xx():
    mock_response = MagicMock()
    mock_response.ok = False
    with patch("py_mono.llm.ollama_connectivity.requests.get", return_value=mock_response):
        assert is_ollama_reachable("http://somehost:11434") is False


def test_unreachable_returns_false_on_connection_error():
    with patch("py_mono.llm.ollama_connectivity.requests.get", side_effect=requests.exceptions.ConnectionError):
        assert is_ollama_reachable("http://somehost:11434") is False


def test_unreachable_returns_false_on_timeout():
    with patch("py_mono.llm.ollama_connectivity.requests.get", side_effect=requests.exceptions.Timeout):
        assert is_ollama_reachable("http://somehost:11434") is False


def test_custom_timeout_is_passed_through():
    mock_response = MagicMock()
    mock_response.ok = True
    with patch("py_mono.llm.ollama_connectivity.requests.get", return_value=mock_response) as mock_get:
        is_ollama_reachable("http://somehost:11434", timeout=5.0)
        mock_get.assert_called_once_with("http://somehost:11434/api/tags", timeout=5.0)
