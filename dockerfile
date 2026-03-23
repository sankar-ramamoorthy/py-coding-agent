FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN uv pip install --system -e .

RUN mkdir -p /app/dynamic_tools

ENV PYTHONUNBUFFERED=1
# Dockerfile snippet
ENV LLM_PROVIDER=ollama
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=lfm2.5-thinking:latest

CMD ["python", "py_mono/main.py"]