# py_mono/tools/tool.py

class Tool:
    def __init__(self, name, description, func, parameters=None, returns: dict | None = None):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {"type": "object", "properties": {}, "required": []}
        self.returns = returns or {}
    def run(self, **kwargs):
        return self.func(**kwargs)
    