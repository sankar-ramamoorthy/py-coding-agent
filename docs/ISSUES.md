# Issues Register

Lightweight issue tracker for py-coding-agent. Not a substitute for `docs/adr/` (standing
architecture decisions) or `specs/` (Spec Kit feature plans) — this is for tracking discrete,
open pieces of work and known problems across sessions.

## Fields
- **ID** — sequential, prefixed `ISS-NNN` (zero-padded, 3 digits, monotonically increasing, never reused)
- **Title** — short description
- **Status** — `open | in-progress | blocked | done | wontfix`
- **Branch** — branch working the issue, if any (`—` if none yet)
- **Source** — where it originated (e.g. link/reference to audit report, session, or requester)
- **Notes** — brief context, links to relevant files/ADRs

## Open / Tracked

| ID | Title | Status | Branch | Source | Notes |
|----|-------|--------|--------|--------|-------|
| ISS-005 | Pre-existing test failures unrelated to any current branch work | open | — | Discovered 2026-08-03 verifying kb-template | `tests/test_listallpy_skill.py` fails to collect (`ModuleNotFoundError: No module named 'skills'`); `tests/tools/test_create_tool.py` has 2 failing assertions (`test_create_tool_writes_file_for_valid_name`, `test_create_tool_rejects_invalid_module_name`) — behavior doesn't match test expectations. Confirmed pre-existing by reproducing identically with kb-template's changes stashed. Not fixed as part of kb-template (out of scope, unrelated concern per Constitution Principle I). |
| ISS-006 | `pyyaml` used transitively but not declared in root `pyproject.toml` | open | — | Discovered 2026-08-03 during kb-template planning; unbundled 2026-08-03 per external PR review | `py_mono/skill/validator.py`, `py_mono/skill/base.py`, and `py_mono/playbook/playbookregistry.py` all `import yaml` directly, but it's only ever resolved transitively (via `litellm`/`fastmcp`), never declared as a direct dependency. A fix was briefly bundled into the kb-template branch (commit `c3f8f80`) but reverted (commit pending) since kb-template's own `pyproject.toml` already declares `pyyaml` independently and doesn't need the root repo touched — this is a separate, pre-existing hygiene gap, not a kb-template requirement. |
| ISS-008 | Full isolated-worker execution for skills/dynamic tools (narrow tool RPC) | open | — | docs/project-audit-2026-08-02.md (C-03) remediation, deferred 2026-08-03 during ISS-003 | The audit's full C-03 recommendation was "execute approved extensions in an isolated worker with narrow tool RPC" — a materially larger infrastructure project (real process/container isolation + a constrained tool-call protocol), explicitly out of scope for ISS-003's fix (which closed the "runs before approval" gap via a hash-ledger gate, not content-level sandboxing). Tracked here for future consideration; not started. |

## Closed

| ID | Title | Status | Branch | Source | Notes |
|----|-------|--------|--------|--------|-------|
| ISS-001 | App fails to import/start (syntax errors) | done | — | docs/project-audit-2026-08-02.md (C-01) | Confirmed fixed 2026-08-03: `python -m compileall -q py_mono skills kb-template` exits 0. Original fix landed in commit `34e595e` ("fixed syntax errors and tested system"). |
| ISS-004 | Add kb-template/ portable knowledge-base scaffold | done | kb-template | 2026-08-03 session | Landed in commits `1dd949f`, `b12cc64`, `c3f8f80` on branch `kb-template`. Reusable YAML front-matter + Obsidian-markdown scaffold with a standalone validator, extracted before further TradeForge-KB/AITrader-style drift accumulates. See `specs/001-kb-template/`. |
| ISS-007 | Add dual Ollama backend selection (local + remote GPU) with runtime model switching | done | ollama-dual-backend | 2026-08-03 session, user request | Landed in commits `bf1e23b`, `550a51d` on branch `ollama-dual-backend`. Adds `ollama-remote`/`ollama-local`/`ollama-auto` `provider_registry.py` entries wrapping the existing `OllamaProvider` (new optional `base_url` param) plus a connectivity-probe fallback (`ollama-auto` prefers remote GPU desktop over Tailscale, falls back to local). Model switching works via the existing `/provider <name> <model>` command, no command-dispatch changes. Verified end-to-end against the real backends, not just mocked tests. See `specs/002-ollama-dual-backend/`. |
| ISS-002 | `/workspace` sandbox escape via path-check bypass | done | fix-workspace-sandbox | docs/project-audit-2026-08-02.md (C-02) | Landed in commits `71a9ffa`, `ad8eb20` on branch `fix-workspace-sandbox`. Real path containment (`Path.is_relative_to`) replaces the string-prefix check, plus a new empty-by-default `ADDITIONAL_ALLOWED_PATHS` allowlist; `shell` tool now opt-in via `ENABLE_SHELL_TOOL` (default false) with a 30s timeout, description corrected to not overstate its safety; `docker-compose.yml`'s `.:/app` mount is now read-only. `docs/adr/ADR-001` corrected (Proposed → Accepted). Both original bugs live-demonstrated pre-fix and the fix verified for real, post-fix, inside the actual running container (not just mocked tests) — see `specs/003-fix-workspace-sandbox/`. |
| ISS-003 | Skills/dynamic tools execute arbitrary code before approval | done | fix-skill-tool-approval-gate | docs/project-audit-2026-08-02.md (C-03) | Landed in commits `d4cddfa`, `f542ccc` on branch `fix-skill-tool-approval-gate`. `SkillRegistry.load()`/`reload_skill()` gated on a hash-ledger approval record (`skills/.approvals.json`, content hash of `skill.py` at approval time — not just the in-file status field) before `exec_module` runs; editing `skill.py` post-approval invalidates it. `/approve` re-validates current `skill.py` via `validate_skill_py` before writing the ledger. The 8 pre-existing approved skills auto-seeded with zero disruption. `ENABLE_DYNAMIC_TOOLS` (default false) gates dynamic-tool auto-loading, mirroring ISS-002's `ENABLE_SHELL_TOOL`; static forbidden-pattern/AST validation added before `exec_module` and before `create_tool()` writes to disk. `docs/adr/ADR-013` corrected. Bug live-demonstrated pre-fix and the exact fix verified live, post-fix, inside the real container. Full isolated-worker execution explicitly deferred, tracked as `ISS-008`. See `specs/004-fix-skill-tool-approval-gate/`. |
