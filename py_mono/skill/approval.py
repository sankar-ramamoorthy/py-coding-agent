# py_mono/skill/approval.py

import time
from collections.abc import Mapping
from typing import Optional, Dict

from py_mono.skill.base import SkillRegistry, SkillContext, Skill
from py_mono.skill.telemetry import log_skill_run
from py_mono.skill.fitness import check_model_fitness


class ApprovalError(Exception):
    """Raised when an unapproved skill is attempted to run."""
    pass


class SafeToolWrapper:
    """
    Wrap a Tool object to forbid direct .func() access.

    Skills must call tools via tool.run(**kwargs).
    """

    def __init__(self, tool: "Tool"):
        self._tool = tool

    def __getattr__(self, name):
        if name == "func":
            raise RuntimeError(
                "Direct tool.func() usage is forbidden - use tool.run(**kwargs)"
            )
        return getattr(self._tool, name)


class SafeAgentTools(Mapping):
    """
    Read-only tool mapping that enforces per-skill allowed_tools policy.

    A skill is only blocked when it actually tries to access a disallowed tool.
    Merely having other tools loaded in the agent must not block execution.
    """

    def __init__(
        self,
        agent_tools: Dict[str, "Tool"],
        allowed_tools: set[str],
        skill_name: str,
    ):
        self._tools = {
            name: SafeToolWrapper(tool) for name, tool in agent_tools.items()
        }
        self._allowed_tools = allowed_tools
        self._skill_name = skill_name

    def _ensure_allowed(self, tool_name: str) -> None:
        if tool_name not in self._allowed_tools:
            raise ApprovalError(
                f"Skill '{self._skill_name}' is not allowed to use the tool '{tool_name}'"
            )

    def __getitem__(self, tool_name: str):
        self._ensure_allowed(tool_name)
        return self._tools[tool_name]

    def get(self, tool_name: str, default=None):
        if tool_name not in self._tools:
            return default
        self._ensure_allowed(tool_name)
        return self._tools[tool_name]

    def __iter__(self):
        return iter(self._tools)

    def __len__(self) -> int:
        return len(self._tools)


def wrap_agent_tools(
    agent_tools: Dict[str, "Tool"],
    allowed_tools: set[str],
    skill_name: str,
) -> Mapping[str, "Tool"]:
    """
    Wrap agent tools to enforce both forbidden direct access and allowed_tools.
    """

    return SafeAgentTools(agent_tools, allowed_tools, skill_name)


def run_skill_safe(
    registry: SkillRegistry,
    skill_name: str,
    request: str,
    context: SkillContext,
    parent_skill: Optional[str] = None,
) -> str:
    """
    Run a skill safely with approval enforcement and forbidden pattern checks.

    Args:
        registry: SkillRegistry instance
        skill_name: name of the skill to run
        request: full user request string
        context: SkillContext
        parent_skill: name of calling skill (if any)

    Raises:
        ApprovalError: if the skill is not approved or disallowed
        RuntimeError: if forbidden patterns are used
    """

    skill_name = registry._norm(skill_name)
    if parent_skill:
        parent_skill = registry._norm(parent_skill)

    skill = registry.get(skill_name)
    if not skill:
        raise ApprovalError(f"Skill '{skill_name}' not found.")

    meta = registry._metadata.get(skill_name, {})
    status = meta.get("status", "proposed").lower()
    trusted = meta.get("trusted", False)

    if status != "approved" and not trusted:
        raise ApprovalError(f"Skill '{skill_name}' is not approved for execution.")

    if parent_skill and status != "approved":
        raise ApprovalError(
            f"Skill '{skill_name}' cannot be called from '{parent_skill}' "
            "because it is not approved."
        )

    if skill_name == "approval" and parent_skill:
        raise ApprovalError("Approval skill cannot be called from another skill.")

    allowed_tools = set(meta.get("allowed_tools", list(context.agent_tools.keys())))

    safe_context = SkillContext(
        workspace_root=context.workspace_root,
        agent_tools=wrap_agent_tools(context.agent_tools, allowed_tools, skill_name),
        session_manager=context.session_manager,
    )
    safe_context.calling_skill = skill_name

    provider_name = "<unknown>"
    model_name = "<unknown>"
    if context.session_manager is not None:
        try:
            active = context.session_manager.get_active_provider()
            provider_name = active.__class__.__name__
            model_name = getattr(active, "model_name", "<unknown>")
        except Exception:
            pass

    fitness_warning = check_model_fitness(skill_name, provider_name, model_name)

    start = time.monotonic()
    success = False
    failure_reason = ""
    try:
        result = skill.run(request, safe_context)
        success = True
        if fitness_warning:
            return f"{fitness_warning}\n\n{result}"
        return result
    except Exception as e:
        failure_reason = str(e)
        raise RuntimeError(
            f"Skill '{skill_name}' execution failed: {str(e)}"
        ) from e
    finally:
        duration_ms = (time.monotonic() - start) * 1000
        log_skill_run(
            skill_name,
            provider_name,
            model_name,
            duration_ms,
            success,
            request=request,
            failure_reason=failure_reason,
        )
