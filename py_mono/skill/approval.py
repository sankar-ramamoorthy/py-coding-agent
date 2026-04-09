# py_mono/skill/approval.py

from typing import Optional, Dict
from py_mono.skill.base import SkillRegistry, SkillContext, Skill


class ApprovalError(Exception):
    """Raised when an unapproved skill is attempted to run."""
    pass


class SafeToolWrapper:
    """
    Wraps a Tool object to forbid direct .func() access.
    Must call via tool.run({...}) instead.
    """

    def __init__(self, tool: 'Tool'):
        self._tool = tool

    def __getattr__(self, name):
        if name == "func":
            raise RuntimeError(
                "Direct tool.func() usage is forbidden — use tool.run({...})"
            )
        return getattr(self._tool, name)


def wrap_agent_tools(agent_tools: Dict[str, 'Tool']) -> Dict[str, 'Tool']:
    """
    Wrap all agent tools to enforce forbidden pattern rule.
    """
    return {name: SafeToolWrapper(tool) for name, tool in agent_tools.items()}


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

    # ------------------------------------------------------------------
    # Canonical normalization using registry
    # ------------------------------------------------------------------
    skill_name = registry._norm(skill_name)
    if parent_skill:
        parent_skill = registry._norm(parent_skill)

    skill = registry.get(skill_name)
    if not skill:
        raise ApprovalError(f"Skill '{skill_name}' not found.")

    # ------------------------------------------------------------------
    # Metadata lookup
    # ------------------------------------------------------------------
    meta = registry._metadata.get(skill_name, {})
    status = meta.get("status", "proposed").lower()
    trusted = meta.get("trusted", False)

    # ------------------------------------------------------------------
    # Approval enforcement
    # ------------------------------------------------------------------
    if status != "approved" and not trusted:
        raise ApprovalError(f"Skill '{skill_name}' is not approved for execution.")

    if parent_skill and status != "approved":
        raise ApprovalError(
            f"Skill '{skill_name}' cannot be called from '{parent_skill}' "
            "because it is not approved."
        )

    if skill_name == "approval" and parent_skill:
        raise ApprovalError("Approval skill cannot be called from another skill.")

    # ------------------------------------------------------------------
    # Safe context: wrap tools + track calling skill
    # ------------------------------------------------------------------
    safe_context = SkillContext(
        workspace_root=context.workspace_root,
        agent_tools=wrap_agent_tools(context.agent_tools),
        session_manager=context.session_manager,
    )
    safe_context.calling_skill = skill_name

    # ------------------------------------------------------------------
    # Enforce per-skill allowed tools
    # ------------------------------------------------------------------
    allowed_tools = meta.get("allowed_tools", list(safe_context.agent_tools.keys()))
    for tool_name in safe_context.agent_tools:
        if tool_name not in allowed_tools:
            raise ApprovalError(
                f"Skill '{skill_name}' is not allowed to use the tool '{tool_name}'"
            )
        

    # ------------------------------------------------------------------
    # Execute skill
    # ------------------------------------------------------------------
    try:
        result = skill.run(request, safe_context)
    except Exception as e:
        raise RuntimeError(
            f"Skill '{skill_name}' execution failed: {str(e)}"
        ) from e

    return result