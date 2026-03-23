# ADR-006: Provider Registry, Session Management, and Key Management

**Status:** Proposed
**Date:** 2026-03-22
**Milestone:** 3

---

## Context

The initial multi-provider implementation (ADR-005) uses environment variables to select
a provider at container startup. This is sufficient for Milestone 2 but has limitations:

- Provider is locked at startup, not switchable at runtime
- API keys must be in environment variables or Docker env, not user-manageable
- No session-level provider state
- Agent code would need to know about specific providers if not abstracted properly

As the agent matures, users will want to:
- Switch providers mid-session (`/provider groq`)
- Use a provider for a single task only (temporary override)
- Manage their own API keys securely without editing env files
- Have the system route to the right provider automatically based on task type

---

## Decision

### 1. Provider Registry

Replace hardcoded `if/else` provider selection with a registry pattern:

```python
# py_mono/llm/provider_registry.py

REGISTRY = {
    "ollama": OllamaProvider,
    "groq": LiteLLMProvider,      # model=groq/llama-3.3-70b-versatile
    "openai": LiteLLMProvider,    # model=openai/gpt-4o
    "anthropic": LiteLLMProvider, # model=anthropic/claude-3-5-haiku
    "gemini": LiteLLMProvider,    # model=gemini/gemini-pro
}

def get_provider(name: str, api_key: str = None) -> LLMProvider:
    cls = REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown provider: {name}. Available: {list(REGISTRY.keys())}")
    return cls(api_key=api_key)
```

New providers are added to the registry only — no changes to agent or session code.

### 2. Session Manager

A `SessionManager` holds per-session state including the active provider and API keys.
The agent never knows what provider it is using — it only calls `provider.generate()`.

```python
# py_mono/session/session_manager.py

class SessionManager:
    def __init__(self, default_provider="ollama"):
        self.provider_name = default_provider
        self.provider = get_provider(default_provider)
        self._override_provider = None  # temporary per-message override

    def switch_provider(self, name: str):
        """Permanently switch provider for this session."""
        self.provider_name = name
        self.provider = get_provider(name, api_key=key_manager.get(name))

    def use_provider_once(self, name: str):
        """Temporarily override provider for one request only."""
        self._override_provider = get_provider(name, api_key=key_manager.get(name))

    def get_active_provider(self) -> LLMProvider:
        if self._override_provider:
            p = self._override_provider
            self._override_provider = None  # reset after use
            return p
        return self.provider
```

### 3. Dynamic Switching Strategies

Three switching modes supported:

**Hard switch** — provider changes for all subsequent requests:
```
/provider groq
```

**Temporary override** — provider used for one request only:
```
use groq just for this task
```

**Smart routing (future)** — system decides automatically based on task type:

| Tier | Provider | Use case |
|---|---|---|
| local | Ollama | cheap, private tasks |
| fast cloud | Groq | fast reasoning, tool calling |
| high quality | Anthropic/OpenAI | complex multi-step tasks |
| long context | Gemini | large file analysis |

### 4. CLI Provider Commands

New special commands handled before the LLM loop:

```
/provider           → show current provider
/provider groq      → switch to groq for session
/providers          → list available providers
/key groq sk-abc    → store encrypted API key for groq
```

### 5. Key Management

API keys are managed by a `KeyManager` that:
- Never stores plaintext keys on disk
- Encrypts using Fernet symmetric encryption
- Stores encrypted blob in `/workspace/.keys.enc`
- Reads master key from `LLM_MASTER_KEY` environment variable
- Never logs keys even in DEBUG mode

