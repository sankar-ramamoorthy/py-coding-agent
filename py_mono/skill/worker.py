"""Subprocess worker execution for approved skill files."""

from __future__ import annotations

import contextlib
import importlib.util
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from py_mono.skill.base import Skill, SkillContext

DEFAULT_WORKER_TIMEOUT_SECONDS = 30


class WorkerExecutionError(RuntimeError):
    pass


def run_skill_in_worker(
    *,
    skill_py_path: Path,
    skill_name: str,
    request: str,
    context: SkillContext,
    allowed_tools: set[str],
    timeout_seconds: float = DEFAULT_WORKER_TIMEOUT_SECONDS,
) -> str:
    process = subprocess.Popen(
        [sys.executable, "-m", "py_mono.skill.worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(Path.cwd()),
    )
    assert process.stdin is not None
    assert process.stdout is not None

    output_queue: queue.Queue[Optional[str]] = queue.Queue()
    stderr_queue: queue.Queue[str] = queue.Queue()

    def read_stdout() -> None:
        try:
            for line in process.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    def read_stderr() -> None:
        assert process.stderr is not None
        for line in process.stderr:
            stderr_queue.put(line)

    threading.Thread(target=read_stdout, daemon=True).start()
    threading.Thread(target=read_stderr, daemon=True).start()

    init = {
        "module_path": str(skill_py_path),
        "skill_name": skill_name,
        "request": request,
        "workspace_root": str(context.workspace_root),
        "tools": sorted(context.agent_tools.keys()),
    }
    _send(process, init)

    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            process.kill()
            raise WorkerExecutionError(
                f"Skill worker for '{skill_name}' timed out after {timeout_seconds:g}s"
            )

        try:
            line = output_queue.get(timeout=min(0.1, remaining))
        except queue.Empty:
            if process.poll() is not None:
                stderr = _drain_queue(stderr_queue).strip()
                raise WorkerExecutionError(
                    f"Skill worker for '{skill_name}' exited without a result."
                    + (f" stderr: {stderr}" if stderr else "")
                )
            continue

        if line is None:
            stderr = _drain_queue(stderr_queue).strip()
            raise WorkerExecutionError(
                f"Skill worker for '{skill_name}' exited without a result."
                + (f" stderr: {stderr}" if stderr else "")
            )

        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            process.kill()
            raise WorkerExecutionError(
                f"Skill worker for '{skill_name}' emitted malformed RPC: {exc}"
            ) from exc

        message_type = message.get("type")
        if message_type == "result":
            process.wait(timeout=1)
            return str(message.get("value", ""))
        if message_type == "error":
            process.wait(timeout=1)
            raise WorkerExecutionError(str(message.get("message", "unknown worker error")))
        if message_type == "tool_call":
            response = _handle_tool_call(
                message=message,
                skill_name=skill_name,
                context=context,
                allowed_tools=allowed_tools,
            )
            _send(process, response)
            continue
        if message_type == "provider_generate":
            response = _handle_provider_generate(message, context)
            _send(process, response)
            continue

        process.kill()
        raise WorkerExecutionError(
            f"Skill worker for '{skill_name}' emitted unknown RPC type: {message_type}"
        )


def _handle_tool_call(
    *,
    message: dict[str, Any],
    skill_name: str,
    context: SkillContext,
    allowed_tools: set[str],
) -> dict[str, Any]:
    tool_name = str(message.get("tool") or "")
    args = message.get("args") or {}
    if tool_name not in allowed_tools:
        return {
            "type": "tool_result",
            "ok": False,
            "error": f"Skill '{skill_name}' is not allowed to use the tool '{tool_name}'",
        }
    tool = context.agent_tools.get(tool_name)
    if tool is None:
        return {
            "type": "tool_result",
            "ok": False,
            "error": f"Unknown tool '{tool_name}'",
        }
    try:
        return {"type": "tool_result", "ok": True, "value": tool.run(**args)}
    except Exception as exc:
        return {
            "type": "tool_result",
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def _handle_provider_generate(
    message: dict[str, Any],
    context: SkillContext,
) -> dict[str, Any]:
    if context.session_manager is None:
        return {
            "type": "provider_result",
            "ok": False,
            "error": "No session manager is available to the skill worker",
        }
    if message.get("tools") is not None:
        return {
            "type": "provider_result",
            "ok": False,
            "error": "Provider RPC only supports tools=None",
        }
    try:
        provider = context.session_manager.get_active_provider()
        result = provider.generate(messages=message.get("messages") or [], tools=None)
        return {"type": "provider_result", "ok": True, "value": result}
    except Exception as exc:
        return {
            "type": "provider_result",
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def _send(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()


def _drain_queue(values: queue.Queue[str]) -> str:
    lines = []
    while True:
        try:
            lines.append(values.get_nowait())
        except queue.Empty:
            return "".join(lines)


class RpcTool:
    def __init__(self, name: str, protocol: "WorkerProtocol"):
        self.name = name
        self.description = f"RPC proxy for parent tool {name}"
        self.parameters = {"type": "object", "properties": {}, "required": []}
        self._protocol = protocol

    @property
    def func(self):
        raise RuntimeError("Direct tool.func() usage is forbidden - use tool.run(**kwargs)")

    def run(self, **kwargs):
        return self._protocol.call_tool(self.name, kwargs)


class RpcProvider:
    model_name = "<parent-active-model>"

    def __init__(self, protocol: "WorkerProtocol"):
        self._protocol = protocol

    def generate(self, messages, tools=None):
        return self._protocol.call_provider_generate(messages=messages, tools=tools)


class RpcSessionManager:
    def __init__(self, protocol: "WorkerProtocol"):
        self._provider = RpcProvider(protocol)

    def get_active_provider(self):
        return self._provider


class WorkerProtocol:
    def __init__(self, out):
        self._out = out

    def call_tool(self, tool_name: str, args: Mapping[str, Any]):
        self._write({"type": "tool_call", "tool": tool_name, "args": dict(args)})
        response = _read_json_line(sys.stdin)
        if response.get("type") != "tool_result":
            raise RuntimeError("Parent returned unexpected tool RPC response")
        if not response.get("ok", False):
            raise RuntimeError(str(response.get("error", "tool RPC failed")))
        return response.get("value")

    def call_provider_generate(self, messages, tools=None):
        self._write({"type": "provider_generate", "messages": messages, "tools": tools})
        response = _read_json_line(sys.stdin)
        if response.get("type") != "provider_result":
            raise RuntimeError("Parent returned unexpected provider RPC response")
        if not response.get("ok", False):
            raise RuntimeError(str(response.get("error", "provider RPC failed")))
        return response.get("value")

    def result(self, value: Any) -> None:
        self._write({"type": "result", "value": value})

    def error(self, message: str) -> None:
        self._write({"type": "error", "message": message})

    def _write(self, message: dict[str, Any]) -> None:
        self._out.write(json.dumps(message) + "\n")
        self._out.flush()


def main() -> None:
    protocol_out = sys.stdout
    protocol = WorkerProtocol(protocol_out)
    try:
        init = _read_json_line(sys.stdin)
        module_path = Path(str(init["module_path"]))
        skill_name = str(init["skill_name"])
        request = str(init["request"])
        tools = {
            str(tool_name): RpcTool(str(tool_name), protocol)
            for tool_name in init.get("tools", [])
        }
        context = SkillContext(
            workspace_root=Path(str(init["workspace_root"])),
            agent_tools=tools,
            session_manager=RpcSessionManager(protocol),
        )
        context.calling_skill = skill_name
        with contextlib.redirect_stdout(sys.stderr):
            skill = _load_skill_from_path(module_path)
            result = skill.run(request, context)
        protocol.result(result)
    except Exception as exc:
        protocol.error(f"{exc.__class__.__name__}: {exc}")


def _load_skill_from_path(module_path: Path) -> Skill:
    spec = importlib.util.spec_from_file_location(f"isolated_skill.{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(sys.stderr):
        spec.loader.exec_module(module)
    for value in vars(module).values():
        if isinstance(value, type) and issubclass(value, Skill) and value is not Skill:
            return value()
    raise RuntimeError("No Skill subclass found in worker module")


def _read_json_line(stream) -> dict[str, Any]:
    line = stream.readline()
    if not line:
        raise RuntimeError("RPC stream closed")
    return json.loads(line)


if __name__ == "__main__":
    main()
