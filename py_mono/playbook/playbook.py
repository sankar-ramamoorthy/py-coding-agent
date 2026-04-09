from dataclasses import dataclass
from pathlib import Path

@dataclass
class Playbook:
    name: str
    path: Path
    content: str