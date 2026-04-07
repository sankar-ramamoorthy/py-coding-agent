# py_mono\llm\tool_schema.py
from typing import TypedDict, Optional, Any, List

class FunctionSchema(TypedDict):
    name: str
    description: str
    parameters: dict
    returns: Optional[Any]

class ToolSchema(TypedDict):
    type: str
    function: FunctionSchema

def tool_to_schema(tool) -> ToolSchema:
    """Convert a Tool object to Ollama-compatible JSON schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "returns": getattr(tool, "returns", None),
        }
    }

def build_tool_schemas(tools: List[Any]) -> List[ToolSchema]:
    return [tool_to_schema(t) for t in tools]