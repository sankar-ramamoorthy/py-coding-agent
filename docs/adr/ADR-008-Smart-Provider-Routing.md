Here’s a new **ADR‑008** that builds directly on **ADR‑005** (multi‑provider) and **ADR‑006** (session‑level provider switching) and defines a **smart provider‑routing pattern** where the agent can route tasks automatically to Ollama, Groq, Anthropic, etc.

Save this as:

`docs/adr/ADR-008-Smart-Provider-Routing.md`

***

### ADR‑008: Smart Provider Routing by Task Type

**Status:** Proposed  
**Date:** 2026‑03‑27  
**Milestone:** 3  
**Related ADRs:**  
- ADR‑005: Multi‑Provider LLM Support  
- ADR‑006: Provider Registry, Session Management, and Key Management  
- ADR‑003: Pi‑Mono Minimal Agent Loop  

***

## Context

With ADR‑005 and ADR‑006 in place, users can already:

- Switch between `ollama`, `litellm‑grov`, `litellm‑openai`, etc.  
- Have a session‑level active provider and even per‑request overrides.

However, this still requires **manual routing**:

- `/provider groq`  
- `use anthropic just for this task`  

This is great for experimentation, but as use‑cases grow, the agent should be able to **decide** which provider is most appropriate based on task category.

Example:

- **Local / cheap, private tasks** → `ollama`  
- **Fast, low‑latency execution** (tool calling, small reasoning) → `groq`  
- **Large‑context analysis** (big files) → `gemini`  
- **High‑quality reasoning / complex planning** → `anthropic` / `openai`

Today, that routing lives in the user’s head; we want to push it into the agent.

***

## Decision

We adopt a **smart routing layer** that:

- Stays **behind** the `SessionManager` and `ProviderRegistry`.  
- Lets the agent keep calling `provider.generate(...)` without knowing the underlying routing.  
- Supports **three routing modes**:

  1. **Hard‑coded heuristics** (`routing_type: "heuristic"`)  
  2. **User‑forced provider** (`/use groq for this task`)  
  3. **Future LLM‑based scorer** (`routing_type: "scored"`)

### 1. Routing Layer Design

Introduce a `ProviderRouter` that sits between `SessionManager` and `ProviderRegistry`:

```python
from typing import Dict, Any, List


class ProviderRouter:
    """Smartly choose which provider to use for a request."""

    def __init__(
        self,
        registry: Dict[str, Any],  # { name: cls } from ADR‑006
        routing_type: str = "heuristic"  # "heuristic", "fixed", "scored"
    ):
        self.registry = registry
        self.routing_type = routing_type
        self.default_provider = "ollama"  # local default

    def pick_provider(
        self,
        session_name: str,
        task_type: str,
        tools: List[Dict[str, Any]] = None,
        context_size_hint: int = 0,
        latency_budget: float = 0.0,
    ) -> str:
        """
        Decide which provider name to use for this request.
        """
        raise NotImplementedError


class HeuristicRouter(ProviderRouter):
    def pick_provider(
        self,
        session_name: str,
        task_type: str,
        tools: List[Dict[str, Any]] = None,
        context_size_hint: int = 0,
        latency_budget: float = 0.0,
    ) -> str:
        # Examples:
        if "file" in task_type.lower() or "big" in task_type.lower():
            return "gemini"  # large‑context
        if tools and context_size_hint < 10000:
            return "groq"    # fast tool calls
        if "plan" in task_type.lower() or "reason" in task_type.lower():
            return "anthropic"
        return self.default_provider  # "ollama"
```

`SessionManager` can now optionally wrap a `ProviderRouter`:

```python
class SessionManager:
    def __init__(
        self,
        default_provider="ollama",
        router: ProviderRouter = None
    ):
        self.default_provider = default_provider
        self.router = router
        # ...

    def get_active_provider(self) -> LLMProvider:
        if self._override_provider:
            p = self._override_provider
            self._override_provider = None
            return p
        if self.router:
            # Infer task type or let caller pass it
            task_type = self._infer_task_type_from_last_user_message()
            provider_name = self.router.pick_provider(
                session_name=self.id,
                task_type=task_type
            )
            return get_provider(provider_name)
        return self.provider
```

***

### 2. Routing Modes

