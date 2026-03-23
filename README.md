# py-coding-agent

A Dockerized Python coding agent that uses an LLM to reason, call tools, and execute tasks inside a **sandboxed workspace**.

Inspired by autonomous agent systems like pi-mono, this project explores **tool-based reasoning, dynamic code execution, and self-extending capabilities** using local or cloud LLMs.

---

## Features

### Core Capabilities

* CLI-driven coding agent
* Multi-step reasoning + execution loop (pi-mono minimal loop)
* Native LLM tool calling with JSON schemas
* **Workspace sandboxing (`/workspace`)**
* Dynamic Python tool creation
* File + shell interaction tools
* **Multi-provider LLM support via LiteLLM** (Groq, OpenAI, Anthropic, and more)
* Local Ollama support (default, zero extra dependencies)

---

### Sandboxed Execution

All agent actions are restricted to:

```
/workspace
```

* Prevents access to system files
* Blocks directory traversal (`../../`)
* Ensures safe file operations inside Docker

---

### Built-in Tools

* `list_files` — List files and directories (recursive support)
* `read_file` — Read file contents
* `write_file` — Write content to files
* `edit_file` — Edit files via find-and-replace
* `shell` — Execute shell commands (restricted to workspace)
* `install_dependency` — Install Python packages via `uv`
* `create_tool` — Dynamically create new Python tools

---

### LLM Providers

| Provider | `LLM_PROVIDER` | Model env var | Notes |
|---|---|---|---|
| Ollama (default) | `ollama` | `OLLAMA_MODEL` | Local, zero extra deps |
| Groq | `litellm` | `LITELLM_MODEL=groq/qwen/qwen3-32b` | Fast, free tier |
| OpenAI | `litellm` | `LITELLM_MODEL=openai/gpt-4o` | Requires `OPENAI_API_KEY` |
| Anthropic | `litellm` | `LITELLM_MODEL=anthropic/claude-3-5-haiku-20241022` | Requires `ANTHROPIC_API_KEY` |

---

### Pi-Mono Minimal Loop

The agent follows a **minimal reasoning loop** inspired by pi-mono:

```
1. User sends query → Agent
2. Agent appends query to memory
3. LLM reads memory → decides:
      a) Final answer → return to user
      b) Tool call → specify tool + args
4. Agent executes tool (sandboxed)
5. Tool result appended to memory
6. LLM reads updated memory → next tool call or final answer
7. Repeat until LLM returns final answer or max steps reached
```

---

### Dynamic Tools Workflow

Dynamic tools allow the agent to extend itself at runtime:

```
User → Agent → LLM → create_tool → Tool file saved in dynamic_tools/
           ↓                     ↘ load_dynamic_tools() → Agent updates tool registry
           LLM ← memory updated ← Tool result
           ↓
       Final Answer → User
```

---

### Session & Memory Management

Special commands supported by the agent:

- `/clear` → Clears conversation memory (except system prompt), resets loop guards
- `/bye` → Ends session cleanly

**Memory Handling**

- Agent auto-prunes older messages after every N tool calls (default: 5)
- Keeps the last 20 messages by default

---

### Project Structure

```
py_mono/
├── agent/        # Core agent loop
├── llm/          # Ollama + LiteLLM providers, tool schemas
├── tools/        # Built-in and dynamic tools
├── utils/        # Path safety + helpers
├── ui/           # CLI interface
├── config.py     # Environment configuration
└── main.py       # Entry point

dynamic_tools/    # Runtime-generated tools (volume mounted)
workspace/        # Mounted safe working directory
docs/
├── adr/          # Architectural Decision Records
└── *.md          # Design and architecture docs
```

---

### Running with Docker

#### 1. Clone the repository

```
git clone https://github.com/sankar-ramamoorthy/py-coding-agent.git
Set-Location py-coding-agent
```

#### 2. Configure environment

Create a `.env` file in the project root:

```
# LLM Provider — choose one
LLM_PROVIDER=litellm
LITELLM_MODEL=groq/qwen/qwen3-32b
GROQ_API_KEY=your-groq-key-here

# Or use local Ollama (default)
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=lfm2.5-thinking:latest
```

#### 3. Start Ollama on host (if using Ollama)

```
ollama serve
ollama pull lfm2.5-thinking:latest
```

#### 4. Build and run

```
docker compose build
docker compose run py-coding-agent
```

---

### Example Usage

```
> list files
> read file plan.md
> write a hello world python script to hello.py
> run hello.py
> write me a Python script that reads a CSV file and prints a summary
> install the requests package
> create a tool that appends safely to a file
> /clear
> /bye
```

---

### Current Limitations

* No persistent memory across sessions
* No tool validation or retry logic
* Output prints twice in CLI (known issue, backlog)
* LLM may answer from stale memory instead of re-reading files after edits

---

### Roadmap

**Milestone 1 (Core Agent) ✅**

* [x] Agent loop with tool execution
* [x] Base tools (file + shell)
* [x] CLI interface
* [x] Native Ollama tool calling
* [x] Workspace sandboxing
* [x] File listing tool (`list_files`)
* [x] Tool usage reliability improvements
* [x] Docstrings and polish

**Milestone 2 (Runtime + Infra) 🔄**

* [x] Multi-provider LLM support via LiteLLM (ADR-005)
* [x] Docker Compose with volume mounts
* [x] Config-driven environment
* [x] MVP demo — end-to-end script generation
* [ ] MCP Server (ADR-004)

**Milestone 3 (Provider Registry + Session Management)**

* [ ] Provider registry pattern (ADR-006)
* [ ] Runtime provider switching (`/provider groq`)
* [ ] Encrypted API key management
* [ ] Session manager

**Milestone 4 (Polish)**

* [ ] Documentation
* [ ] Full workflow testing
* [ ] Packaging

---

### Future Enhancements (V2)

* Multi-agent system (planner / coder / tester)
* Tool registry + validation
* Memory indexing for tools
* Automated tool testing
* Smarter task decomposition
* Smart provider routing by task type

---

### Key Concepts

* Tool-based LLM agents
* Self-extending systems
* Local-first AI workflows
* Safe execution via containerization
* Provider-agnostic LLM abstraction

---

## License

MIT License