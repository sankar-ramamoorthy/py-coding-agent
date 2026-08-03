# Project Audit - 2026-08-02

## Scope and Method

This is a source and local-verification audit of `py-coding-agent` at commit
`579ae39` (`Update SKILL.md`). The review covered the agent loop, built-in
tools, workspace boundary, dynamic tool and skill loading, skill approval,
provider/session/key handling, MCP integration, Docker configuration,
packaging, and tests. No runtime call to an LLM service or Docker daemon was
performed.

Severity uses the following definitions:

| Severity | Meaning |
| --- | --- |
| Critical | Prevents normal use or permits execution outside a stated trust boundary. |
| High | Material security, integrity, or core-workflow failure with a practical path to impact. |
| Medium | Important correctness, operational, or maintainability gap. |
| Low | Limited impact or quality issue that should be addressed during normal maintenance. |

## Executive Summary

The repository has a clear modular intent: a provider-agnostic agent loop,
tools, skills, playbooks, sessions, and an MCP adapter are separated into
distinct packages. The `Tool.run(**kwargs)` convention and the skill metadata
model are good foundations.

The current checkout is not runnable. Importing `py_mono.main` fails because
`py_mono/playbook/playbookregistry.py` has an `IndentationError`. A full
compile also found syntax errors in two additional modules. The present
execution boundary is not a sandbox: path-checked file tools are bypassable
through `shell`, dynamic tools and skills execute arbitrary Python at load
time, and Compose mounts the repository read-write into the agent container.

The immediate priority is to restore a compiling, test-collectable baseline;
then close the execution and dynamic-code trust boundaries before adding new
agent features.

## Architecture Observed

| Area | Current implementation | Assessment |
| --- | --- | --- |
| Entry point | `py_mono/main.py` builds base, dynamic, and MCP tools, loads skills, then starts the CLI. | Logical composition point, but unavailable due to an import-time syntax error. |
| Agent loop | `py_mono/agent/agent.py` retains canonical messages, calls one LLM tool at a time, limits steps, and prunes history. | Reasonable minimal design; debug logging is unsafe by default. |
| Built-in tools | Read/write/edit/list use `resolve_safe_path`; shell and package installation run subprocesses. | File tools are conceptually sandboxed, but the overall boundary is not enforced. |
| Skills | Markdown metadata plus optional `skill.py`, loaded using `importlib`. | Approval enforcement happens only after module import. |
| Dynamic tools | User-supplied Python is written to `dynamic_tools/` and imported on startup/reload. | Arbitrary code execution with no validation or isolation. |
| LLM providers | Ollama and LiteLLM translate to/from a normalized response shape. | The provider abstraction is useful; stored cloud keys are not correctly resolved. |
| MCP | Synchronous wrapper over a FastMCP client. | Small and isolated; lacks test coverage and timeout/error policy tests. |

## Findings

### Critical

#### C-01: The application cannot import or start

Evidence:

- `py_mono/playbook/playbookregistry.py:4` has an unexpected indent before
  `import yaml`. `py_mono/agent/agent.py:13` imports this module, so
  `import py_mono.main` fails before the CLI is constructed.
- `py_mono/utils/special_commands.py:28` has another `IndentationError`.
- `skills/bug_fix/skill.py:229` has a `return` outside a function, producing
  a `SyntaxError`.

Impact: The documented direct entry point and Docker command cannot start. The
broken skill also cannot be loaded, and syntax faults make static verification
unreliable.

Recommendation: Fix the three parse errors first and add a CI compilation gate
(`python -m compileall -q py_mono skills`) before test execution.

#### C-02: The claimed `/workspace` sandbox can be escaped

Evidence:

- `py_mono/utils/path_utils.py:10-13` accepts a candidate when its string
  merely starts with `WORKSPACE_ROOT`.
- With the default root `/workspace`, resolving `../workspace_evil` returns
  `/workspace_evil` and is accepted. That path is outside `/workspace`.
- `py_mono/tools/shell.py:47-52` uses `subprocess.run(..., shell=True)`.
  Setting `cwd` does not restrict commands such as `cd /app`, absolute paths,
  parent traversals, redirection, or network calls.
- `docker-compose.yml:12` mounts the full repository at `/app` read-write.

Impact: An LLM-selected command or a skill can read and modify mounted source,
credentials available to the container, and container-accessible network
resources. The documented workspace restriction does not hold.

Recommendation: Use `Path.is_relative_to(WORKSPACE_ROOT)` (or `relative_to` in
a try/except) instead of a string prefix. Treat shell execution as a separately
privileged capability: remove it from the default tool set, use an allowlisted
non-shell interface, or run it in a dedicated restricted container that mounts
only `/workspace`. Do not mount `.:/app` read-write in the execution container.

#### C-03: Proposed skills and dynamic tools run arbitrary code before approval

Evidence:

