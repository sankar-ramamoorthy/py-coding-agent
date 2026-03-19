# py_mono/agent/agent.py

from py_mono.llm.prompts import build_system_prompt


class Agent:
    """
    Core agent loop that interacts with an LLM and executes tools.

    Responsibilities:
    - Maintain conversation memory
    - Send messages to LLM
    - Detect tool calls
    - Execute tools
    - Feed tool results back to the LLM
    """

    def __init__(self, llm, tools, max_steps=10):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps

        # Initialize conversation memory with system prompt
        self.memory = [{
            "role": "system",
            "content": build_system_prompt()
        }]

    def run(self, user_input: str):
        """Run the agent for a single user query."""

        self.memory.append({
            "role": "user",
            "content": user_input
        })

        for step in range(self.max_steps):

            response = self.llm.generate(
                messages=self.memory,
                tools=list(self.tools.values())
            )

            tool_call = response.get("tool_call")

            # --- TOOL EXECUTION PATH ---
            if tool_call:
                tool_name = tool_call["name"]
                args = tool_call.get("args", {})

                tool = self.tools.get(tool_name)

                if not tool:
                    result = f"[TOOL ERROR] Unknown tool: {tool_name}"
                else:
                    try:
                        result = tool.func(**args)
                    except Exception as e:
                        result = f"[TOOL ERROR] {str(e)}"

                # Add tool result to conversation
                self.memory.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": str(result)
                })

                continue

            # --- NORMAL RESPONSE ---
            text = response.get("text")

            if text:
                self.memory.append({
                    "role": "assistant",
                    "content": text
                })
                print(f"[AGENT STEP {step}]")
                print(response)
                return text

        return "[ERROR] Agent reached max steps"
