# py_mono/agent/agent.py

from py_mono.llm.prompts import build_system_prompt
import json
import uuid
from typing import Any, Dict, List, Optional
from py_mono.session.session_manager import SessionManager
from py_mono.llm.provider_registry import REGISTRY, get_provider
#from py_mono.utils.special_commands import is_special_command,handle_special_command
from py_mono.skill.base import SkillContext, SkillRegistry
from py_mono.config import WORKSPACE_ROOT

class Agent:
    """
    Minimal agent loop (pi-mono style) with memory management and provider-agnostic
    canonical message format (OpenAI-style, per ADR-005).

    Responsibilities:
    - Maintain conversation memory in canonical format
    - Let LLM decide when to call tools
    - Execute tools
    - Feed results back into loop
    - Return final answer when LLM stops calling tools
    - Support memory clearing, pruning, auto-pruning, session termination
    """

    def __init__(
        self,
        session_manager: SessionManager,
        tools: List[Any],
        skill_registry: Optional[SkillRegistry] = None,
        max_steps: int = 10,
        debug: bool = True,
        auto_prune_after: int = 5,
        prune_keep_last: int = 20,
    ):
        self.session_manager = session_manager
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
        self.debug = debug
        self.auto_prune_after = auto_prune_after
        self.prune_keep_last = prune_keep_last

        # Initialize memory with system prompt only
        self.memory = [
            {
                "role": "system",
                "content": build_system_prompt(),
            }
        ]

        # Loop guards
        self.last_tool_call: Optional[tuple] = None
        self.repeat_count = 0
        self.tool_call_count = 0
        self.skill_registry = skill_registry

    def _log(self, *args: Any) -> None:
        if self.debug:
            print(*args)

    def _print_memory(self) -> None:
        if self.debug:
            print("\n===== MEMORY =====")
            print(json.dumps(self.memory, indent=2))
            print("==================\n")


    def _is_special_command(self, text: str) -> bool:
        text = text.strip()
        if text == "/clear":
            return True
        if text == "/bye":
            return True
        if text == "/providers":
            return True
        if text.startswith("/provider "):
            return True

        if text == "/skill list":
            return True
        if text.startswith("/skill help "):
            return True
        if text.startswith("/skill "):
            return True

        return False

    def _handle_skill_list(self) -> str:
        """Return a formatted list of all available skills."""
        if self.skill_registry is None:
            return "[SKILL] No skill registry configured."
    
        skills = self.skill_registry.list_skills()
        if not skills:
            return "[SKILL] No skills found. Add skills under the skills/ directory."
    
        lines = ["Available skills:\n"]
        for s in skills:
            code_marker = "✅" if s["has_code"] else "📋"
            status_marker = "🔒 proposed" if s["status"] == "proposed" else "✅ approved"
            lines.append(
                f"  {code_marker} {s['name']:30s} {s['description'][:60]}  [{status_marker}]"
            )
        return "\n".join(lines)
    
    
    def _handle_skill_help(self, skill_name: str) -> str:
        """Return the SKILL.md content for a named skill."""
        if self.skill_registry is None:
            return "[SKILL] No skill registry configured."
    
        content = self.skill_registry.get_skill_md(skill_name)
        if content is None:
            return f"[SKILL] No skill named '{skill_name}' found."
        return f"--- SKILL.md: {skill_name} ---\n{content}"
    
    
    def _handle_skill_run(self, text: str) -> str:
        """
        Route /skill <name> [args] to the matching skill.
        Enforces approval check before execution.
        """
        if self.skill_registry is None:
            return "[SKILL] No skill registry configured."
    
        parts = text.strip().split(maxsplit=2)
        if len(parts) < 2:
            return "Usage: /skill <name> [args]"
    
        skill_name = parts[1]
        skill = self.skill_registry.get(skill_name)
    
        if skill is None:
            available = [s["name"] for s in self.skill_registry.list_skills()]
            return (
                f"[SKILL] Unknown skill '{skill_name}'. "
                f"Available: {', '.join(available) or 'none'}\n"
                f"Use /skill list to see all skills."
            )
    
        # Approval check (ADR-010 review model)
        if not self.skill_registry.is_approved(skill_name):
            return (
                f"[SKILL] Skill '{skill_name}' is not approved for execution.\n"
                f"Status: proposed. To approve, set 'status: approved' in "
                f"skills/{skill_name}/SKILL.md."
            )
    
        # Build context and run
        context = SkillContext(
            workspace_root=WORKSPACE_ROOT,
            session_manager=self.session_manager,
            agent_tools=self.tools,
        )
    
        try:
            result = skill.run(request=text, context=context)
            return result
        except Exception as e:
            return f"[SKILL ERROR] {skill_name} failed: {str(e)}"
 

    def _handle_special_command(self, text: str) -> str:
        text = text.strip()

        if text == "/clear":
            self.clear_memory()
            return "Cleared conversation history (system prompt preserved)."

        if text == "/bye":
            return "Bye!"

        if text == "/providers":
            active = self.session_manager.get_active_provider()
            available = ", ".join(sorted(REGISTRY.keys()))
            model = getattr(active, "model_name", "<unknown>")
            return (
                f"Active provider: {active.__class__.__name__}\n"
                f"Active model: {model}\n"
                f"Available providers: {available}"
            )

        if text.startswith("/provider "):
            parts = text.split(maxsplit=2)  # /provider ollama granite4:350m
            if len(parts) < 2:
                return "Usage: /provider <provider> [model]"

            provider_key = parts[1]
            model_hint = parts[2] if len(parts) == 3 else None

            if provider_key not in REGISTRY:
                available_names = ", ".join(sorted(REGISTRY.keys()))
                return f"Unknown provider '{provider_key}'. Available providers: {available_names}"

            try:
                self.session_manager.switch_provider(provider_key, model=model_hint)
                current = self.session_manager.get_active_provider()
                model = getattr(current, "model_name", "<unknown>")
                if model_hint:
                    return (
                        f"Switched provider to {current.__class__.__name__} ({provider_key}) "
                        f"using model '{model_hint}'.\n"
                        f"Underlying model: {model}"
                    )
                return f"Switched provider to {current.__class__.__name__} ({provider_key})."
            except Exception as e:
                return f"Could not switch provider: {e}"
        if text == "/skill list":
            return self._handle_skill_list()
    
        if text.startswith("/skill help "):
            skill_name = text[len("/skill help "):].strip()
            return self._handle_skill_help(skill_name)
    
        if text.startswith("/skill "):
            return self._handle_skill_run(text)
    
        return ""



    # -------------------------
    # Memory / Session Methods
    # -------------------------

    def clear_memory(self) -> str:
        """
        Clear all conversation history except the core system prompt.
        Reset all loop guards.
        """
        self.memory = [
            {
                "role": "system",
                "content": build_system_prompt(),
            }
        ]
        self.last_tool_call = None
        self.repeat_count = 0
        self.tool_call_count = 0
        self._log("🗑️ Memory fully cleared. Ready for a fresh session.")
        return "✅ Memory cleared. You can start fresh."

    def prune_memory(self) -> None:
        """
        Compact memory by keeping only the last N messages (excluding system prompt).
        """
        system_msgs = [msg for msg in self.memory if msg["role"] == "system"]
        other_msgs = [msg for msg in self.memory if msg["role"] != "system"]
        self.memory = system_msgs + other_msgs[-self.prune_keep_last:]
        self._log(f"🧹 Memory pruned to last {self.prune_keep_last} messages.")

    # -------------------------
    # Main agent loop
    # -------------------------

    def run(self, user_input: str) -> str:
        """
        Run the agent for a single user query.
        """
        # Handle session commands
        # Handle special commands BEFORE appending to memory
        user_input_stripped = user_input.strip()  
        if self._is_special_command(user_input_stripped):
            reply = self._handle_special_command(user_input_stripped)
            if user_input == "/bye":
                return reply
            self.memory.append(
                {"role": "assistant", "content": reply}
            )
            return reply
                    

        # Add user message
        self.memory.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        for step in range(self.max_steps):
            self._log(f"\n--- STEP {step} ---")
            self._print_memory()

            llm = self.session_manager.get_active_provider()

            response = llm.generate(
                messages=self.memory,
                tools=list(self.tools.values()),
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
                args = tool_call.get("args") or {}  # guard against None

                # Generate unique tool_call_id for canonical format (ADR-005)
                tool_call_id = str(uuid.uuid4())

                # Loop detection
                current_call = (tool_name, json.dumps(args, sort_keys=True))
                if current_call == self.last_tool_call:
                    self.repeat_count += 1
                else:
                    self.repeat_count = 0
                self.last_tool_call = current_call

                # Guard against repeated identical calls
                if self.repeat_count >= 1:
                    self._log("⚠️ Repeated tool call detected, nudging LLM")
                    # Use role "user" not "system" to avoid polluting the system prompt slot
                    self.memory.append(
                        {
                            "role": "user",
                            "content": "[AGENT] You already called this tool with the same arguments. Use the result to answer the user.",
                        }
                    )
                    continue

                # Record assistant tool call in canonical OpenAI-style format (ADR-005)
                # Note: "arguments" is a dict, not a JSON string.
                self.memory.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": args or {},  # dict, not json.dumps
                                },
                            }
                        ],
                    }
                )

                # Execute the tool
                tool = self.tools.get(tool_name)
                if not tool:
                    result = f"[TOOL ERROR] Unknown tool: {tool_name}"
                else:
                    try:
                        result = tool.func(**args)
                    except Exception as e:
                        result = f"[TOOL ERROR] {str(e)}"

                self._log(f"TOOL [{tool_name}] RESULT:", result)

                # Record tool result in canonical format (ADR-005)
                self.memory.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": str(result),
                    }
                )

                # Auto-prune memory if needed
                if self.tool_call_count % self.auto_prune_after == 0:
                    self.prune_memory()

                continue

            # -------------------------
            # Final answer
            # -------------------------
            if text:
                self.memory.append(
                    {
                        "role": "assistant",
                        "content": text,
                    }
                )
                self._log("\n✅ FINAL ANSWER:")
                #self._log(text)
                return text

            # -------------------------
            # Fallback
            # -------------------------
            self._log("⚠️ Empty response, stopping")
            break

        return "[ERROR] Agent reached max steps"


