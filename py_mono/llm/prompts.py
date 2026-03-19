# py_mono/llm/prompts.py

def build_system_prompt():
    return """
You are a Python coding agent running inside a Docker sandbox.

You have access to tools.

CRITICAL RULES:
- If the user request involves files, directories, or shell commands, you MUST call a tool.
- You are NOT allowed to answer from memory.
- You are NOT allowed to guess file contents or directory listings.
- You MUST use tools to get real data.

- Do NOT simulate outputs.
- Do NOT describe actions.
- Either:
  (1) Call a tool
  (2) Or give a final answer if no tool is needed

Failure to use tools when required is incorrect.
"""



def build_tool_description_block(tools: dict) -> str:
    lines = []
    for tool in tools.values():
        params = tool.parameters.get("properties", {})
        param_str = ", ".join(
            f"{k} ({v.get('type','any')}): {v.get('description','')}"
            for k, v in params.items()
        )
        lines.append(f"- {tool.name}({param_str}): {tool.description}")
    return "\n".join(lines)

def build_final_answer_prompt(user_message: str, tool_results: str) -> str:
    return f"""The user asked: {user_message}

Tool results:
{tool_results}

Using only the tool results above, give a direct, concise final answer.
Do not repeat the tool results verbatim. Do not describe your process."""