# mcp_servers/datetime/Dockerfile

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY . .

RUN uv pip install --system -e .

ENV PYTHONUNBUFFERED=1

CMD ["python", "datetime_mcp/server.py"]