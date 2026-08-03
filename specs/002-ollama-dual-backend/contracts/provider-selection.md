# Contract: Provider selection (`/provider` command + `get_provider`)

This feature's only user-facing interface is the pre-existing `/provider`/`/providers`
CLI commands (unchanged code, newly-meaningful inputs) and, at the code level,
`py_mono.llm.provider_registry.get_provider`. This documents the contract both surfaces
must honor.

## CLI surface (unchanged code — `py_mono/agent/agent.py`)

```
/providers
```
Lists all `REGISTRY` keys. After this feature: `ollama`, `ollama-remote`, `ollama-local`,
`ollama-auto`, `litellm` (five, up from two).

```
/provider <name> [<model>]
```
- `<name>` MUST be a key in `REGISTRY`, else a clear "Unknown provider" error listing valid
  keys (unchanged existing behavior).
- `<model>`, if given, overrides that backend's configured default model for this
  selection only — does not persist as the new default for subsequent selections.

## `get_provider(name, model=None, api_key=None) -> LLMProvider` contract

| `name` | Behavior |
|---|---|
| `"ollama"` | Unchanged: `OllamaProvider(model_name=model or os.getenv("OLLAMA_MODEL", ...), api_key=api_key)`, `base_url` from `OLLAMA_BASE_URL` env var inside the provider itself. |
| `"ollama-remote"` | `OllamaProvider(model_name=model or os.getenv("OLLAMA_REMOTE_MODEL", "qwen3.5:4b"), api_key=api_key, base_url=os.getenv("OLLAMA_REMOTE_URL", "http://100.105.24.12:11434"))`. Never probes; connection failures surface directly. |
| `"ollama-local"` | Same shape, using `OLLAMA_LOCAL_MODEL`/`OLLAMA_LOCAL_URL` (defaults `Qwen3:4b` / `http://host.docker.internal:11434`). Never probes. |
| `"ollama-auto"` | Probes `is_ollama_reachable(remote_url)` once; resolves to the `ollama-remote` construction path if `True`, else the `ollama-local` path. The probe itself never raises — a probe failure means "resolve to local," not an error. |
| `"litellm"` | Unchanged. |
| anything else | `raise ValueError(f"Unknown provider: {name}. Available: {list(REGISTRY.keys())}")` — unchanged existing behavior, just a longer `Available` list. |

## Stability

- `is_ollama_reachable`'s exact timeout value (2.0s) is an implementation detail, not part
  of this contract — callers must not depend on the exact duration, only on the fact that
  it returns within a short, bounded time and never raises.
- The five `REGISTRY` key names (`ollama`, `ollama-remote`, `ollama-local`, `ollama-auto`,
  `litellm`) ARE the stable contract — a script or user muscle-memory keying off `/provider
  ollama-remote` should keep working across future internal refactors of how that name
  resolves internally.
