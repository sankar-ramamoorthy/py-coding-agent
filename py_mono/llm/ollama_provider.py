# py_mono/llm/ollama_provider.py

import os
import requests
from py_mono.llm.base import LLMProvider
from py_mono.llm.tool_schema import build_tool_schemas
from typing import Optional

DEBUG = True  # Set to False to silence debug logs


class OllamaProvider(LLMProvider):
    """
    Ollama REST provider.

    Translates canonical OpenAI-style memory format (ADR-005) to Ollama wire format
    before sending, and normalizes Ollama responses back to the canonical dict.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name=model_name)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        # Use CLI‑provided model first, env as fallback
        self.model_name = model_name or os.getenv(
            "OLLAMA_MODEL", "lfm2.5-thinking:latest"
        )
    def to_wire_messages(self, messages: list) -> list:
        """
        Translate canonical OpenAI-style messages to Ollama wire format.

        Key differences vs canonical format:
        - assistant content must be "" not None
        - tool_calls list uses {"function": {"name", "arguments"}} with no "id" or "type"
        - tool result messages drop tool_call_id
        - nudge messages with role "user" pass through unchanged
        """
        wire = []
        for msg in messages:
            role = msg.get("role")

            if role == "assistant" and msg.get("tool_calls"):
                # Translate canonical tool_calls → Ollama tool_calls
                wire.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        }
                        for tc in msg["tool_calls"]
                    ]
                })

            elif role == "tool":
                # Ollama tool results drop tool_call_id
                wire.append({
                    "role": "tool",
                    "content": msg.get("content", "")
                })

            else:
                # system, user, assistant text — pass through as-is
                wire.append(msg)

        return wire

    def generate(self, messages: list, tools=None) -> dict:
        """
        Send messages to Ollama and return normalized response.

        Args:
            messages: Canonical OpenAI-style message list
            tools: List of Tool objects

        Returns:
            {"text": str | None, "tool_call": {"name": str, "args": dict} | None}
        """
        wire_messages = self.to_wire_messages(messages)

        payload = {
            "model": self.model_name,
            "messages": wire_messages,
            "stream": False
        }
        if tools:
            payload["tools"] = build_tool_schemas(tools)

        if DEBUG:
            import json
            print(f"[DEBUG] Sending to Ollama:\n{json.dumps(payload, indent=2)}\n")

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=300
        )
        if not resp.ok:
            # Log raw error from Ollama
            print(f"[DEBUG] Ollama HTTP {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        data = resp.json()

        if DEBUG:
            import json
            print(f"[DEBUG] Ollama response:\n{json.dumps(data, indent=2)}\n")

        message = data.get("message", {})

        # Tool call response
        tool_calls = message.get("tool_calls")
        if tool_calls:
            call = tool_calls[0]["function"]
            return {
                "text": None,
                "tool_call": {
                    "name": call["name"],
                    "args": call["arguments"]
                }
            }

        # Text response
        return {
            "text": message.get("content", ""),
            "tool_call": None
        }