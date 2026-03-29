# py_mono/skill/__init__.py
"""
Skills framework for py-coding-agent.

Public API:
    Skill         — abstract base class for all skills
    SkillContext  — runtime context passed to skills
    SkillRegistry — discovers and manages skills from skills/ directory

See ADR-010 for architecture details.
"""

from py_mono.skill.base import Skill, SkillContext, SkillRegistry

__all__ = ["Skill", "SkillContext", "SkillRegistry"]