- `py_mono/skill/base.py:161-167` loads every `skill.py` with
  `spec.loader.exec_module(module)` during registry load. This executes module
  top-level code before `run_skill_safe` checks the skill status.
- `py_mono/tools/tool_loader.py:37-46` imports every `dynamic_tools/*.py` in
  the same way. There is no validation, signature, approval, or isolation.
- `py_mono/tools/create_tool.py:35-52` writes LLM-provided source that becomes
  executable after startup or `/reload_tools`.

Impact: Metadata approval is not a security boundary. Any writable skill or
dynamic-tool file can execute with the agent process permissions merely by
being discovered. With the Compose mounts, that includes host repository edits.

Recommendation: Do not import untrusted code during discovery. Parse metadata
without executing Python, require an explicit trusted activation record outside
the artifact being approved, and execute approved extensions in an isolated
worker with narrow tool RPC. Until that exists, disable runtime-generated tools
and load only reviewed built-in skills.

### High

#### H-01: Default debug output exposes prompts, workspace content, and model traffic

Evidence:

- `Agent.__init__` defaults `debug=True` at `py_mono/agent/agent.py:38`.
- `py_mono/agent/agent.py:82-86` prints the complete conversation, including
  user input and tool results.
- `py_mono/llm/ollama_provider.py:9` sets `DEBUG = True`; lines 91-108 print
  complete request payloads and model responses.
- `skills/generate_skill/skill.py:246` logs generated model text at INFO.

Impact: CLI, container, and CI logs can retain sensitive prompts, source, tool
output, and secrets pasted by a user.

Recommendation: Make debug logging opt-in, redact known secrets, and never log
complete prompts or provider payloads at normal log levels.

#### H-02: Persisted provider keys are stored under names the active provider does not resolve

Evidence:

- CLI commands store keys as `groq`, `openai`, or `anthropic` in
  `py_mono/ui/cli.py:91-100`.
- The registry exposes `litellm`, not those provider names, in
  `py_mono/llm/provider_registry.py:11-16`.
- `SessionManager._resolve_key` looks up the selected provider name; when it is
  `litellm`, `py_mono/session/session_manager.py:63-64` asks for `litellm`, not
  `groq`/`openai`/`anthropic`.

Impact: `/key groq ...` reports success but is not used when the user switches
to LiteLLM. Users may incorrectly believe encrypted key storage is active.

Recommendation: Define a canonical credential schema driven by the active
LiteLLM model provider, or have `/key` explicitly store a `litellm` default.
Add tests for CLI storage, session resolution, and environment fallback.

#### H-03: Test suite is not collectable and contains stale expectations

Evidence:

- Full `uv run pytest -q` stops during collection because
  `tests/test_listallpy_skill.py:6` imports `skills.listallpy.skill`, but there
  is no `skills/listallpy/` directory and `skills` is not packaged in
  `pyproject.toml:23-24`.
- The focused `tests/tools/test_create_tool.py` run has two failures. The test
  supplies `x = 1`, while `py_mono/tools/create_tool.py:20-22` requires a
  function; it also expects messages that do not match lines 12-13.

Impact: CI cannot establish a usable signal, and passing tests would not prove
the current implementation behavior.

Recommendation: Remove or restore the obsolete `listallpy` test/skill, decide
whether `skills` is application content or an importable package, and align the
dynamic-tool tests with the accepted source contract.

### Medium

#### M-01: Approval can rewrite skill definitions and has no immutable audit trail

Evidence: `/approve` updates `status:` directly in the skill's `SKILL.md` at
`py_mono/agent/agent.py:369-385`. Approval state and executable artifact live
in the same writable directory.

Impact: In a shared or unattended environment, a changed skill may be approved
without a durable association to the reviewed artifact. This compounds C-03.

Recommendation: Store approvals outside the skill directory with an artifact
hash, approver identity, timestamp, and explicit revocation path. Reload only
after the hash matches the approved artifact.

#### M-02: Tool contracts are inconsistent and schema generation is fragile

Evidence:

- `Tool.run` calls functions with keyword arguments
  (`py_mono/tools/tool.py:72-75`), but the broken bug-fix skill uses
  `.func({...})` at `skills/bug_fix/skill.py:126`, bypassing the wrapper and
  passing a positional dictionary.
- `create_tool` extracts a signature using regex at
  `py_mono/tools/create_tool.py:20-33`; annotations, defaults containing
  commas, positional-only parameters, and multiline signatures are not handled
  reliably. Every inferred parameter is marked required, including defaults.

Impact: Generated tools and skills can fail only at runtime; the advertised
tool execution contract is not consistently enforceable.

Recommendation: Enforce `Tool.run(**kwargs)` in existing skills, use `ast` and
`inspect.signature` for generated tool schemas, and validate a generated module
in a subprocess before activation.

#### M-03: Resource and failure controls are incomplete

Evidence:

