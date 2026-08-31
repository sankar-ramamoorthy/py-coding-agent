"""File-backed lifecycle reports for generated skill candidates."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from py_mono.skill.diffing import ArtifactDiff, candidate_dir_for, has_candidate
from py_mono.skill.lifecycle import LifecycleStageResult, SkillLifecycleRun, SmokeTestResult

logger = logging.getLogger(__name__)

REPORT_MD = "lifecycle_report.md"
REPORT_JSON = "lifecycle_report.json"


@dataclass
class ReportWriteResult:
    ok: bool
    report_dir: Path
    markdown_path: Optional[Path] = None
    json_path: Optional[Path] = None
    error: str = ""


@dataclass
class LifecycleReportView:
    skill_name: str
    report_dir: Path
    markdown_path: Path
    json_path: Path
    has_candidate: bool
    data: Optional[dict[str, Any]] = None
    markdown: str = ""
    error: str = ""


def write_lifecycle_report(
    *,
    report_dir: Path,
    skill_name: str,
    mode: str,
    status: str,
    lifecycle: SkillLifecycleRun,
    skill_path: Path,
    candidate_path: Optional[Path] = None,
    smoke_test: Optional[SmokeTestResult] = None,
    diffs: Optional[Iterable[ArtifactDiff]] = None,
    failure_context: Any = None,
    next_steps: Optional[Iterable[str]] = None,
) -> ReportWriteResult:
    """Write Markdown and JSON lifecycle reports.

    Report persistence is deliberately separate from approval. A failure here
    is returned to the caller for display, but it does not approve, load, or
    reject the candidate.
    """

    record = build_lifecycle_report_record(
        skill_name=skill_name,
        mode=mode,
        status=status,
        lifecycle=lifecycle,
        skill_path=skill_path,
        candidate_path=candidate_path,
        smoke_test=smoke_test,
        diffs=list(diffs or []),
        failure_context=failure_context,
        next_steps=list(next_steps or []),
    )
    markdown = render_lifecycle_report_markdown(record)

    try:
        report_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = report_dir / REPORT_MD
        json_path = report_dir / REPORT_JSON
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return ReportWriteResult(
            ok=True,
            report_dir=report_dir,
            markdown_path=markdown_path,
            json_path=json_path,
        )
    except OSError as exc:
        logger.warning("Could not write lifecycle report to %s: %s", report_dir, exc)
        return ReportWriteResult(
            ok=False,
            report_dir=report_dir,
            error=f"{exc.__class__.__name__}: {exc}",
        )


def load_lifecycle_report_view(skill_name: str, skill_dir: Path) -> LifecycleReportView:
    candidate_dir = candidate_dir_for(skill_dir)
    pending_candidate = has_candidate(skill_dir)
    report_dir = candidate_dir if pending_candidate else skill_dir
    markdown_path = report_dir / REPORT_MD
    json_path = report_dir / REPORT_JSON

    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return LifecycleReportView(
                skill_name=skill_name,
                report_dir=report_dir,
                markdown_path=markdown_path,
                json_path=json_path,
                has_candidate=pending_candidate,
                data=data,
            )
        except (OSError, JSONDecodeError) as exc:
            markdown = _read_markdown_fallback(markdown_path)
            return LifecycleReportView(
                skill_name=skill_name,
                report_dir=report_dir,
                markdown_path=markdown_path,
                json_path=json_path,
                has_candidate=pending_candidate,
                markdown=markdown,
                error=f"{exc.__class__.__name__}: {exc}",
            )

    markdown = _read_markdown_fallback(markdown_path)
    return LifecycleReportView(
        skill_name=skill_name,
        report_dir=report_dir,
        markdown_path=markdown_path,
        json_path=json_path,
        has_candidate=pending_candidate,
        markdown=markdown,
        error="" if markdown else "No lifecycle report found.",
    )


def render_lifecycle_review(view: LifecycleReportView) -> str:
    lines = [f"Review: {view.skill_name}"]
    if view.has_candidate:
        lines.append(f"Candidate: {view.report_dir}")

    if view.data is not None:
        return "\n".join(lines + _render_json_summary(view))

    if view.markdown:
        if view.error:
            lines.append(f"Lifecycle report JSON unavailable: {view.error}")
        lines.append(f"Lifecycle report: {view.markdown_path}")
        lines.append("")
        lines.append(_preview_markdown(view.markdown))
        lines.append("")
        lines.append(f"Approve: /approve {view.skill_name}")
        return "\n".join(lines)

    lines.append(view.error or "No lifecycle report found.")
    if view.has_candidate:
        lines.append(f"Candidate exists, but no lifecycle report was found at {view.report_dir}.")
    lines.append(f"Approve: /approve {view.skill_name}")
    return "\n".join(lines)


def build_lifecycle_report_record(
    *,
    skill_name: str,
    mode: str,
    status: str,
    lifecycle: SkillLifecycleRun,
    skill_path: Path,
    candidate_path: Optional[Path],
    smoke_test: Optional[SmokeTestResult],
    diffs: list[ArtifactDiff],
    failure_context: Any,
    next_steps: list[str],
) -> dict[str, Any]:
    baseline = _baseline_record(diffs)
    return {
        "skill_name": skill_name,
        "mode": mode,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_path": str(skill_path),
        "candidate_path": str(candidate_path) if candidate_path is not None else "",
        "stages": [_stage_record(stage) for stage in lifecycle.stages],
        "smoke_test": _smoke_record(smoke_test),
        "baseline": baseline,
        "diffs": [_diff_record(diff) for diff in diffs],
        "failure_context": _failure_context_record(failure_context),
        "next_steps": next_steps,
    }


def render_lifecycle_report_markdown(record: dict[str, Any]) -> str:
    lines = [
        f"# Lifecycle Report: {record['skill_name']}",
        "",
        f"- Status: {record['status']}",
        f"- Mode: {record['mode']}",
        f"- Timestamp: {record['timestamp']}",
        f"- Skill path: {record['skill_path']}",
    ]
    if record["candidate_path"]:
        lines.append(f"- Candidate path: {record['candidate_path']}")

    lines.extend(["", "## Stages", ""])
    for stage in record["stages"]:
        lines.append(f"- {stage['stage']}: {stage['status']} - {stage['message']}")
        for detail in stage["details"]:
            lines.append(f"  - {detail}")

    smoke = record["smoke_test"]
    if smoke is not None:
        lines.extend(["", "## Smoke Test", ""])
        lines.append(f"- Status: {smoke['status']}")
        lines.append(f"- Request: {smoke['request']}")
        if smoke["output_preview"]:
            lines.append(f"- Output preview: {smoke['output_preview']}")
        if smoke["failure_reason"]:
            lines.append(f"- Failure reason: {smoke['failure_reason']}")

    failure_context = record["failure_context"]
    if failure_context is not None:
        lines.extend(["", "## Failure Context", ""])
        for key in ("request", "failure_reason", "provider", "model", "timestamp"):
            lines.append(f"- {key.replace('_', ' ').title()}: {failure_context[key]}")

    if record["baseline"] is not None or record["diffs"]:
        lines.extend(["", "## Baseline", ""])
        baseline = record["baseline"] or {}
        lines.append(f"- Available: {baseline.get('available', False)}")
        if baseline.get("reason"):
            lines.append(f"- Reason: {baseline['reason']}")

    if record["diffs"]:
        lines.extend(["", "## Diffs", ""])
        for diff in record["diffs"]:
            lines.append(f"### {diff['artifact']}")
            lines.append("")
            lines.append("```diff")
            lines.append(diff["diff_text"])
            lines.append("```")
            lines.append("")

    if record["next_steps"]:
        lines.extend(["", "## Next Steps", ""])
        for index, step in enumerate(record["next_steps"], 1):
            lines.append(f"{index}. {step}")

    return "\n".join(lines).rstrip() + "\n"


def _stage_record(stage: LifecycleStageResult) -> dict[str, Any]:
    return {
        "stage": stage.stage,
        "status": stage.status,
        "message": stage.message,
        "details": list(stage.details),
    }


def _smoke_record(smoke_test: Optional[SmokeTestResult]) -> Optional[dict[str, str]]:
    if smoke_test is None:
        return None
    return asdict(smoke_test)


def _diff_record(diff: ArtifactDiff) -> dict[str, Any]:
    return {
        "artifact": diff.artifact,
        "changed": diff.changed,
        "baseline_available": diff.baseline_available,
        "diff_text": diff.diff_text,
    }


def _baseline_record(diffs: list[ArtifactDiff]) -> Optional[dict[str, Any]]:
    if not diffs:
        return None
    available = all(diff.baseline_available for diff in diffs)
    reason = ""
    if not available:
        reason = next(
            (diff.diff_text for diff in diffs if not diff.baseline_available),
            "No approved baseline available.",
        )
    return {"available": available, "reason": reason}


def _failure_context_record(failure_context: Any) -> Optional[dict[str, str]]:
    if failure_context is None:
        return None
    return {
        "request": str(getattr(failure_context, "request", "")),
        "failure_reason": str(getattr(failure_context, "failure_reason", "")),
        "provider": str(getattr(failure_context, "provider", "")),
        "model": str(getattr(failure_context, "model", "")),
        "timestamp": str(getattr(failure_context, "timestamp", "")),
    }


def _read_markdown_fallback(markdown_path: Path) -> str:
    try:
        if markdown_path.exists():
            return markdown_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return ""


def _render_json_summary(view: LifecycleReportView) -> list[str]:
    data = view.data or {}
    lines = [
        f"Status: {data.get('status', '<unknown>')}",
        f"Mode: {data.get('mode', '<unknown>')}",
        f"Lifecycle report: {view.json_path}",
    ]
    if data.get("candidate_path"):
        lines.append(f"Candidate path: {data['candidate_path']}")
    if data.get("timestamp"):
        lines.append(f"Timestamp: {data['timestamp']}")

    stages = data.get("stages") or []
    if stages:
        lines.extend(["", "Stages:"])
        for stage in stages:
            lines.append(
                "  - "
                f"{stage.get('stage', '<unknown>')}: "
                f"{stage.get('status', '<unknown>')} - "
                f"{stage.get('message', '')}"
            )

    smoke = data.get("smoke_test")
    if smoke:
        lines.extend(["", "Smoke test:"])
        lines.append(f"  - Status: {smoke.get('status', '<unknown>')}")
        if smoke.get("request"):
            lines.append(f"  - Request: {smoke['request']}")
        if smoke.get("output_preview"):
            lines.append(f"  - Output preview: {smoke['output_preview']}")
        if smoke.get("failure_reason"):
            lines.append(f"  - Failure: {smoke['failure_reason']}")

    diffs = data.get("diffs") or []
    if diffs:
        lines.extend(["", "Diffs:"])
        for diff in diffs:
            if not diff.get("baseline_available", False):
                summary = "baseline unavailable"
            elif diff.get("changed", False):
                summary = "changed"
            else:
                summary = "no changes"
            lines.append(f"  - {diff.get('artifact', '<unknown>')}: {summary}")

    next_steps = data.get("next_steps") or [f"Approve: /approve {view.skill_name}"]
    lines.extend(["", "Next steps:"])
    for index, step in enumerate(next_steps, 1):
        lines.append(f"  {index}. {step}")
    if not any("/approve " in step for step in next_steps):
        lines.append(f"  {len(next_steps) + 1}. Approve: /approve {view.skill_name}")
    return lines


def _preview_markdown(markdown: str, max_lines: int = 80) -> str:
    lines = markdown.splitlines()
    preview = lines[:max_lines]
    if len(lines) > max_lines:
        preview.append("...")
    return "\n".join(preview)
