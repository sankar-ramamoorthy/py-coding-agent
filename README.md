
***

## README.md
```markdown
# py-coding-agent

A Dockerized Python coding agent that uses an LLM to reason, call tools, and execute tasks inside a **sandboxed workspace**.

Inspired by autonomous agent systems like pi‑mono, this project explores **tool‑based reasoning, dynamic code execution, and self‑extending capabilities** using local or cloud LLMs.

---

## Overall file responsibilities

* `README.md` → short, welcoming intro + how‑to‑run  
* `docs/design.md` → big‑picture design, goals, and narrative flow  
* `docs/architectural‑diagram.md` → diagrams + ADR‑005 / ADR‑004 visuals  
* `docs/design-summary.md` → one‑page snapshot of “what is implemented now” + where we are headed  

---

## Features

### Core Capabilities

* CLI‑driven coding agent  
* Multi‑step reasoning + execution loop (pi‑mono minimal loop)  
* Native LLM tool calling with JSON schemas  
* **Workspace sandboxing (`/workspace`)**  
* Dynamic Python tool creation  
* File + shell interaction tools  
* **Multi‑provider LLM support via LiteLLM** (Groq, OpenAI, Anthropic, and more)  
* Local Ollama support (default, zero extra dependencies)  
* **MCP Server integration via FastMCP + HTTP**  
* **Runtime LLM provider switching and model binding** via `/provider <name> [model]` and `/providers`  

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

### Built‑in Tools

* `list_files` — List files and directories (recursive support)  
* `read_file` — Read file contents  
* `write_file` — Write content to files  
* `edit_file` — Edit files via find‑and‑replace  
* `shell` — Execute shell commands (restricted to workspace)  
* `install_dependency` — Install Python packages via `uv`  
* `create_tool` — Dynamically create new Python tools  

### MCP Tools

* `get_current_datetime` — Get current UTC datetime from datetime MCP server  

---

### LLM Providers

| Provider                 | `LLM_PROVIDER` | Model env var                                         | Notes |
|--------------------------|----------------|-------------------------------------------------------|-------|
| Ollama (default)         | `ollama`       | `OLLAMA_MODEL`                                        | Local, zero extra deps |
| Groq via LiteLLM         | `litellm`      | `LITELLM_MODEL=groq/qwen/qwen3-32b`                  | Fast, free tier |
| OpenAI via LiteLLM       | `litellm`      | `LITELLM_MODEL=openai/gpt-4o`                         | Requires `OPENAI_API_KEY` |
| Anthropic via LiteLLM    | `litellm`      | `LITELLM_MODEL=anthropic/claude-3-5-haiku-20241022`  | Requires `ANTHROPIC_API_KEY` |

Thanks to the **provider registry** and **SessionManager**, you can **dynamically switch** providers and bind models at runtime using CLI commands (see “How to use” below).

---

### MCP Servers

| MCP Server   | Port | Tool                | Status |
|--------------|------|---------------------|--------|
| `datetime-mcp` | 50051 | `get_current_datetime` | ✅ Live |

MCP servers run as separate Docker containers on a shared network.  
The agent communicates with them via `http://datetime-mcp:50051/mcp`.

---

### Pi‑Mono Minimal Loop

The agent follows a **minimal reasoning loop** inspired by pi‑mono:

```
1. User sends query → Agent
2. Agent appends query to memory
3. LLM reads memory → decides:
   a) Final answer → return to user
   b) Tool call → specify tool + args
4. Agent executes tool (sandboxed or via MCP server)
5. Tool result appended to memory
6. LLM reads updated memory → next tool call or final answer
7. Repeat until LLM returns final answer or max steps reached
```

---

### Dynamic Tools Workflow

Dynamic tools allow the agent to extend itself at runtime:

```
User → Agent → LLM → create_tool → Tool file saved in dynamic_tools/
       ↓                           ↘ load_dynamic_tools() → Agent updates tool registry
       ↓
   Final Answer → User
```

---

### Session & Memory Management

Special commands supported by the agent:

- `/clear` → Clears conversation memory (except system prompt), resets loop guards  
- `/bye` → Ends session cleanly  
- `/providers` → Shows current provider and available providers  
- `/provider <name>` → Switches active LLM provider for the remainder of the session  
- `/provider <name> <model>` → Switches provider and **binds a model** for this session  
  - Example: `/provider ollama granite4:350m`, `/provider litellm groq/qwen/qwen3-32b`  

