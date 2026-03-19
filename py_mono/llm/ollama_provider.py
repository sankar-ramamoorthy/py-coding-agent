# py_mono/llm/ollama_provider.py
import os
import requests
import json
from py_mono.llm.tool_schema import build_tool_schemas

DEBUG = True  # Set to False to silence debug logs

class OllamaProvider:
    """
    Ollama REST provider with debug logs and safe JSON extraction.
    """
    def __init__(self, model=None):
        self.model = model or os.getenv("OLLAMA_MODEL", "Qwen3:4b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

    def generate(self, messages, tools=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if tools:
            payload["tools"] = build_tool_schemas(tools)

        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=300)
        data = resp.json()
        message = data.get("message", {})

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
        return {"text": message.get("content", ""), "tool_call": None}
        

    def generate_old(self, messages, tools=None):
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        if DEBUG:
            print(f"[DEBUG] Sending prompt to Ollama:\n{prompt}\n")

        payload = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=300)
            resp.raise_for_status()
            text = resp.text.strip()
            if DEBUG:
                print(f"[DEBUG] Raw response from Ollama:\n{text}\n")

            # Attempt to extract JSON
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_text = text[start:end+1]
                data = json.loads(json_text)
                if DEBUG:
                    print(f"[DEBUG] Parsed JSON:\n{data}\n")
                return {
                    "text": data.get("text", ""),
                    "tool_call": data.get("tool_call", None)
                }

            # If no JSON, return raw text
            return {"text": text, "tool_call": None}

        except (requests.RequestException, json.JSONDecodeError) as e:
            if DEBUG:
                print(f"[DEBUG] Error during LLM call: {e}")
            return {"text": f"[LLM ERROR] {e}", "tool_call": None}