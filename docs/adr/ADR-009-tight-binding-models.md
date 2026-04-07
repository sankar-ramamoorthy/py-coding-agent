# ADR‑009: Tight‑binding model names in LLM providers

## Status

Proposed

## Context

We want users to be able to switch not just the **LLM provider** at runtime (e.g. `/provider litellm`), but also the **model name** bound to that provider (e.g. `/provider ollama granite4:350m`).

Two options were considered:

- `env‑only`: only environment variables (`OLLAMA_MODEL`, `LITELLM_MODEL`) control the model; `/provider ... model` only gives a hint.  
- `tight‑binding`: the model name is passed into the `LLMProvider` instance itself and overrides any default taken from env.

We chose **tight‑binding**.

## Decision

We will:

- Extend `LLMProvider` to accept an optional `model_name: str` at construction.  
- Make `OllamaProvider` and `LiteLLMProvider` interpret `model_name` as the primary model specifier, using env only as a default.  
- Let `provider_registry.get_provider(name, model)` pass `model` into the provider class.  
- Make `SessionManager.switch_provider(name, model)` and `use_provider_once(name, model)` carry the model along with the provider.  
- Allow the CLI to override the model via:
  - `/provider ollama granite4:350m`  
  - `/provider litellm groq/qwen/qwen3-32b`  

This means:

- `/provider` commands are **truthful**: the agent really uses the stated model.  
- Model choice is **per‑session** rather than per‑environment.

## Consequences

**Pros**

- Clear UX: `/provider ollama granite4:350m` immediately switches to that model without requiring env edits.  
- Supports future “one‑off” commands like `/provider once litellm groq/qwen/qwen3-32b`.  

**Cons**

- More constructor wiring (`model_name` must be threaded through providers).  
- Two sources of truth: env vs CLI‑provided model; we resolve this by:
  - **CLI‑provided model wins**.
  - env is the fallback.
