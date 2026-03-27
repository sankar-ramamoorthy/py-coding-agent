# py_mono/llm/litellm_provider.py
"""
LiteLLM provider for py-coding-agent.

Supports any provider that LiteLLM supports, including:
- Groq:      groq/llama-3.3-70b-versatile
- OpenAI:    openai/gpt-4o
- Anthropic: anthropic/claude-3-5-haiku-20241022
- Together:  together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1


Environment variables:
    LITELLM_MODEL   — model string in litellm format (e.g. groq/llama-3.3-70b-versatile)
    GROQ_API_KEY    — if using Groq
    OPENAI_API_KEY  — if using OpenAI
    ANTHROPIC_API_KEY — if using Anthropic

See ADR-005 for canonical message format specification.
"""

import os
from py_mono.llm.base import LLMProvider
from py_mono.llm.tool_schema import build_tool_schemas
from typing import Any, Dict, List, Union, Optional

try:
    import litellm
    litellm.drop_params = True  # silently drop unsupported params per provider
except ImportError:
    raise ImportError(
        "litellm is not installed. "
        "Run: pip install py-coding-agent[litellm]"
    )


class LiteLLMProvider(LLMProvider):
    """
    LLM provider using LiteLLM to support multiple cloud providers
    through a single OpenAI-compatible interface.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name=model_name)
        # Use CLI‑provided model as primary; env as fallback
        self.model_name = model_name or os.getenv("LITELLM_MODEL", "groq/llama-3.3-70b-versatile")


    def to_wire_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        LiteLLM speaks OpenAI natively, but Groq wants arguments as JSON strings.
        Translate canonical tool_calls so that "arguments" is JSON‑encoded.
        """
        import json

        wire = []
        for msg in messages:
            role = msg.get("role")

            if role == "assistant" and msg.get("tool_calls"):
                transformed = {
                    "role": "assistant",
                    "content": msg.get("content"),
                    "tool_calls": [],
                }
                for tc in msg["tool_calls"]:
                    func = tc["function"]
                    args = func["arguments"]
                    # If it's a dict, serialize it; otherwise leave it
                    if isinstance(args, dict):
                        args = json.dumps(args, separators=(",", ":"))
                    transformed["tool_calls"].append({
                        "id": tc.get("id"),
                        "type": tc.get("type", "function"),
                        "function": {
                            "name": func["name"],
                            "arguments": args,
                        },
                    })
                wire.append(transformed)

            elif role == "tool":
                # Pass tool result through as-is
                wire.append(msg)

            else:
                # system, user, assistant text
                wire.append(msg)

        return wire


    def to_wire_messages1(self, messages: list) -> list:
        """
        LiteLLM speaks OpenAI natively so canonical format passes through as-is.

        Args:
            messages: Canonical OpenAI-style message list

        Returns:
            list: Same message list, unchanged
        """
        return messages

    def generate(self, messages: list, tools: list = None) -> dict:
        try:
            wire_messages = self.to_wire_messages(messages)
            kwargs = {
                "model": self.model_name,
                "messages": wire_messages,
            }
            if tools:
                kwargs["tools"] = build_tool_schemas(tools)
                kwargs["tool_choice"] = "auto"

            response = litellm.completion(**kwargs)
            message = response.choices[0].message

            if message.tool_calls:
                call = message.tool_calls[0]
                import json
                args = call.function.arguments
                if isinstance(args, str):
                    args = json.loads(args)
                return {
                    "text": None,
                    "tool_call": {
                        "name": call.function.name,
                        "args": args
                    }
                }

            return {
                "text": message.content or "",
                "tool_call": None
            }

        except Exception as e:
            return {
                "text": f"[LLM ERROR] {str(e)}",
                "tool_call": None
            }