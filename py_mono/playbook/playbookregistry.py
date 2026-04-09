from pathlib import Path
from typing import List
from py_mono.playbook.playbook import Playbook


class PlaybookRegistry:
    def __init__(self, root: Path):
        self.root = root
        self._playbooks = self._load()

    def _load(self) -> List[Playbook]:
        playbooks = []
        if self.root.exists(): #If playbooks/ doesn't exist yet we skip for loop
            for md_file in self.root.rglob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                playbooks.append(
                    Playbook(
                        name=md_file.stem.lower(),
                        path=md_file,
                        content=content,
                    )
                )

        return playbooks

    def search(self, query: str) -> List[Playbook]:
        query = query.lower()

        # v1: dumb keyword match
        results = []
        for pb in self._playbooks:
            if pb.name in query or any(word in pb.content.lower() for word in query.split()):
                results.append(pb)

        return results[:3]  # keep context small