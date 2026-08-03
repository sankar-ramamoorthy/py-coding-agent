# Quickstart: Dual Ollama Backend Selection

Validation scenarios proving the feature works end-to-end. See `data-model.md` for the
resolution rules and `contracts/provider-selection.md` for the full CLI/`get_provider`
contract.

## Prerequisites

- Repo checked out on `ollama-dual-backend` after `/speckit-implement` has landed the code.
- Remote Ollama reachable at `http://100.105.24.12:11434` (Tailscale connected) for the
  "real remote" scenarios; local Ollama running for the "real local" scenarios.

## Automated (mocked, no real network) — run first

```
uv run pytest tests/llm/ tests/session/ -v
```
**Expected**: all pass. Confirms, without any real network dependency: explicit
`ollama-remote`/`ollama-local` resolution, model override, bare `ollama` regression
(unchanged), and `ollama-auto`'s fallback logic in both the reachable and unreachable cases
(mocked `is_ollama_reachable`).

## Scenario 1: Remote preferred by default (SC-001)

```
docker compose run --rm py-coding-agent python -m py_mono.main
```
With `LLM_PROVIDER` unset (fresh `.env` from `.env.example`) and the remote backend
reachable: send a chat message with no `/provider` command first.

**Expected**: response returns using the remote backend's default model (`qwen3.5:4b` unless
overridden) — confirm via `/providers` output or by comparing response characteristics
against Scenario 3 below (different model families).

## Scenario 2: Automatic fallback when remote is unreachable (SC-002)

Temporarily set `OLLAMA_REMOTE_URL` to an unreachable address (or stop the remote Ollama
service), then repeat Scenario 1 with no explicit `/provider` command.

**Expected**: the session starts on the local backend within ~2 seconds (the probe timeout),
with no error surfaced for the fallback itself — a real chat message is answered using the
local backend's default model (`Qwen3:4b`).

## Scenario 3: Explicit backend override (SC-003)

```
/provider ollama-remote
```
then, in a separate run:
```
/provider ollama-local
```
**Expected**: each command switches to the named backend immediately, regardless of which
one Scenario 1/2 would have auto-selected; a chat message afterward is answered by the
explicitly-chosen backend.

## Scenario 4: Explicit selection of an unreachable backend fails loudly (FR-004)

```
/provider ollama-remote
```
with the remote backend deliberately made unreachable.

**Expected**: a direct connection error is shown — the session does NOT silently fall back
to local (distinguishes this from `ollama-auto`'s behavior in Scenario 2).

## Scenario 5: Model override in one action (SC-004)

```
/provider ollama-remote qwen3:4b
```
**Expected**: the remote backend is used with `qwen3:4b` instead of its configured default
(`qwen3.5:4b`) — distinguishable since they're different model families. Then:
```
/provider ollama-remote
```
(no model given) **Expected**: reverts to the remote backend's configured default
(`qwen3.5:4b`), proving the override didn't persist as a new default.

## Scenario 6: Backward compatibility (SC-005)

With `LLM_PROVIDER=ollama` explicitly set (not `ollama-auto`):

**Expected**: behavior is byte-for-byte identical to before this feature — single backend
via `OLLAMA_BASE_URL`/`OLLAMA_MODEL`, no probing, no fallback, regardless of remote
reachability.

## Repo-level regression checks

```
python -m compileall -q py_mono
pytest
```
**Expected**: all pass; nothing outside the files listed in `plan.md`'s Project Structure
changed behavior.