**Memory handling**

- Agent auto‑prunes older messages after every N tool calls (default: 5)  
- Keeps the last 20 messages by default  

---

### Project Structure

```
py_mono/
├── agent/            # Core agent loop
├── llm/              # Ollama + LiteLLM providers, tool schemas
├── mcp_integration/  # MCP client and tool wrappers
├── tools/            # Built-in and dynamic tools
├── utils/            # Path safety + helpers
├── ui/               # CLI interface
├── config.py         # Environment configuration
└── main.py           # Entry point

mcp_servers/          # MCP microservices
└── datetime/         # Datetime MCP server (FastMCP + HTTP)

dynamic_tools/        # Runtime‑generated tools (volume mounted)
workspace/            # Mounted safe working directory
docs/
├── adr/              # Architectural Decision Records
└── *.md              # Design and architecture docs
```

---

### Running with Docker

#### 1. Clone the repository

```bash
git clone https://github.com/sankar-ramamoorthy/py-coding-agent.git
cd py-coding-agent
```

#### 2. Configure environment

Create a `.env` file in the project root:

```bash
# LLM Provider — choose one
LLM_PROVIDER=litellm
LITELLM_MODEL=groq/qwen/qwen3-32b
GROQ_API_KEY=your-groq-key-here

# Or use local Ollama (default)
LLM_PROVIDER=ollama
OLLAMA_MODEL=lfm2.5-thinking:latest
```

#### 3. Start Ollama on host (if using Ollama)

```bash
ollama serve
ollama pull lfm2.5-thinking:latest
```

#### 4. Build and run

```bash
# In project root (agent)
uv lock

# In mcp_servers/datetime
cd mcp_servers/datetime
uv lock

# Back to project root
cd ../../
docker compose build
docker compose run py-coding-agent
```

Both the agent and datetime MCP server start automatically via Docker Compose.

---

### How to use (including provider switching)

Once the agent is running:

```text
> /providers
Active provider: OllamaProvider
Active model: lfm2.5-thinking:latest
Available providers: ollama, litellm
```

Switch provider and optionally bind a model:

```text
> /provider litellm groq/qwen/qwen3-32b
Switched provider to LiteLLMProvider (litellm) using model 'groq/qwen/qwen3-2b'.
```

Switch back:

```text
> /provider ollama
Switched provider to OllamaProvider (ollama).
```

Switch with an explicit local model:

```text
> /provider ollama granite4:350m
Switched provider to OllamaProvider (ollama) using model 'granite4:350m'.
```

Run normal tasks (all of these automatically use the currently active provider):

```text
> list files
> what is the current date and time
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
* LLM may answer from stale memory instead of re‑reading files after edits  

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

**Milestone 2 (Runtime + Infra) ✅**

* [x] Multi‑provider LLM support via LiteLLM (ADR‑005)  
* [x] Docker Compose with volume mounts  
* [x] Config‑driven environment  
* [x] MVP demo — end‑to‑end script generation  
* [x] MCP Server integration via FastMCP + HTTP (ADR‑004)  

**Milestone 3 (Provider Registry + Session Management) ✅**

* [x] Provider registry pattern (ADR‑006)  
* [x] Runtime provider switching and model binding (e.g. `/provider ollama granite4:350m`, `/providers`)  
* [x] Session manager  
* [x] **Dependency locking strategy (ADR‑007)** — hybrid `uv lock` workflow on host vs Docker  
* [x] Tight‑binding model selection in provider instances (ADR‑009)  
* [ ] Smart provider routing by task type (ADR‑008) — e.g., `ollama` for local/private, `groq` for fast tools, `anthropic` for complex reasoning  

**Milestone 4 (Polish)**

* [ ] Documentation  
* [ ] Full workflow testing  
* [ ] Packaging  

---

### Future Enhancements (V2)

* Multi‑agent system (planner / coder / tester)  
* Tool registry + validation  
* Memory indexing for tools  
* Automated tool testing  
* Smarter task decomposition  
* Smart provider routing by task type  
* Additional MCP servers (weather, search, geocoding)  

---

### Key Concepts

* Tool‑based LLM agents  
* Self‑extending systems  
* Local‑first AI workflows  
* Safe execution via containerization  
* Provider‑agnostic LLM abstraction  
* MCP microservices for specialized tool execution  

---

## License

MIT License
```

***
