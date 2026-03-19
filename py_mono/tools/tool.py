# py_mono/tools/tool.py

class Tool:
    def __init__(self, name, description, func, parameters=None):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {"type": "object", "properties": {}, "required": []}