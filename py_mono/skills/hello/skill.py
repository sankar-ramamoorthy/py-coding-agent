# skills/hello/skill.py

from py_mono.skill.base import Skill, SkillContext


class HelloSkill(Skill):
    def name(self) -> str:
        return "hello"

    def description(self) -> str:
        return "Say hello and echo the arguments."

    def run(self, request: str, context: SkillContext) -> str:
        # You can fill this in later once you’re comfortable.
        return f"[HELLO SKILL] Got request: {request!r}"
