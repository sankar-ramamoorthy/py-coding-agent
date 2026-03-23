# README.md

# py-coding-agent

A Dockerized Python coding agent that uses an LLM to reason, call tools, and execute tasks inside a **sandboxed workspace**.

Inspired by autonomous agent systems like pi-mono, this project explores **tool-based reasoning, dynamic code execution, and self-extending capabilities** using local LLMs via Ollama.

---

## Features

### Core Capabilities

* CLI-driven coding agent
* Multi-step reasoning + execution loop (pi-mono minimal loop)
* Native LLM tool calling (Ollama `/api/chat`)
* **Workspace sandboxing (`/workspace`)**
* Dynamic Python tool creation
* File + shell interaction tools

---

### Sandboxed Execution

All agent actions are restricted to:

````
/workspace
````

* Prevents access to system files
* Blocks directory traversal (`../../`)
* Ensures safe file operations inside Docker



### Built-in Tools

* `list_files` — List files and directories (recursive support)
* `read_file` — Read file contents
* `write_file` — Write content to files
* `edit_file` — Modify files
* `shell` — Execute shell commands (restricted to workspace)
* `install_dependency` — Install Python packages via `uv`
* `create_tool` — Dynamically create new Python tools

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

**How it works:**

1. LLM generates code using `build_create_tool_prompt(user_request)`.
2. `create_tool()` saves Python file in `dynamic_tools/`.
3. `load_dynamic_tools()` immediately makes it available for the agent loop.
4. Tools must use `resolve_safe_path()` and return **LLM-friendly strings**.

**Example tool prompt for LLM:**

```
Please create a Python tool called safe_append_file:
- Use resolve_safe_path for file operations
- Append content safely inside /workspace
- Return a clear string indicating success or error
- Define parameters in Tool metadata
```

---

### LLM Integration

* Uses **Ollama** for local inference
* Supports **native tool calling with JSON schemas**
* Multi-step loop with memory tracking ensures proper tool execution

**ASCII Flow Diagram:**

```
USER
 │
 │ query
 ▼
AGENT
 │
 │ appends to memory
 ▼
LLM
 │
 │ decides: text answer or tool_call
 ▼
┌───────────────┐
│ TOOL CALL?     │
└───────┬───────┘
        │ yes
        ▼
  Execute tool
  (sandboxed)
        │
        ▼
Tool result appended to memory
        │
        ▼
      LLM reads memory
        │
        ▼
  Repeat tool calls OR return text
        │
        ▼
FINAL ANSWER → USER
```

``
### Dynamic Tool Template

When creating a dynamic tool using `create_tool`, the LLM should follow a standard template to ensure safety and consistency.  

**Template for Python dynamic tools:**

``
# dynamic_tools/my_dynamic_tool.py

from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path
from pathlib import Path

def my_dynamic_tool_function(path: str, content: str = "") -> str:
    """
    Description of what the tool does.

    Args:
        path (str): relative path inside /workspace
        content (str, optional): content to write/append

    Returns:
        str: clear, LLM-friendly success/error message
    """
    try:
        safe_path = resolve_safe_path(path)

        # Ensure parent directories exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Example operation: append content
        with open(safe_path, "a", encoding="utf-8") as f:
            f.write(content)

        return f"✅ Successfully updated {safe_path} with {len(content)} characters."

    except Exception as e:
        return f"❌ Tool Error: {str(e)}"

# Tool metadata for agent
my_dynamic_tool = Tool(
    name="my_dynamic_tool",
    description="Describe what this dynamic tool does",
    func=my_dynamic_tool_function,
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path inside /workspace"
            },
            "content": {
                "type": "string",
                "description": "Content to append or write"
            }
        },
        "required": ["path"]
    }
)
``

**Notes for LLM-generated tools:**

1. Always use `resolve_safe_path()` to prevent escaping `/workspace`.
2. Return a **clear string**, indicating success or error (no raw exceptions).
3. Define the tool using the `Tool` class with proper `name`, `description`, and `parameters`.
4. Avoid hardcoding absolute paths.
5. Keep operations idempotent and predictable if possible.

**Example LLM prompt to generate a dynamic tool:**

```
Please create a Python tool called safe_append_file:
- It must use resolve_safe_path for file operations
- It should append content safely inside /workspace
- It should return a clear string indicating success or error
- It should define parameters in Tool metadata
```

Once saved, the agent can immediately load it via:

```
from py_mono.tools.tool_loader import load_dynamic_tools

new_tools = load_dynamic_tools()
agent.tools.update({t.name: t for t in new_tools})
```

``
###  Session & Memory Management

Special commands supported by the agent:

- `/clear` → Clears conversation memory (except system prompt)
- `/bye` → Ends session cleanly

**Memory Handling**

- Agent auto-prunes older messages after every N tool calls (default: 5)
- Keeps the last 20 messages by default
- Future: memory can be offloaded to disk for persistence


> list files
> /clear
✅ Memory cleared. You can start fresh.
> read file main.py
> /bye
👋 Goodbye! Session ended.
---

### Project Structure

``
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
``

---

### Running with Docker

### 1. Clone the repository

```
git clone https://github.com/sankar-ramamoorthy/py-coding-agent.git
Set-Location py-coding-agent
```

### 2. Start Ollama on host

```
ollama serve
```

Pull a model (recommended):

```
ollama pull lfm2.5-thinking:latest
```

### 3. Build the Docker image

```
docker build -t py-coding-agent .
```

### 4. Run the agent

docker compose run py-coding-agent
```
 **Note:** Alternatively, run directly with Docker:
 docker run -it -v ${PWD}\workspace:/workspace -v ${PWD}\dynamic_tools:/app/dynamic_tools py-coding-agent
```

---

### Example Usage

```
> list files
> list files recursively
> write file test.py with hello world code
> run a shell command to list files
> create a tool that appends safely to a file
```

---

### Current Limitations (V1)

* Tool usage is **not always reliably triggered**
* Limited reasoning over large codebases
* No persistent memory yet
* No tool validation or retry logic
* Output formatting can vary depending on model

---

### Roadmap

**Milestone 1 (Core Agent)**

* [x] Agent loop with tool execution
* [x] Base tools (file + shell)
* [x] CLI interface
* [x] Native Ollama tool calling
* [x] Workspace sandboxing
* [x] File listing tool (`list_files`)
* [x] Tool usage reliability improvements
* [x] Docstrings and polish

**Milestone 2 (Runtime + Infra)**

* Docker + host LLM integration
* Config-driven environment
* Introduce MCP-Server to handle runtime tool offloading, memory pruning, and multi-agent support.  docs\adr\ADR-004-MCP-Server.md

**Milestone 3 (Dynamic Tools)**

* Runtime tool creation
* Tool loading system

**Milestone 4 (Polish)**

* Documentation
* Full workflow testing
* Packaging

---

### Future Enhancements (V2)

* Multi-agent system (planner / coder / tester)
* Tool registry + validation
* Memory indexing for tools
* Automated tool testing
* Smarter task decomposition

---

### Key Concepts

* Tool-based LLM agents
* Self-extending systems
* Local-first AI workflows
* Safe execution via containerization

---

## License

MIT License

```

