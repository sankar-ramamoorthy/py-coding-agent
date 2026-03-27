
### File: `docs/adr/ADR-007-Dependency-Locking-Strategy.md`

```markdown
# ADR-007: Dependency Locking Strategy (Option A vs Option B)

**Status:** Proposed  
**Date:** 2026-03-26  
**Milestone:** 3  
**Related ADRs:**  
- ADR‑005: Multi‑Provider LLM Support  
- ADR‑006: Provider Registry, Session Management, and Key Management  

---

## Context

The project now uses `uv` as the packaging and dependency tool:

- `pyproject.toml` defines direct dependencies for the agent and the `datetime‑mcp` server.  
- `uv.lock` captures the exact locked transitive closure of these dependencies.  
- Dependency installation in Docker images happens via `uv sync --no-dev --no-editable` from the lockfile.

When `uv.lock` is updated, there are two main workflows:

- **Option A – `uv lock` on the host**  
  Run `uv lock` directly on the developer’s machine (Windows or macOS), then commit `uv.lock` and build images with `uv sync --frozen`.

- **Option B – `uv lock` inside Docker**  
  Run `docker compose run py‑coding‑agent uv lock` in a Linux container, commit the resulting `uv.lock`, and build images with `uv sync --frozen`.

The choice affects:
- Development speed on slower machines.
- Reproducibility across platforms (Windows, macOS, Linux).
- Alignment between dev and production environments.

---

## Decision

We adopt a **hybrid strategy**:

- **Default dev workflow: Option A**  
  Developers run `uv lock` locally on their host for fast iteration.  
  This is optimized for usability on slower machines where container startup is expensive.

- **Gold‑standard lock resolution: Option B**  
  Before releases, major feature merges, or CI‑controlled locks, dependency resolution happens inside the Docker container via `docker compose run ... uv lock`.  
  This guarantees that `uv.lock` is resolved in the same Linux environment as production.

This gives:

- Fast local iterations via Option A.  
- Strong reproducibility and cross‑platform consistency via Option B at key points.

---

## Option A – `uv lock` on the host

Run `uv lock` on the developer’s host OS (Windows/macOS):

```bash
# In project root
uv lock

# In mcp_servers/datetime
cd mcp_servers/datetime
uv lock
```

### Pros

- **Fast iteration**: no Docker overhead; `uv lock` completes in seconds on the host.  
- **Simple workflow**: every developer can update dependencies without thinking about containers.  
- **Good enough for most packages**: standard PyPI‑published wheels are platform‑independent or provide universal‑wheel‑like behavior, so macOS/Windows resolves correctly for Linux.  
- **Small team‑friendly**: low friction, no extra commands beyond `uv lock && git add uv.lock`.

### Cons

- Lockfile is resolved on the host OS, not in the production Linux environment.  
  - In rare cases, this can lead to slight platform‑specific choices (e.g., native wheels, build‑flag sensitivity) that differ from Docker‑resolved locks.  
- Less “officially reproducible” story for CI and production, since developers may never lock inside Docker.

---

## Option B – `uv lock` inside Docker

Resolve dependencies inside the runtime environment:

```bash
# In project root
docker compose run --rm py-coding-agent uv lock

# In mcp_servers/datetime
cd mcp_servers/datetime
docker compose run --rm datetime-mcp uv lock
```

### Pros

- **Maximum reproducibility**: `uv.lock` is always resolved in the same Linux container as the runtime image, exactly matching production.  
- **Strong cross‑platform story**: macOS and Windows developers can still clone and run the project; locks are built by Linux, not their local OS.  
- **CI‑friendly**: Jenkins/GitHub Actions only need to run `docker compose run ... uv lock` once per dependency change, then reuse the lockfile for builds.

### Cons

- **Slower feedback loop**: every lock update requires starting a container.  
  - On slower machines, this overhead is noticeable.  
- **Higher cognitive load**: developers must remember a different command than `uv lock` on the host.  
- **Tight coupling to Docker**: hard to use the same workflow outside of Docker‑based setups.

---

## How Both Options Are Used Together

### 1. Day‑to‑day development (Option A)

Developers:

- Ensure `uv` is installed on their host.  
- Edit `pyproject.toml` (or `mcp_servers/datetime/pyproject.toml`).  
- Run:

  ```bash
  uv lock
  docker compose up
  ```

- This is the default workflow for feature work and bugfixing.

### 2. Release‑quality lockfiles (Option B)

Before a major release or environment‑sensitive change:

- Run in the project root:

  ```bash
  docker compose run --rm py-coding-agent uv lock
  git add uv.lock
  git commit -m "Lock deps with Linux‑resolved uv.lock"
  ```

- Similarly, lock `mcp_servers/datetime` if needed:

  ```bash
  cd mcp_servers/datetime
  docker compose run --rm datetime-mcp uv lock
  git add uv.lock
  ```

- CI pipelines then use `uv sync --frozen` and never re‑resolve dependencies.

This gives:
- Fast iteration on the host (Option A).  
- Production‑grade, Linux‑resolved locks (Option B) at critical points.

---

## Consequences

### Benefits

- **Fast local development** thanks to Option A, especially on slower machines.  
- **Strong reproducibility and cross‑platform support** via Option B when it matters.  
- **Flexible for different contributors**:  
  - New users can just `git clone && docker compose up`.  
  - Power users can update locks locally or inside Docker as they prefer.  
- **Matches uv best practices**: lock once, then install with `uv sync --frozen` in Docker builds.

### Trade‑offs

- Developers must understand two slightly different workflows (`uv lock` vs `docker compose run ... uv lock`).  
- If contributors forget to run Option B before a release, there is a small risk that the lockfile is not as tightly aligned with production.  
- Documentation overhead: the project must clearly document both patterns.

---

## Alternatives Considered

- **Only Option A forever**  
  Pros: uniform, simple, fast.  
  Cons: less confidence in lockfile reproducibility between local dev and Linux‑only production.

- **Only Option B forever**  
  Pros: maximum reproducibility and CI alignment.  
  Cons: slower day‑to‑day dev, higher barrier to contribution, especially on slower hardware.

- **Locking in CI only, never locally**  
  Pros: very strict control over lockfiles.  
  Cons: developers cannot preview dependency changes without pushing to CI, leading to long cycles.

- **Ignore locking** and use `uv pip install` without a lockfile  
  Pros: no cognitive overhead.  
  Cons: non‑reproducible builds, broken “repeatable environment” guarantees.

---

## Common Mistakes to Avoid

- ❌ Running `uv pip install ...` without updating `uv.lock` via `uv lock` (or `docker compose run ... uv lock`).  
- ❌ Forgetting to run Option B before a release and trusting only host‑resolved locks.  
- ❌ Putting `uv.lock`‑sensitive decisions (e.g., CI‑only env) without clearly documenting the Option B workflow.  
- ❌ Not documenting the split between “fast‑dev Option A” and “production‑quality Option B” in the README.

---

## Files to Create / Update

| File | Purpose |
|---|---|
| `docs/adr/ADR-007-Dependency-Locking-Strategy.md` | This ADR. |
| `README.md` | Briefly document “Option A for dev, Option B for production‑like locks” and the two commands. |
| `mcp_servers/datetime/pyproject.toml` | No change; already uses `uv`‑compatible structure. |
| `pyproject.toml` | No change; already uses `uv`‑compatible structure. |
```

***
