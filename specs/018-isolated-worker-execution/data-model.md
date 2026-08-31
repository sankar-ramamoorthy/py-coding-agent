# Data Model: Isolated Worker Execution

## SkillProxy

- `name`: Normalized skill name.
- `description`: Metadata description from `SKILL.md`.
- `skill_py_path`: Path to approved `skill.py`.

## WorkerRequest

- `kind`: `skill` or `dynamic_tool`.
- `module_path`: Extension module path.
- `skill_name` or `tool_name`: Invocation target.
- `request` or `args`: Input payload.
- `workspace_root`: Workspace path.
- `allowed_tools`: Allowed parent tools for skills.

## WorkerResponse

- `type`: `result`, `error`, or `tool_call`.
- `value`: Result value for successful execution.
- `message`: Error message for failures.
- `tool`: Requested tool name for tool calls.
- `args`: Tool keyword arguments.

## DynamicToolProxy

- `name`: Tool name extracted from metadata.
- `description`: Tool description extracted from metadata.
- `parameters`: JSON-schema-like parameters extracted from metadata.
- `module_path`: Dynamic tool file path.