- `shell` has no subprocess timeout (`py_mono/tools/shell.py:47-53`).
- `list_files` accepts unbounded `max_depth` and recursively materializes a
  complete tree (`py_mono/tools/list_files.py:24-39`).
- `OllamaProvider.generate` has a 300-second request timeout
  (`py_mono/llm/ollama_provider.py:96-100`) but does not catch request errors;
  this can terminate the agent loop rather than return a normalized error.

Impact: A tool call can tie up the process, generate excessive output/memory,
or terminate an interactive session unexpectedly.

Recommendation: Add execution timeouts and output/file-count limits, validate
numeric arguments, and normalize provider exceptions at the provider boundary.

#### M-04: Dependency and deployment hygiene need tightening

Evidence:

- `pyproject.toml:8-16` has mostly unpinned runtime dependencies despite
  behavior-sensitive execution and protocol libraries.
- `dockerfile:18` runs `uv sync --no-dev --no-editable`, then line 25 uses
  `uv pip install --system -e .`, mixing a managed uv environment with a system
  editable install.
- `docker-compose.yml:9-10` and lines 31-32 publish debug and MCP ports to the
  host without a stated requirement.

Impact: Reproducibility, package isolation, and host exposure are weaker than
the Docker-first design suggests.

Recommendation: Keep the lockfile current and enforce it in CI, use one image
installation strategy, run as a non-root user, and bind ports only when needed.

### Low

#### L-01: Encoding and repository hygiene issues reduce maintainability

Evidence: Several source comments and user-facing strings display mojibake
(for example `py_mono/main.py` and `dockerfile`), and unused/obsolete files
remain (`py_mono/agent/agent_backupv1.py`, `py_mono/skill/prompts_bak.py`, and
deprecated helper methods).

Impact: The behavior is not directly unsafe, but it obscures code review,
causes confusing CLI output, and increases the chance of fixing the wrong
implementation path.

Recommendation: Normalize file encoding to UTF-8, remove or archive obsolete
code deliberately, and keep one authoritative implementation per workflow.

## Verification Results

| Command | Result |
| --- | --- |
| `uv run pytest -q` | Failed at collection: `ModuleNotFoundError: No module named 'skills'` from `tests/test_listallpy_skill.py`. |
| `uv run python -m compileall -q py_mono skills` | Failed: indentation errors in `playbookregistry.py` and `special_commands.py`; syntax error in `skills/bug_fix/skill.py`. |
| `uv run python -c "import py_mono.main"` | Failed due to the `playbookregistry.py` indentation error. |
| `uv run pytest tests/tools/test_create_tool.py -q` | Failed: 2 failed, 1 passed; tests and implementation disagree on validation and messages. |
| Workspace guard probe | `resolve_safe_path('../workspace_evil')` returned `/workspace_evil` instead of rejecting it. |

The first `uv` attempt was denied access to the shared cache by the local
sandbox. The commands above were then repeated with cache access; that did not
affect repository state.

## Recommended Remediation Plan

### Phase 0: Restore a trustworthy baseline

1. Fix the three syntax/indentation errors.
2. Resolve the obsolete `listallpy` test and dynamic-tool test mismatch.
3. Add `compileall` and `pytest` as required CI checks. Do not proceed while
   either fails.

### Phase 1: Re-establish the execution boundary

1. Correct `resolve_safe_path` using path containment, with tests for sibling
   prefixes, absolute paths, traversal, and symlinks.
2. Remove general `shell=True` from the default capability. Use a separate,
   explicitly enabled executor with a minimal workspace-only mount.
3. Change Compose so source is read-only or baked into the image; mount only
   the intended workspace read-write.

### Phase 2: Secure extensions and credentials

1. Stop import-time execution for discovered skills and dynamic tools.
2. Disable runtime-generated Python extensions until reviewed activation and
   isolated execution exist.
3. Repair LiteLLM credential mapping and test it without logging secret values.
4. Default prompt/provider debug logging to off and add redaction.

### Phase 3: Strengthen reliability

1. Add tests for tools, paths, provider transforms, key selection, dynamic
   loader rejection, skill approval, and MCP errors.
2. Add integration tests that construct `main` with fake providers and tools.
3. Add timeout and size limits to subprocess, network, and recursive traversal
   operations.
4. Consolidate old implementations only after the baseline is green.

## Positive Controls Worth Preserving

- The agent stores a normalized internal message form and delegates wire-format
  differences to provider adapters.
- File tools share a path helper; fixing that helper benefits several tools.
- `SafeAgentTools` already models per-skill tool allowlists and should remain
  part of an eventual isolated skill-execution design.
- The key store uses Fernet and avoids revealing values through `repr`; repair
  credential resolution rather than replacing that component.

## Residual Risk

This audit did not test a live LLM, an MCP server, or container runtime
permissions. Those checks are required after the baseline and execution
boundary findings are corrected. Until then, treat this project as a local
development prototype, not a sandboxed or multi-user coding-agent environment.
