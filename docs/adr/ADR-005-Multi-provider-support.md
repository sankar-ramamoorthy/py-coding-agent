# ADR-005: Multi-Provider LLM Support

**Status:** Proposed  
**Date:** 2026-03-22  
**Milestone:** 2 (Runtime + Infra)

---

## Context

In V1, the agent connects exclusively to a local **Ollama** instance via direct HTTP (`/api/chat`).
This is intentional for the default use case: a low-resource local machine with no external dependencies.

However, as the agent matures, users may want to:

- Use cloud LLM providers (OpenAI, Anthropic, Groq) for more capable models
- Switch providers via config without changing code
- Run the agent on machines without a local GPU or Ollama installation

The current `OllamaProvider` sends messages directly in Ollama wire format.
There is no abstraction layer to support other providers, and the internal memory format
in `agent.py` is currently Ollama-specific (missing `tool_calls` list structure, no `tool_call_id`).

Additionally, importing a large framework like LangChain to solve this is explicitly avoided
due to past experience with breaking version changes.

---

## Decision

### 1. Canonical Internal Memory Format

`agent.py` will store conversation memory in **OpenAI-style format** as the canonical internal representation.
No provider-specific format will appear in `agent.py`.

```python
# assistant tool call (canonical)
{
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {
            "id": "<uuid>",
            "type": "function",
            "function": {
                "name": "list_files",
                "arguments": {"path": "."}
            }
        }
    ]
}

# tool result (canonical)
{
    "role": "tool",
    "tool_call_id": "<uuid>",
    "content": "plain string result"
}
```

This format is chosen because:
- It is the most widely adopted standard
- Ollama is close to it already (minor translation needed)
- LiteLLM speaks it natively
- It keeps `agent.py` provider-agnostic

### 2. Provider Abstraction

Each provider implements `LLMProvider` from `llm/base.py`:

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: list, tools: list = None) -> dict:
        # always returns {"text": str | None, "tool_call": {...} | None}
        pass

    @abstractmethod
    def to_wire_messages(self, messages: list) -> list:
        # translates canonical memory format → provider wire format
        pass
```

`generate()` always receives canonical messages and always returns the normalized dict.
Translation to/from wire format is the provider's responsibility, not the agent's.

### 3. Two Providers

**`OllamaProvider` (default)**
- Direct HTTP to `localhost:11434` (or `host.docker.internal:11434` from Docker)
- No extra dependencies beyond `requests`
- Translates canonical → Ollama wire format in `to_wire_messages()`:
  - `content: None` → `content: ""`
  - strips `tool_call_id` from tool result messages
  - flattens `tool_calls` list to Ollama's expected shape

**`LiteLLMProvider` (optional)**
- Uses `litellm` package to support OpenAI, Anthropic, Groq, Together, Mistral, etc.
- Model selected via string: `"groq/llama3"`, `"anthropic/claude-3-5-haiku"`, `"openai/gpt-4o"`
- `to_wire_messages()` is a near no-op since LiteLLM speaks OpenAI natively
- Only loaded if `LLM_PROVIDER=litellm` in environment

### 4. Provider Selection via Config

`config.py` reads `LLM_PROVIDER` from environment:

```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" | "litellm"
```

`main.py` selects the provider at startup:

```python
if LLM_PROVIDER == "litellm":
    from py_mono.llm.litellm_provider import LiteLLMProvider
    llm = LiteLLMProvider()
else:
    from py_mono.llm.ollama_provider import OllamaProvider
    llm = OllamaProvider()
```

This keeps `litellm` as a soft dependency — it is never imported unless explicitly configured.

### 5. Optional Dependency in pyproject.toml

```toml
[project]
dependencies = [
    "requests",   # Ollama only — default, no extras needed
]

[project.optional-dependencies]
litellm = ["litellm"]
```

Install for Ollama only (default):
```
pip install py-coding-agent
```

Install with cloud provider support:
```
pip install py-coding-agent[litellm]
```

---

## Consequences

**Benefits:**
- Agent core (`agent.py`) is fully provider-agnostic
- Ollama remains zero-extra-dependency default
- Cloud providers available on demand via LiteLLM without writing per-provider adapters
- Canonical format future-proofs memory management and MCP-Server work (ADR-004)
- Avoids LangChain and its version fragility

**Trade-offs:**
- `to_wire_messages()` must be kept in sync if Ollama changes its API
- LiteLLM is a third-party dependency with its own version risk (mitigated by pinning)
- API keys for cloud providers must be managed via environment variables

---

## Alternatives Considered

- **LangChain**: Rejected due to past version breakage experience and unnecessary complexity for this use case.
- **Per-provider adapters without LiteLLM**: More control but significant maintenance burden as providers evolve.
- **Ollama-only forever**: Simple but limits the agent to local hardware capabilities.

---

## Related ADRs

- ADR-003: Pi-Mono Style Minimal Agent Loop — provider abstraction must not complicate the loop
- ADR-004: MCP-Server — canonical message format established here will be reused there

---

## Files Affected (when implemented)

| File | Change |
|---|---|
| `py_mono/agent/agent.py` | Adopt canonical message format |
| `py_mono/llm/base.py` | Add `to_wire_messages()` abstract method |
| `py_mono/llm/ollama_provider.py` | Implement `to_wire_messages()`, fix wire format |
| `py_mono/llm/litellm_provider.py` | New file |
| `py_mono/config.py` | Add `LLM_PROVIDER` switching logic |
| `py_mono/main.py` | Provider selection at startup |
| `pyproject.toml` | Add optional `litellm` extra |