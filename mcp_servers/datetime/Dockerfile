# mcp_servers/datetime/Dockerfile

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy lockfile and manifest
COPY uv.lock pyproject.toml ./

# Install dependencies from lockfile
RUN uv sync --no-dev --no-editable

# Copy the app
COPY . /app

ENV PYTHONUNBUFFERED=1

#CMD ["python", "datetime_mcp/server.py"]
CMD ["uv", "run", "python", "datetime_mcp/server.py"]

# rely on uv.lock + uv sync for reproducibility, no uv pip install 
# ... unless you need an editable install.