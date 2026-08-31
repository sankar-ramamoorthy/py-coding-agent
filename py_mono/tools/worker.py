"""Subprocess worker execution for dynamic tool files."""

from __future__ import annotations

import contextlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from py_mono.tools.tool import Tool

DEFAULT_TOOL_WORKER_TIMEOUT_SECONDS = 30


class DynamicToolWorkerError(RuntimeError):
    pass


def run_dynamic_tool_in_worker(
    *,
    module_path: Path,
    tool_name: str,
    args: dict[str, Any],
    timeout_seconds: float = DEFAULT_TOOL_WORKER_TIMEOUT_SECONDS,
) -> Any:
    process = subprocess.run(
        [sys.executable, "-m", "py_mono.tools.worker"],
        input=json.dumps(
            {
                "module_path": str(module_path),
                "tool_name": tool_name,
                "args": args,
            }
        )
        + "\n",
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
        timeout=timeout_seconds,
        check=False,
    )
    if process.returncode != 0:
        raise DynamicToolWorkerError(
            f"Dynamic tool worker exited with {process.returncode}: {process.stderr.strip()}"
        )
    try:
        message = json.loads(process.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise DynamicToolWorkerError("Dynamic tool worker emitted malformed output") from exc
    if message.get("type") == "result":
        return message.get("value")
    if message.get("type") == "error":
        raise DynamicToolWorkerError(str(message.get("message", "unknown worker error")))
    raise DynamicToolWorkerError(
        f"Dynamic tool worker emitted unknown message type: {message.get('type')}"
    )


def main() -> None:
    try:
        init = json.loads(sys.stdin.readline())
        module_path = Path(str(init["module_path"]))
        tool_name = str(init["tool_name"])
        args = init.get("args") or {}
        with contextlib.redirect_stdout(sys.stderr):
            tool = _load_tool(module_path, tool_name)
            value = tool.run(**args)
        print(json.dumps({"type": "result", "value": value}))
    except Exception as exc:
        print(json.dumps({"type": "error", "message": f"{exc.__class__.__name__}: {exc}"}))


def _load_tool(module_path: Path, tool_name: str) -> Tool:
    spec = importlib.util.spec_from_file_location(f"isolated_tool.{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for value in vars(module).values():
        if isinstance(value, Tool) and value.name == tool_name:
            return value
    raise RuntimeError(f"No Tool named '{tool_name}' found in {module_path}")


if __name__ == "__main__":
    main()
