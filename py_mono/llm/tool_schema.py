# py_mono/llm/tool_schema.py

def tool_to_schema(tool) -> dict:
    """Convert a Tool object to Ollama-compatible JSON schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters  # you'll need to add this to Tool
        }
    }

def build_tool_schemas(tools: list) -> list:
    return [tool_to_schema(t) for t in tools]
