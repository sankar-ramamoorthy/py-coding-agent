# Contract: Extension Worker RPC

## Skill Worker Init

Parent sends one JSON line:

```json
{
  "kind": "skill",
  "module_path": "skills/demo/skill.py",
  "skill_name": "demo",
  "request": "/skill demo",
  "workspace_root": "/workspace",
  "allowed_tools": ["list_files"]
}
```

## Tool Call

Worker may emit:

```json
{"type": "tool_call", "tool": "list_files", "args": {"path": "."}}
```

Parent replies:

```json
{"type": "tool_result", "ok": true, "value": "..."}
```

or:

```json
{"type": "tool_result", "ok": false, "error": "Skill 'demo' is not allowed to use tool 'read_file'"}
```

## Final Result

Worker emits:

```json
{"type": "result", "value": "..."}
```

## Error

Worker emits:

```json
{"type": "error", "message": "RuntimeError: boom"}
```

Malformed messages, timeout, or unexpected worker exit are parent-side execution failures.
