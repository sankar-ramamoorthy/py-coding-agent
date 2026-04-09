import re
from typing import List

STOPWORDS = {
    "the","is","in","on","at","a","an","and","or","to","for","of","with","by","from"
}


class KeywordRanker:
    """
    Lightweight keyword-based retrieval and ranking strategy.

    This class scores items (e.g., playbooks) based on:
    - keyword frequency
    - exact phrase matches
    - adjacent keyword pairs

    It is designed to be:
    - fast (no external dependencies)
    - interpretable (easy to debug scores)
    - extensible (can be replaced by TF-IDF or embeddings later)

    Parameters
    ----------
    logger : callable, optional
        Logging function (e.g., agent._log). If not provided, logging is disabled.
    """
    
    def __init__(self, logger=None, debug=False):
        self._log = logger or (lambda *args, **kwargs: None)
        self.debug = debug
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize input text into lowercase word tokens.

        Uses a simple regex to extract alphanumeric words.

        Parameters
        ----------
        text : str
            Input text.

        Returns
        -------
        List[str]
            List of normalized tokens.
        """
        return re.findall(r"\b\w+\b", text.lower())

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from a query string.

        Filters out:
        - common stopwords
        - very short tokens

        Falls back to all tokens if filtering removes everything.

        Parameters
        ----------
        query : str
            User query.

        Returns
        -------
        List[str]
            List of keywords used for scoring.
        """


        tokens = self._tokenize(query)
        keywords = [t for t in tokens if t not in STOPWORDS and len(t) > 3]

        if not keywords:
            keywords = tokens

        return keywords

    def _score(self, content: str, query: str, keywords: List[str]) -> int:
        """
        Compute a relevance score between a query and a content string.

        Scoring components:
        - keyword frequency (weighted)
        - exact query match (strong boost)
        - adjacent keyword pair matches (medium boost)

        Parameters
        ----------
        content : str
            Text content to evaluate (e.g., playbook body).
        query : str
            Original user query.
        keywords : List[str]
            Extracted keywords from the query.

        Returns
        -------
        int
            Relevance score (higher = more relevant).
        """

        content = content.lower()
        score = 0

        # keyword frequency
        for kw in keywords:
            score += content.count(kw) * 2

        # exact phrase boost
        if query.lower() in content:
            score += 10

        # adjacent word boost
        for i in range(len(keywords) - 1):
            pair = f"{keywords[i]} {keywords[i+1]}"
            if pair in content:
                score += 5

        return score

    def _get_text(self, item) -> str:
        """
        Extract searchable text from an item.

        This abstraction allows different item schemas
        without changing the ranking logic.
        """
        return getattr(item, "content", "")

    def search(self, query: str, items: list, top_k: int = 3):
        """
        Rank items by relevance to a query and return top matches.

        Steps:
        1. Extract keywords from query
        2. Score each item
        3. Sort by score (descending)
        4. Filter out zero-score items
        5. Return top_k results

        Parameters
        ----------
        query : str
            User query string.
        items : list
            List of items with a `.content` attribute.
        top_k : int, optional
            Maximum number of results to return (default is 3).

        Returns
        -------
        list
            Top-ranked items.
        """

        keywords = self._extract_keywords(query)

        scored = [
            (item, self._score(self._get_text(item), query, keywords))
            for item in items
        ]

        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        if self.debug:
            self._log("🔍 Retrieval debug:")
            for item, score in ranked[:5]:
                self._log(f"  {getattr(item, 'name', '<unnamed>')}: {score}")

        return [item for item, score in ranked if score > 0][:top_k]