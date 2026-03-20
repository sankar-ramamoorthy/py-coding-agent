#  py-coding-agent

A Dockerized Python coding agent that uses an LLM to reason, call tools, and execute tasks inside a **sandboxed workspace**.

Inspired by autonomous agent systems like pi-mono, this project explores **tool-based reasoning, dynamic code execution, and self-extending capabilities** using local LLMs via Ollama.

---

##  Features

###  Core Capabilities

* CLI-driven coding agent
* Multi-step reasoning + execution loop
* Native LLM tool calling (Ollama `/api/chat`)
* **Workspace sandboxing (`/workspace`)**
* Dynamic Python tool creation
* File + shell interaction tools

---

###  Sandboxed Execution

All agent actions are restricted to:

```text
/workspace
```

* Prevents access to system files
* Blocks directory traversal (`../../`)
* Ensures safe file operations inside Docker

---

###  Built-in Tools

* `list_files` — List files and directories (recursive support)
* `read_file` — Read file contents
* `write_file` — Write content to files
* `edit_file` — Modify files
* `shell` — Execute shell commands (restricted to workspace)
* `install_dependency` — Install Python packages via `uv`
* `create_tool` — Dynamically create new Python tools

---

###  LLM Integration

* Uses **Ollama** for local inference
* Supports **native tool calling with JSON schemas**
* Multi-step loop:

  1. LLM decides → tool call or answer
  2. Agent executes tool
  3. Result fed back into LLM
  4. Final answer generated

---

##  Architecture

```text
User (CLI)
   ↓
Agent Loop
   ↓
LLM (Ollama)
   ↓
Tool Call → Tool Execution
   ↓
Result → LLM → Final Answer
```

---

##  Project Structure

```text
py_mono/
├── agent/        # Core agent loop
├── llm/          # Ollama provider + tool schemas
├── tools/        # Built-in and dynamic tools
├── utils/        # Path safety + helpers
├── ui/           # CLI interface
├── config.py     # Environment configuration
└── main.py       # Entry point

dynamic_tools/    # Runtime-generated tools
workspace/        # Mounted safe working directory
```

---

## 🐳 Running with Docker

### 1. Clone the repository

```powershell
git clone https://github.com/sankar-ramamoorthy/py-coding-agent.git
Set-Location py-coding-agent
```

---

### 2. Start Ollama on host

```bash
ollama serve
```

Pull a model (recommended):

```bash
ollama pull qwen3:4b
```

---

### 3. Build the Docker image

```bash
docker build -t py-coding-agent .
```

---

### 4. Run the agent

```powershell
docker run -it `
  -v ${PWD}\workspace:/workspace `
  -e OLLAMA_MODEL=qwen3:4b `
  py-coding-agent
```

---

##  Example Usage

```text
> list files
> list files recursively
> read file py_mono/main.py
> write file test.py with hello world code
> run a shell command to list files
```

---

##  Current Limitations (V1)

* Tool usage is **not always reliably triggered**
* Limited reasoning over large codebases
* No persistent memory yet
* No tool validation or retry logic
* Output formatting can vary depending on model

---

##  Roadmap

### Milestone 1 (Core Agent)

* [x] Agent loop with tool execution
* [x] Base tools (file + shell)
* [x] CLI interface
* [x] Native Ollama tool calling
* [x] Workspace sandboxing
* [x] File listing tool (`list_files`)
* [ ] Tool usage reliability improvements
* [ ] Docstrings and polish

---

### Milestone 2 (Runtime + Infra)

* Docker + host LLM integration
* Config-driven environment

---

### Milestone 3 (Dynamic Tools)

* Runtime tool creation
* Tool loading system

---

### Milestone 4 (Polish)

* Documentation
* Full workflow testing
* Packaging

---

##  Future Enhancements (V2)

* Multi-agent system (planner / coder / tester)
* Tool registry + validation
* Memory indexing for tools
* Automated tool testing
* Smarter task decomposition

---

##  Key Concepts

This project explores:

* Tool-based LLM agents
* Self-extending systems
* Local-first AI workflows
* Safe execution via containerization

---

##  License

MIT License
