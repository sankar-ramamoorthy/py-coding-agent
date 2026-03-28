# py_mono/llm/litellm_provider.py  (updated)

import os
from typing import Any, Dict, List, Optional

from py_mono.llm.base import LLMProvider
from py_mono.llm.tool_schema import build_tool_schemas


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
    through a single OpenAI‑compatible interface.
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)
        # Use CLI‑provided model as primary; env as fallback
        self.model_name = model_name or os.getenv("LITELLM_MODEL", "groq/llama-3.3-70b-versatile")
        # Use explicitly passed api_key first, then env
        self.api_key = api_key or self._get_env_key()

    def _get_env_key(self) -> Optional[str]:
        """Try to read API key from environment variables."""
        # Example logic; you can extend this
        for key in [
            "GROQ_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]:
            val = os.getenv(key)
            if val:
                return val
        return None

    def to_wire_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                    if isinstance(args, dict):
                        args = json.dumps(args, separators=(",", ":"))
                    transformed["tool_calls"].append(
                        {
                            "id": tc.get("id"),
                            "type": tc.get("type", "function"),
                            "function": {"name": func["name"], "arguments": args},
                        }
                    )
                wire.append(transformed)

            elif role == "tool":
                wire.append(msg)

            else:
                wire.append(msg)

        return wire

    def generate(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> dict:
        try:
            wire_messages = self.to_wire_messages(messages)
            kwargs = {
                "model": self.model_name,
                "messages": wire_messages,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key

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
                    "tool_call": {"name": call.function.name, "args": args},
                }

            return {
                "text": message.content or "",
                "tool_call": None,
            }

        except Exception as e:
            return {
                "text": f"[LLM ERROR] {str(e)}",
                "tool_call": None,
            }
