# py_mono/agent/agent.py

from py_mono.llm.prompts import build_system_prompt
import json

class Agent:
    """
    Minimal agent loop (pi-mono style) with memory management.

    Responsibilities:
    - Maintain conversation memory
    - Let LLM decide when to call tools
    - Execute tools
    - Feed results back into loop
    - Return final answer when LLM stops calling tools
    - Support memory clearing, pruning, auto-pruning, and session termination
    """

    def __init__(self, llm, tools, max_steps=10, debug=True, auto_prune_after=5, prune_keep_last=20):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
        self.debug = debug
        self.auto_prune_after = auto_prune_after   # prune every N tool calls
        self.prune_keep_last = prune_keep_last

        # Initialize memory with system prompt only
        self.memory = [{
            "role": "system",
            "content": build_system_prompt()
        }]

        # Simple loop guard
        self.last_tool_call = None
        self.repeat_count = 0
        self.tool_call_count = 0

    def _log(self, *args):
        if self.debug:
            print(*args)

    def _print_memory(self):
        if self.debug:
            print("\n===== MEMORY =====")
            print(json.dumps(self.memory, indent=2))
            print("==================\n")

    # -------------------------
    # Memory / Session Methods
    # -------------------------
    def clear_memory(self):
        """Clear all conversation history except system prompt."""
        self.memory = [msg for msg in self.memory if msg["role"] == "system"]
        self._log("🗑️ Memory cleared.")

    def prune_memory(self):
        """Compact memory by keeping only the last N messages (excluding system prompt)."""
        system_msgs = [msg for msg in self.memory if msg["role"] == "system"]
        user_tool_msgs = [msg for msg in self.memory if msg["role"] != "system"]
        self.memory = system_msgs + user_tool_msgs[-self.prune_keep_last:]
        self._log(f"🧹 Memory pruned to last {self.prune_keep_last} messages.")

    # -------------------------
    # Main agent loop
    # -------------------------
    def run(self, user_input: str):
        """Run the agent for a single user query."""

        # Check for special session commands first
        if user_input.strip().lower() == "/clear":
            self.clear_memory()
            return "✅ Memory cleared. You can start fresh."

        if user_input.strip().lower() == "/bye":
            return "👋 Goodbye! Session ended."

        # Add user message to memory
        self.memory.append({
            "role": "user",
            "content": user_input
        })

        for step in range(self.max_steps):
            self._log(f"\n--- STEP {step} ---")
            self._print_memory()

            response = self.llm.generate(
                messages=self.memory,
                tools=list(self.tools.values())
            )

            self._log("LLM RESPONSE:", response)

            tool_call = response.get("tool_call")
            text = response.get("text")

            # -------------------------
            # Tool execution
            # -------------------------
            if tool_call:
                self.tool_call_count += 1
                tool_name = tool_call.get("name")
                args = tool_call.get("args", {})

                # Loop detection
                current_call = (tool_name, json.dumps(args, sort_keys=True))
                if current_call == self.last_tool_call:
                    self.repeat_count += 1
                else:
                    self.repeat_count = 0
                self.last_tool_call = current_call

                # Guard against infinite loops
                if self.repeat_count >= 1:
                    self._log("⚠️ Repeated tool call detected, nudging LLM")
                    self.memory.append({
                        "role": "system",
                        "content": "You already called this tool with the same arguments. Use the result to answer the user."
                    })
                    continue

                # Record assistant tool call
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

                # Record tool result
                self.memory.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": str(result)
                })

                # -------------------------
                # Auto-prune memory
                # -------------------------
                if self.tool_call_count % self.auto_prune_after == 0:
                    self.prune_memory()

                continue

            # -------------------------
            # Final answer
            # -------------------------
            if text:
                self.memory.append({
                    "role": "assistant",
                    "content": text
                })
                self._log("\n✅ FINAL ANSWER:")
                self._log(text)
                return text

            # -------------------------
            # Fallback
            # -------------------------
            self._log("⚠️ Empty response, stopping")
            break

        return "[ERROR] Agent reached max steps"