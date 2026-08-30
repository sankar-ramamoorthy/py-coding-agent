"""Failure-context helpers for skill evolution proposals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from py_mono.skill.telemetry import TELEMETRY_LOG, read_skill_runs


@dataclass
class SkillFailureContext:
    skill_name: str
    request: str
    failure_reason: str
    provider: str
    model: str
    timestamp: str

    def to_prompt_text(self) -> str:
        return (
            f"Recent failure for skill '{self.skill_name}':\n"
            f"- request: {self.request or '<unknown>'}\n"
            f"- failure: {self.failure_reason or '<unknown>'}\n"
            f"- provider: {self.provider}\n"
            f"- model: {self.model}\n"
            f"- timestamp: {self.timestamp}"
        )


def latest_failure_context(skill_name: str, log_path: Path = TELEMETRY_LOG) -> Optional[SkillFailureContext]:
    candidate_names = {skill_name, skill_name.replace("-", "_"), skill_name.replace("_", "-")}
    for record in reversed(read_skill_runs(log_path)):
        record_skill = str(record.get("skill") or "")
        if record_skill not in candidate_names:
            continue
        if record.get("success") is not False:
            continue
        failure_reason = str(record.get("failure_reason") or "").strip()
        request = str(record.get("request") or "").strip()
        if not failure_reason:
            continue
        return SkillFailureContext(
            skill_name=record_skill,
            request=request,
            failure_reason=failure_reason,
            provider=str(record.get("provider") or "<unknown>"),
            model=str(record.get("model") or "<unknown>"),
            timestamp=str(record.get("timestamp") or "<unknown>"),
        )
    return None
