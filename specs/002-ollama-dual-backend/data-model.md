# Phase 1 Data Model: Dual Ollama Backend Selection

## Backend

A named Ollama endpoint configuration. Not a persisted/DB entity — resolved at runtime from
environment variables via a small dispatch table in `provider_registry.py`.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `name` | string | registry key | one of `ollama-remote`, `ollama-local` (also the resolution targets for `ollama-auto`) |
| `base_url_env` | string | code constant | env var name providing the URL override |
| `base_url_default` | string | code constant | fallback URL if env var unset |
| `model_env` | string | code constant | env var name providing the default-model override |
| `model_default` | string | code constant | fallback default model if env var unset |

Concrete values:

| `name` | `base_url_env` | `base_url_default` | `model_env` | `model_default` |
|---|---|---|---|---|
| `ollama-remote` | `OLLAMA_REMOTE_URL` | `http://100.105.24.12:11434` | `OLLAMA_REMOTE_MODEL` | `qwen3.5:4b` |
| `ollama-local` | `OLLAMA_LOCAL_URL` | `http://host.docker.internal:11434` | `OLLAMA_LOCAL_MODEL` | `Qwen3:4b` |

`ollama` (bare) is not part of this table — it continues to resolve exclusively via the
pre-existing `OLLAMA_BASE_URL`/`OLLAMA_MODEL` env vars, untouched.

## Provider selection

The resolved outcome of a `get_provider(name, model, api_key)` call for an Ollama-family
name — an ephemeral, in-memory `OllamaProvider` instance, not a stored entity.

| Field | Type | Rule |
|-------|------|------|
| `resolved_name` | string | For `ollama-auto`: `ollama-remote` if reachable, else `ollama-local`. For explicit names: unchanged. |
| `base_url` | string | `os.getenv(backend.base_url_env, backend.base_url_default)` |
| `model_name` | string | explicit `model` argument if given, else `os.getenv(backend.model_env, backend.model_default)` |

## Reachability check (not a stored entity — a point-in-time function result)

`is_ollama_reachable(base_url: str, timeout: float = 2.0) -> bool`

| Input | Output | Rule |
|---|---|---|
| `base_url` reachable, `GET {base_url}/api/tags` returns 2xx | `True` | — |
| any `requests.RequestException` (timeout, connection refused, DNS failure, etc.) | `False` | caught, never raised |
| non-2xx response | `False` | `resp.ok` is `False` |

Called exactly once per `ollama-auto` resolution (session start or explicit switch to
`ollama-auto`) — never per chat turn, never for `ollama-remote`/`ollama-local`/`ollama`.

## State transitions (session provider state)

```text
[SessionManager constructed, default_provider = LLM_PROVIDER env value]
        │
        ▼
[_resolve_provider(name, model) called once at construction]
        │  if name == "ollama-auto": probe remote, resolve to ollama-remote or ollama-local
        ▼
[self.provider = OllamaProvider(base_url=..., model_name=...)]
        │
        │  user runs "/provider <name> <model>" at any point
        ▼
[switch_provider(name, model) → _resolve_provider(name, model) again, replaces self.provider]
```

No mid-session automatic re-probing — a session's active backend only changes via an
explicit `/provider` command, never automatically after construction (per spec's Edge Cases
section, this is an intentional scope boundary, not a gap).