| Mode | Description | When to use |
|---|---|---|
| `heuristic` | Rules‑based (task type, tools, context size) | Now, Milestone 3 |
| `fixed` | Always use `default_provider` | Local‑only dev / “no routing” |
| `scored` (future) | Use an LLM or scoring model to rank providers | When we add model‑aware cost/latency metadata |

### 3. Task‑Type Taxonomy (Heuristic)

Example categories (can be annotated in `ToolSpec` or inferred from user query):

| Task type | Example prompt | Best provider |
|---|---|---|
| `tools` | “Run this shell command”, “Call `list_files`” | `groq` (fast, low‑latency) |
| `local` | Any request that can be done on‑device | `ollama` (private, free) |
| `long_context` | “Read this large CSV”, “Analyze log files” | `gemini` |
| `planning` | “Plan a multi‑step project” | `anthropic` / `gpt‑4o` |
| `coding` | “Write a Python script” | `gpt‑4o` / `gemma‑3‑27b` |

The heuristic router can start with a small, additive ruleset and grow over time.

***

### 4. CLI / Semantic Commands

New natural‑language / CLI forms that respect routing:

```
# User‑forced (bypasses routing)
use groq just for this task
use anthropic for this task

# Let routing decide
run this fast
plan this project
analyze this big file
```

`SessionManager` parses these into `task_type` tags and hands them to `ProviderRouter`.

***

### 5. Session‑Level vs Request‑Level

- **Session‑level preference** (from ADR‑006):  
  - `provider = <name>` still defines the “default” if routing is disabled or falls back.
- **Request‑level**:
  - `ProviderRouter` can override it for a single request (`groq` for tools, `ollama` for follow‑ups).

This keeps routing composable and not global.

***

### 6. Configuration

In `config.py` or `.env`:

```python
ROUTING_TYPE = os.getenv("ROUTING_TYPE", "heuristic")  # "heuristic", "fixed", "scored"
DEFAULT_ROUTING_PROVIDER = "ollama"
```

Later in `main.py`:

```python
router = None
if ROUTING_TYPE == "heuristic":
    router = HeuristicRouter(
        registry=REGISTRY,
        routing_type=ROUTING_TYPE
    )

session_manager = SessionManager(
    default_provider="ollama",
    router=router
)
```

***

## Consequences

### Benefits

- Agent remains fully provider‑agnostic; routing is an extra layer you can disable.  
- Users can say things like `run this fast` and get automatically routed to `groq`.  
- Foundation for **cost‑aware** and **quality‑aware** routing in the future.  
- Extensible architecture: adding a new task type or provider only touches the router, not core agent logic.

### Trade‑offs

- Adds another abstraction (`ProviderRouter`) and a small cognitive load.  
- Heuristics can be brittle if not tuned to actual model behavior; will need iteration.  
- Requires `task_type` inference or tagging, which can be noisy from natural language.

***

## Alternatives Considered

- **No routing, only manual /provider**:  
  - Simpler, but forces user to remember which provider is best for which task.  
- **Hardcoded mapping in `agent.py`**:  
  - Ties routing to core loop logic, violating ADR‑005’s “provider‑agnostic agent” goal.  
- **Full LLM‑based scorer from day‑one**:  
  - Overkill for Milestone 3; heuristics plus a `scored` hook is lighter.

***

## Common Mistakes to Avoid

- ❌ Hardcoding concrete provider names like `"groq"` inside `agent.py` instead of routing layer.  
- ❌ Letting routing decide provider without a way for the user to force‑override (e.g., `use groq`).  
- ❌ Coupling routing decisions to specific model names (`"llama3‑70b"`) instead of task‑size categories.

***

## Files to Create / Modify

| File | Purpose |
|---|---|
| `py_mono/routing/provider_router.py` | `ProviderRouter` and `HeuristicRouter` base types |
| `py_mono/routing/heuristic_router.py` | Heuristic rules, `pick_provider` implementation |
| `py_mono/session/session_manager.py` | Add `router` optional parameter and integrate routing |
| `py_mono/agent/agent.py` | No change; routing is hidden behind `SessionManager` |
| `py_mono/main.py` | Construct `router` and pass it into `SessionManager` |
| `pyproject.toml` (future) | Optional deps for scoring / cost‑estimation (if `routing_type="scored"`) |

***

This ADR pairs cleanly with ADR‑005 (multi‑provider) and ADR‑006 (session‑level switching) and gives a **clear, incremental path** toward “smart routing” 