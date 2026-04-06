from datetime import datetime
from py_mono.skill.base import Skill, SkillContext

class Myp1Skill(Skill):
    def name(self) -> str:
        return "myp1"

    def description(self) -> str:
        return "what is today's day of week?"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            tool = context.agent_tools.get("get_current_datetime")
            if not tool:
                return "Error: get_current_datetime tool not available"
            datetime_str = tool.run({})
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            current_dt_utc = datetime.fromisoformat(datetime_str)
            return current_dt_utc.strftime("%A")
        except Exception as e:
            return f"Error: {e}"