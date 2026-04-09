from typing import List, Protocol


class RetrievalStrategy(Protocol):
    def search(self, query: str, items: list, top_k: int = 3) -> List:
        ...