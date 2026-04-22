from pathlib import Path
from typing import List, Dict, Any
from py_mono.playbook.playbook import Playbook
    import yaml
from typing import Dict, Any


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

    def search_deprecated(self, query: str) -> List[Playbook]:
        query = query.lower()

        # v1: dumb keyword match
        results = []
        for pb in self._playbooks:
            if pb.name in query or any(word in pb.content.lower() for word in query.split()):
                results.append(pb)

        return results[:3]  # keep context small
    

    def search(self, query: str) -> List[Playbook]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for pb in self._playbooks:
            # Parse YAML front-matter for keywords
            meta = self._parse_frontmatter(pb.content)
            keywords = set([k.lower() for k in meta.get("keywords", [])])
            name = meta.get("name", pb.name).lower()

            score = 0
            # Exact name match = highest priority
            if name in query_lower or query_lower in name:
                score += 100
            # Keyword overlap
            score += len(keywords & query_words) * 10
            # Title match
            if any(w in name for w in query_words):
                score += 5

            if score > 0:
                scored.append((score, pb))

        # Sort by score, return top 3
        scored.sort(key=lambda x: x[0], reverse=True)
        return [pb for score, pb in scored[:3]]

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        if not content.startswith("---"):
            return {}
        try:
            _, fm, _ = content.split("---", 2)
            return yaml.safe_load(fm) or {}
        except:
            return {}