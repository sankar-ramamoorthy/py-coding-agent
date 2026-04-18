• Architectural Summary

  This system is a Dockerized Python coding agent built around a small core loop, a sandboxed execution model, and a growing separation between reasoning and execution.

  At the core, the agent follows a pi-mono-style minimal loop: user message -> LLM decides whether to answer or act -> runtime executes -> result returns to the loop. The design goal is to keep orchestration
  simple and let the model drive decisions, while the runtime enforces safety and boundaries.

  Key Decisions

  - Sandbox-first execution
      - All file access is intended to stay inside /workspace.
      - Tools must resolve paths safely, return LLM-friendly strings, and avoid unsafe shell patterns.
      - Dynamic tools are allowed, but they must follow the same safe template and are hot-loaded into the running agent.
  - Provider-agnostic LLM layer
      - Internal conversation memory uses an OpenAI-style canonical format.
      - Provider-specific translation is pushed into adapters like OllamaProvider and LiteLLMProvider.
      - SessionManager and a provider registry isolate provider switching from agent logic.
      - Model selection is “tight-bound”: runtime /provider <name> <model> overrides env defaults for that session.
  - Docker + MCP microservice pattern
      - External capabilities are meant to be exposed as MCP services over HTTP, not custom REST or stdio wiring.
      - The agent wraps MCP calls behind the same Tool interface used for local tools, so the loop stays unchanged.
  - Skills architecture
      - The newer ADR direction splits the system into:
          - playbooks/ for reasoning guidance
          - orchestration for deciding what to execute
          - approved execution skills for side effects
      - Skills are versioned, status-gated (proposed, approved, deprecated), and may chain only to other approved skills.
      - Interactive skill scaffolding exists, but newly generated skills default to proposed.
  - Strict tool interface
      - Tools should be invoked via Tool.run(**kwargs), not by calling raw functions directly.
      - This creates a clear interception point for future validation, logging, retries, and permission checks.

  Key Constraints

  - Side effects should go through approved execution paths, not free-form LLM behavior.
  - Unapproved skills must not run.
  - Playbooks are reasoning-only and must not become executable workflows.
  - The runtime, not the LLM, is responsible for enforcing approval, validation, and sandbox boundaries.
  - Dependency management uses uv, with a hybrid lockfile strategy:
      - local uv lock for day-to-day work
      - container-resolved locks before releases or major merges

  Current Architectural Shape

  In practical terms, the system is evolving from a “tool-using chat loop” into a layered agent runtime:

  1. LLM reasoning guided by playbooks
  2. Structured orchestration that declares intent
  3. Deterministic skill/tool execution under policy and sandbox controls

  That layered separation is the main architectural throughline across the ADRs. The core tradeoff is deliberate: less ad hoc autonomy in exchange for reviewability, safer execution, and cleaner extension
  points.