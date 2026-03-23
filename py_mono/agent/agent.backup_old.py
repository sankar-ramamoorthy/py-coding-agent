# py_mono/agent/agent.py

from py_mono.llm.prompts import build_system_prompt, build_final_answer_prompt
import json


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

    def __init__(self, llm, tools, max_steps=10, debug=True):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
        self.debug = debug

        # Initialize conversation memory with system prompt
        self.memory = [{
            "role": "system",
            "content": build_system_prompt()
        }]

    def _log(self, *args):
        if self.debug:
            print(*args)

    def _print_memory(self):
        if self.debug:
            print("\n===== MEMORY =====")
            print(json.dumps(self.memory, indent=2))
            print("==================\n")

    def run(self, user_input: str):
        """Run the agent for a single user query."""

        # Add user message
        self.memory.append({
            "role": "user",
            "content": user_input
        })

        tool_called = False

        for step in range(self.max_steps):
            self._log(f"\n--- STEP {step} ---")
            self._print_memory()

            # Call LLM
            response = self.llm.generate(
                messages=self.memory,
                tools=list(self.tools.values())
            )

            self._log("LLM RESPONSE:", response)

            tool_call = response.get("tool_call")
            text = response.get("text")

            # =========================================================
            # 🔧 TOOL EXECUTION PATH
            # =========================================================
            if tool_call:
                tool_called = True
                tool_name = tool_call.get("name")
                args = tool_call.get("args", {})

                # Record assistant tool decision
                self.memory.append({
                    "role": "assistant",
                    "content": None,
                    "tool_call": tool_call
                })

                tool = self.tools.get(tool_name)

                if not tool:
                    result = f"[TOOL ERROR] Unknown tool: {tool_name}"
                else:
                    try:
                        result = tool.func(**args)
                    except Exception as e:
                        result = f"[TOOL ERROR] {str(e)}"

                self._log(f"TOOL [{tool_name}] RESULT:", result)

                # Record tool result in canonical format
                self.memory.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": f"TOOL RESULT:\n{str(result)}"
                })

                continue  # go to next loop step

            # =========================================================
            # 💬 FINAL RESPONSE PATH (if LLM returns text directly)
            # =========================================================
            if text:
                self.memory.append({
                    "role": "assistant",
                    "content": text
                })

                self._log("\n✅ FINAL ANSWER (direct text):")
                self._log(text)

                return text

            # =========================================================
            # ⚠️ FALLBACK (no tool_call, no text)
            # =========================================================
            self._log("⚠️ Empty response, forcing exit")
            break

        # =============================================================
        # 🏁 FINAL ANSWER USING TOOL RESULTS
        # =============================================================
        if tool_called:
            # Collect all tool results for this query
            tool_results_str = "\n".join(
                f"{msg['name']}: {msg['content'].strip()}"
                for msg in self.memory if msg["role"] == "tool"
            )

            # Build final answer prompt
            final_prompt = build_final_answer_prompt(user_input, tool_results_str)

            # Send to LLM as a single "user" message
            final_response = self.llm.generate(messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": final_prompt}
            ])

            answer_text = final_response.get("text")
            self.memory.append({"role": "assistant", "content": answer_text})

            self._log("\n✅ FINAL ANSWER (after tool execution):")
            self._log(answer_text)

            return answer_text

        return "[ERROR] Agent reached max steps"