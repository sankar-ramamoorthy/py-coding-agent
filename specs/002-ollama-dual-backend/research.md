# Phase 0 Research: Dual Ollama Backend Selection

No `NEEDS CLARIFICATION` markers remained in the Technical Context — the prior planning
conversation with the user already resolved the open design questions. This file records
the decisions and rejected alternatives for the record, per Spec Kit's Phase 0 convention.

## Decision: Registry-based backend selection vs. a config-file/proxy layer

**Decision**: Extend `py_mono/llm/provider_registry.py`'s existing `REGISTRY` dict with
`ollama-remote`/`ollama-local`/`ollama-auto` entries, all still instantiating the existing
`OllamaProvider` class.

**Rationale**: `agent.py`'s `/provider <name> <model>` command already validates names
against `REGISTRY` and threads an optional model through to `get_provider` — confirmed by
reading the live code. Any new `REGISTRY` key is therefore automatically switchable and
listed via `/providers` with zero changes to command-dispatch code, satisfying the
constraint against touching `agent.py`. A standalone LiteLLM proxy server (considered in an
earlier, since-corrected draft of this idea) would require running and supervising a
separate process this repo has no existing infrastructure for, and would not reuse any of
the `SessionManager`/`REGISTRY` machinery already in place.

**Alternatives considered**:
- *A standalone LiteLLM proxy (`litellm --config ... --port 4000`)* — rejected: no such
  process/infrastructure exists anywhere in this repo; `LiteLLMProvider` here calls
  `litellm.completion()` directly as an SDK call. Introducing a proxy would be a new
  operational dependency (a service to keep running) for no benefit over extending the
  registry that already exists.
- *A new, separate provider class per backend (e.g. `RemoteOllamaProvider`,
  `LocalOllamaProvider`)* — rejected: `OllamaProvider`'s only backend-specific state is
  `base_url` and `model_name`, both already constructor-parameterizable with one small
  addition; subclassing would duplicate `generate()`/`to_wire_messages()` for no reason.

## Decision: Bare `ollama` stays frozen; new `ollama-auto` carries the fallback behavior

**Decision**: `ollama` (bare) keeps its exact current behavior (reads `OLLAMA_BASE_URL`/
`OLLAMA_MODEL`, no probing, no fallback). A new `ollama-auto` entry carries "prefer remote,
fall back to local," and becomes the new effective default via `LLM_PROVIDER`.

**Rationale**: Confirmed directly with the user (this was the explicit decision point
flagged for sign-off). Freezing `ollama`'s meaning is fully backward compatible — anyone
with `LLM_PROVIDER=ollama` already set in their own `.env` sees zero behavioral change.
Only new installs (or anyone who updates their `.env` from the new `.env.example`) get the
new remote-preferred default.

**Alternatives considered**:
- *Redefine bare `ollama` itself to mean auto-with-fallback* — rejected by the user:
  silently changes an existing, already-documented environment value's meaning for anyone
  already relying on it, with no opt-out.

## Decision: One-time reachability probe, not continuous monitoring

**Decision**: `is_ollama_reachable(base_url, timeout=2.0)` — a single `GET {base_url}/api/tags`
call with a short timeout, called only when `ollama-auto` is resolved (session start or an
explicit switch to `ollama-auto`), never per-request and never for explicit
`ollama-remote`/`ollama-local`/`ollama` selections.

**Rationale**: `requests` is already a direct dependency (confirmed in `pyproject.toml`) —
no new dependency needed. `/api/tags` is a lightweight, already-used Ollama endpoint
(confirmed reachable on both backends during planning). A 2-second timeout is enough to
distinguish "refused/unreachable" from "present but momentarily slow" without a noticeable
hang before falling back — this only runs once per selection, not per chat turn, so the
cost is bounded and infrequent.

**Alternatives considered**:
- *Continuous background health-checking* — rejected: adds an ongoing background task/thread
  for a problem that only needs to be resolved once at selection time; out of proportion to
  the actual requirement (the spec explicitly scopes reachability determination to
  selection time, not continuous monitoring, per its Edge Cases section).
- *No probe at all — always try remote first per-request, catch failures and retry local* —
  rejected: would silently retry on every single request rather than resolving the backend
  once per selection, adding latency and complexity to the hot path (`generate()`) instead
  of the cold path (provider resolution).

## Decision: Env var naming

**Decision**: `OLLAMA_REMOTE_URL`, `OLLAMA_REMOTE_MODEL`, `OLLAMA_LOCAL_URL`,
`OLLAMA_LOCAL_MODEL` — paired URL/model naming per backend, consistent with the existing
`OLLAMA_BASE_URL`/`OLLAMA_MODEL` naming convention (just namespaced by backend).

**Rationale**: Matches the existing single-backend naming pattern exactly, just prefixed by
backend name, making the relationship between the four new vars and the two existing ones
obvious at a glance. `OLLAMA_LOCAL_URL`'s default must remain
`http://host.docker.internal:11434` (not `localhost`) since the agent runs inside a Docker
container and needs the Docker-to-host routing alias — confirmed by reading
`docker-compose.yml`'s existing hardcoded value for the same purpose today.

**Alternatives considered**:
- *A single `OLLAMA_BACKENDS` JSON/YAML blob env var* — rejected: inconsistent with this
  repo's existing one-value-per-env-var convention (confirmed in `config.py`); harder to
  override a single field (e.g. just the remote model) without restating the whole blob.
