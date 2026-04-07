# py_mono/agent/agent.py

from py_mono.llm.prompts import build_system_prompt
import json
import re
import uuid
from typing import Any, Dict, List, Optional
from py_mono.session.session_manager import SessionManager
from py_mono.llm.provider_registry import REGISTRY, get_provider
from py_mono.skill.base import SkillContext, SkillRegistry, SKILLS_DIR
from py_mono.config import WORKSPACE_ROOT
from py_mono.skill.approval import run_skill_safe, ApprovalError,wrap_agent_tools 


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
    - Route /skill and /approve special commands to skill registry
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
        self.skill_registry = skill_registry

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

    # -------------------------
    # Logging
    # -------------------------

    def _log(self, *args: Any) -> None:
        if self.debug:
            print(*args)

    def _print_memory(self) -> None:
        if self.debug:
            print("\n===== MEMORY =====")
            print(json.dumps(self.memory, indent=2))
            print("==================\n")

    # -------------------------
    # Special command routing
    # -------------------------

    def _is_special_command(self, text: str) -> bool:
        text = text.strip()
        if text in ("/clear", "/bye", "/providers"):
            return True
        if text.startswith("/provider "):
            return True
        if text == "/skill list":
            return True
        if text.startswith("/skill help "):
            return True
        if text.startswith("/skill "):
            return True
        if text.startswith("/approve "):
            return True
        return False

    def _handle_special_command(self, text: str) -> str:
        text = text.strip()

        # ------------------------------------------------------------------
        # Memory / session commands
        # ------------------------------------------------------------------
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
            parts = text.split(maxsplit=2)
            if len(parts) < 2:
                return "Usage: /provider <provider> [model]"

            provider_key = parts[1]
            model_hint = parts[2] if len(parts) == 3 else None

            if provider_key not in REGISTRY:
                available_names = ", ".join(sorted(REGISTRY.keys()))
                return (
                    f"Unknown provider '{provider_key}'. "
                    f"Available providers: {available_names}"
                )

            try:
                self.session_manager.switch_provider(provider_key, model=model_hint)
                current = self.session_manager.get_active_provider()
                model = getattr(current, "model_name", "<unknown>")
                if model_hint:
                    return (
                        f"Switched provider to {current.__class__.__name__} "
                        f"({provider_key}) using model '{model_hint}'.\n"
                        f"Underlying model: {model}"
                    )
                return (
                    f"Switched provider to {current.__class__.__name__} ({provider_key})."
                )
            except Exception as e:
                return f"Could not switch provider: {e}"

        # ------------------------------------------------------------------
        # Skill commands
        # ------------------------------------------------------------------
        if text == "/skill list":
            return self._handle_skill_list()

        if text.startswith("/skill help "):
            skill_name = text[len("/skill help "):].strip()
            return self._handle_skill_help(skill_name)

        if text.startswith("/skill "):
            return self._handle_skill_run(text)

        # ------------------------------------------------------------------
        # Approve command
        # ------------------------------------------------------------------
        if text.startswith("/approve "):
            skill_name = text[len("/approve "):].strip()
            return self._handle_skill_approve(skill_name)

        return ""

    # -------------------------
    # Skill handlers
    # -------------------------

    def _handle_skill_list(self) -> str:
        """Return a formatted list of all available skills."""
        if self.skill_registry is None:
            return "[SKILL] No skill registry configured."

        skills = self.skill_registry.list_skills()
        if not skills:
            return "[SKILL] No skills found. Add skills under the skills/ directory."

        lines = ["Available skills:\n"]
        for s in skills:
            name = s["name"]
            desc = s["description"]
            status = s["status"]
            has_code = s["has_code"]

            icon = "✅" if status == "approved" else "🔒"
            code_note = "" if has_code else " (spec only)"

            lines.append(f"{icon} {name}")
            lines.append(f"   {desc}{code_note}")
            lines.append(f"   Status: {status}")

            if status == "approved":
                lines.append(f"   Use: /skill {name}")
            else:
                lines.append(f"   Approve with: /approve {name}")

            lines.append("")

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
        Execute a skill safely.
        - Checks approval status
        - Uses run_skill_safe
        - Ensures forbidden patterns are respected
        """
        if self.skill_registry is None:
            return "[SKILL] No skill registry configured."

        parts = text.strip().split(maxsplit=2)
        if len(parts) < 2:
            return "Usage: /skill <name> [args]"

        skill_name = parts[1]
        skill = self.skill_registry.get(skill_name)
        print("DEBUG requested:", skill_name)
        print("DEBUG available:", list(self.skill_registry._skills.keys()))


        if skill is None:
            available = [s["name"] for s in self.skill_registry.list_skills()]
            return (
                f"[SKILL] Unknown skill '{skill_name}'. "
                f"Available: {', '.join(available) or 'none'}\n"
                f"Use /skill list to see all skills."
            )

        # Approval enforcement
        if not self.skill_registry.is_approved(skill_name):
            return (
                f"[SKILL] Skill '{skill_name}' is not approved for execution.\n"
                f"Status: proposed. Run: /approve {skill_name}"
            )

        # Build skill context
        context = SkillContext(
            workspace_root=WORKSPACE_ROOT,
            session_manager=self.session_manager,
            #agent_tools=self.tools,  # will not call .func() directly
            agent_tools=wrap_agent_tools(self.tools), 
        )

        try:
            # Safe execution: run_skill_safe enforces approval & forbidden patterns
            result = run_skill_safe(
                registry=self.skill_registry,
                skill_name=skill_name,
                request=text,
                context=context,
                parent_skill=getattr(context, "calling_skill", None),
            )
            return result

        except ApprovalError as ae:
            return f"[SKILL BLOCKED] {str(ae)}"
        except Exception as e:
            return f"[SKILL ERROR] {skill_name} failed: {str(e)}"
    
    def _handle_skill_approve(self, skill_name: str) -> str:
        """
        Approve a skill by setting status: approved in its SKILL.md.
        Reloads the registry so the skill is immediately executable.
        """
        if self.skill_registry is None:
            return "[SKILL] No skill registry configured."

        # Check skill exists
        skill_md_content = self.skill_registry.get_skill_md(skill_name)
        if skill_md_content is None:
            available = [s["name"] for s in self.skill_registry.list_skills()]
            return (
                f"[APPROVE] No skill named '{skill_name}' found.\n"
                f"Available: {', '.join(available) or 'none'}"
            )

        # Already approved?
        if self.skill_registry.is_approved(skill_name):
            return f"[APPROVE] Skill '{skill_name}' is already approved."

        # Update status in SKILL.md
        updated = re.sub(
            r"status:\s*\S+",
            "status: approved",
            skill_md_content,
            count=1,
        )

        if updated == skill_md_content:
            return (
                f"[APPROVE] Could not find 'status:' field in "
                f"skills/{skill_name}/SKILL.md to update."
            )

        # Write back
        try:
            skill_md_path = SKILLS_DIR / skill_name / "SKILL.md"
            skill_md_path.write_text(updated, encoding="utf-8")
        except Exception as e:
            return f"[APPROVE] Failed to update SKILL.md: {e}"

        # 🔥 Reload only this skill
        try:
            reloaded = self.skill_registry.reload_skill(skill_name)
            if not reloaded:
                return (
                    f"✅ Skill '{skill_name}' approved in SKILL.md.\n"
                    f"⚠️ Failed to reload skill — skill will be available after agent restart."
                )
        except Exception as e:
            return (
                f"✅ Skill '{skill_name}' approved in SKILL.md.\n"
                f"⚠️ Exception during reload: {e} — restart agent to apply."
            )


        return (
            f"✅ Skill '{skill_name}' approved and ready.\n"
            f"Run it with: /skill {skill_name}"
        )

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
        Special commands are handled before the LLM loop.
        """
        user_input_stripped = user_input.strip()

        if self._is_special_command(user_input_stripped):
            reply = self._handle_special_command(user_input_stripped)
            if user_input_stripped == "/bye":
                return reply
            self.memory.append({"role": "assistant", "content": reply})
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
                args = tool_call.get("args") or {}

                tool_call_id = str(uuid.uuid4())

                # Loop detection
                current_call = (tool_name, json.dumps(args, sort_keys=True))
                if current_call == self.last_tool_call:
                    self.repeat_count += 1
                else:
                    self.repeat_count = 0
                self.last_tool_call = current_call

                if self.repeat_count >= 1:
                    self._log("⚠️ Repeated tool call detected, nudging LLM")
                    self.memory.append(
                        {
                            "role": "user",
                            "content": "[AGENT] You already called this tool with the same arguments. Use the result to answer the user.",
                        }
                    )
                    continue

                # Record assistant tool call in canonical OpenAI-style format (ADR-005)
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
                                    "arguments": args or {},
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
                        result = tool.run(**args)
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
                return text

            # -------------------------
            # Fallback
            # -------------------------
            self._log("⚠️ Empty response, stopping")
            break

        return "[ERROR] Agent reached max steps"