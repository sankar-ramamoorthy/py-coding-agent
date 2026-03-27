FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
# Assumes you have committed uv.lock and pyproject.toml in the repo root.
WORKDIR /app

# Install runtime deps (git, curl, build tools, etc.)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy lockfile and manifest first (best layer caching)
COPY uv.lock pyproject.toml ./

# Install dependencies from the lockfile (no --system, no editable)
RUN uv sync --no-dev --no-editable

# Copy the app code
COPY . /app

# Install the project in-place (if you want an editable install)
# If you moved helpers into pyproject.toml, you can drop this.
#RUN uv pip install --system -e .

# Dynamic‑tools dir
RUN mkdir -p /app/dynamic_tools

# Env vars
ENV PYTHONUNBUFFERED=1 \
    LLM_PROVIDER=ollama \
    OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    OLLAMA_MODEL=lfm2.5-thinking:latest

CMD ["python", "py_mono/main.py"]