```python
# py_mono/security/key_manager.py

from cryptography.fernet import Fernet
import json
import os
from pathlib import Path

KEYS_FILE = Path("/workspace/.keys.enc")

class KeyManager:
    def __init__(self):
        master_key = os.getenv("LLM_MASTER_KEY")
        if not master_key:
            raise RuntimeError("LLM_MASTER_KEY environment variable not set")
        self.fernet = Fernet(master_key.encode())
        self._keys = self._load()

    def _load(self) -> dict:
        if not KEYS_FILE.exists():
            return {}
        encrypted = KEYS_FILE.read_bytes()
        decrypted = self.fernet.decrypt(encrypted)
        return json.loads(decrypted)

    def _save(self):
        plaintext = json.dumps(self._keys).encode()
        encrypted = self.fernet.encrypt(plaintext)
        KEYS_FILE.write_bytes(encrypted)

    def set(self, provider: str, api_key: str):
        """Store an encrypted API key for a provider."""
        self._keys[provider] = api_key
        self._save()

    def get(self, provider: str) -> str | None:
        """Retrieve a decrypted API key for a provider."""
        return self._keys.get(provider)

    def has(self, provider: str) -> bool:
        return provider in self._keys
```

### 6. Key Resolution Order

```python
def resolve_key(provider: str, session: SessionManager) -> str | None:
    # 1. Session-level key (set via /key command)
    if key_manager.has(provider):
        return key_manager.get(provider)
    # 2. Environment variable fallback
    env_key = os.getenv(f"{provider.upper()}_API_KEY")
    if env_key:
        return env_key
    # 3. No key found
    return None
```

### 7. Security Rules

- `LLM_MASTER_KEY` stored in Windows env var (`setx LLM_MASTER_KEY "..."`) — never in repo
- `/workspace/.keys.enc` added to `.gitignore`
- Keys never appear in debug logs — `KeyManager` overrides `__repr__` and `__str__`
- Master key never stored in `/workspace`
- Entire JSON blob encrypted (not per-value) for cleaner storage

---

## Consequences

**Benefits:**
- Agent code stays completely provider-agnostic
- New providers added to registry only — no other code changes
- Users can manage keys at runtime without restarting the container
- Session state survives across queries within a container run
- Foundation for smart routing in future milestones

**Trade-offs:**
- `SessionManager` adds complexity vs simple env var approach
- `KeyManager` requires `LLM_MASTER_KEY` to be set — extra setup step for new users
- Fernet encryption is simple but not enterprise-grade (sufficient for personal/team use)

---

## Alternatives Considered

- **Env vars only**: Simple but not runtime-switchable, keys require container restart
- **Plaintext key file**: Easy but unacceptable security risk
- **External secret manager (Vault, AWS)**: Too complex for current scope, noted for future
- **Per-value encryption**: Less clean than encrypting entire blob

---

## Common Mistakes to Avoid

- ❌ Putting `LLM_MASTER_KEY` in the repo
- ❌ Storing master key in `/workspace`
- ❌ Logging API keys in DEBUG output
- ❌ Storing plaintext keys anywhere on disk
- ❌ Hardcoding provider names in agent or session code

---

## Files to Create (when implemented)

| File | Purpose |
|---|---|
| `py_mono/llm/provider_registry.py` | Provider registry and factory |
| `py_mono/session/session_manager.py` | Per-session provider and state management |
| `py_mono/security/key_manager.py` | Encrypted API key storage and retrieval |
| `py_mono/security/__init__.py` | Module init |
| `py_mono/session/__init__.py` | Module init |

## Files to Modify (when implemented)

| File | Change |
|---|---|
| `py_mono/main.py` | Use SessionManager instead of direct provider init |
| `py_mono/agent/agent.py` | Accept provider via session, not direct injection |
| `py_mono/ui/cli.py` | Handle `/provider`, `/providers`, `/key` commands |
| `pyproject.toml` | Add `cryptography` dependency |
| `.gitignore` | Add `/workspace/.keys.enc` |

---

## Related ADRs

- ADR-005: Multi-Provider LLM Support — this ADR extends ADR-005
- ADR-003: Pi-Mono Minimal Loop — agent must remain provider-agnostic
- ADR-004: MCP Server — session manager may eventually delegate to MCP server