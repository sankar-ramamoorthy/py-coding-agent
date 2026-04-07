# py_mono/tools/tool.py

class Tool:
    """
    Wrapper around a callable that exposes it as a structured agent tool.

    A Tool provides a consistent interface (`run`) for executing functions
    within the agent, along with metadata describing its purpose, expected
    inputs, and outputs. Tools are intended to be invoked by skills and
    LLM-generated code via `tool.run(...)`, not by calling the underlying
    function directly.

    Design principles:
    - Enforces a stable execution interface for all tools
    - Encourages structured, keyword-based argument passing
    - Separates tool metadata (name, description, schema) from execution logic
    - Prevents direct access to the underlying function (`_func`)

    Attributes:
        name (str):
            Unique identifier for the tool. Used to retrieve the tool from
            `context.agent_tools`.

        description (str):
            Human-readable description of what the tool does. Used in prompts
            to inform the LLM.

        _func (Callable):
            The underlying Python function implementing the tool logic.
            This should not be accessed directly; use `run()` instead.

        parameters (dict):
            JSON-schema-like definition of expected input parameters.
            Defaults to an empty object schema.

        returns (dict):
            Optional schema describing the return value.

    Methods:
        run(**kwargs):
            Execute the tool using keyword arguments only.

            Args:
                **kwargs:
                    Named arguments passed to the underlying function.

            Returns:
                Any: The result of the tool execution.

            Raises:
                ValueError:
                    If arguments are not provided as keyword arguments.

    Example:
        def read_file(path: str) -> str:
            return open(path).read()

        tool = Tool(
            name="read_file",
            description="Read a file from disk",
            func=read_file,
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        )

        result = tool.run(path="example.txt")
    """
    def __init__(self, name, description, func, parameters=None, returns: dict | None = None):
        self.name = name
        self.description = description
        self._func = func
        self.parameters = parameters or {"type": "object", "properties": {}, "required": []}
        self.returns = returns or {}
    def run(self, **kwargs):
        if not isinstance(kwargs, dict):
            raise ValueError("Tool.run expects keyword arguments only")
        return self._func(**kwargs)
    