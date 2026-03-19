import importlib.util
import pathlib

def load_dynamic_tools(folder="dynamic_tools"):
    tools = []
    path = pathlib.Path(folder)
    if not path.exists():
        return tools

    for file in path.glob("*.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "tool"):
            tools.append(module.tool)
    return tools