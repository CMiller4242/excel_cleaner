"""
Suggestion Engine - High-performance autocomplete matching
Supports prefix, substring, and fuzzy matching with caching
"""

import re
from typing import List, Tuple, Callable
from functools import lru_cache


class SuggestionEngine:
    """
    High-performance suggestion matching engine with multiple strategies.

    Features:
    - Prefix matching (default)
    - Substring matching
    - Fuzzy matching (optional)
    - LRU caching for repeated queries
    - Case-insensitive
    - Optimized for large datasets
    """

    MATCH_PREFIX = "prefix"      # Matches at start: "per" → "Person Name"
    MATCH_SUBSTRING = "substring" # Matches anywhere: "per" → "Super Person"
    MATCH_FUZZY = "fuzzy"        # Fuzzy match: "prsn" → "Person"

    def __init__(self, values: List[str], match_mode: str = MATCH_SUBSTRING):
        """
        Initialize suggestion engine.

        Args:
            values: List of all possible values
            match_mode: Matching strategy (prefix, substring, fuzzy)
        """
        self.all_values = sorted(values)  # Sort for better UX
        self.match_mode = match_mode
        self._cache = {}
        self._max_cache_size = 1000

    def get_suggestions(self, query: str, max_results: int = 20) -> List[str]:
        """
        Get suggestions matching the query.

        Args:
            query: User's search text
            max_results: Maximum number of suggestions to return

        Returns:
            List of matching suggestions (ranked by relevance)
        """
        if not query:
            return self.all_values[:max_results]

        # Check cache first
        cache_key = f"{query.lower()}:{max_results}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Normalize query
        query_lower = query.lower()

        # Get matches based on mode
        if self.match_mode == self.MATCH_PREFIX:
            matches = self._prefix_match(query_lower)
        elif self.match_mode == self.MATCH_FUZZY:
            matches = self._fuzzy_match(query_lower)
        else:  # MATCH_SUBSTRING (default)
            matches = self._substring_match(query_lower)

        # Rank and limit results
        ranked = self._rank_matches(matches, query_lower)
        results = ranked[:max_results]

        # Cache results (limit cache size)
        if len(self._cache) >= self._max_cache_size:
            # Clear oldest entries (simple FIFO)
            self._cache.clear()
        self._cache[cache_key] = results

        return results

    def _prefix_match(self, query: str) -> List[str]:
        """Match values that start with query"""
        return [v for v in self.all_values if v.lower().startswith(query)]

    def _substring_match(self, query: str) -> List[str]:
        """Match values that contain query anywhere"""
        return [v for v in self.all_values if query in v.lower()]

    def _fuzzy_match(self, query: str) -> List[str]:
        """
        Fuzzy match - matches if query chars appear in order.
        Example: "prsn" matches "Person", "prsnst" matches "Person Street"
        """
        pattern = '.*'.join(map(re.escape, query))
        regex = re.compile(pattern, re.IGNORECASE)
        return [v for v in self.all_values if regex.search(v)]

    def _rank_matches(self, matches: List[str], query: str) -> List[str]:
        """
        Rank matches by relevance.

        Priority:
        1. Exact match (case-insensitive)
        2. Starts with query
        3. Word boundary match (query starts a word)
        4. Contains query
        """
        if not matches:
            return []

        exact = []
        prefix = []
        word_boundary = []
        other = []

        for match in matches:
            match_lower = match.lower()

            if match_lower == query:
                exact.append(match)
            elif match_lower.startswith(query):
                prefix.append(match)
            elif self._is_word_boundary_match(match_lower, query):
                word_boundary.append(match)
            else:
                other.append(match)

        # Combine in priority order
        return exact + prefix + word_boundary + other

    def _is_word_boundary_match(self, text: str, query: str) -> bool:
        """Check if query starts a word in text"""
        # Look for query after word boundaries (space, :, -, etc.)
        pattern = r'[\s:_\-]' + re.escape(query)
        return bool(re.search(pattern, text, re.IGNORECASE))

    def update_values(self, values: List[str]):
        """Update the list of available values and clear cache"""
        self.all_values = sorted(values)
        self._cache.clear()

    def clear_cache(self):
        """Clear suggestion cache"""
        self._cache.clear()


class ContextualSuggestionEngine(SuggestionEngine):
    """
    Extended suggestion engine with contextual awareness.

    Additional features:
    - Track recently used values
    - Boost frequently used suggestions
    - Domain-specific context (e.g., column names, operations)
    """

    def __init__(self, values: List[str], match_mode: str = SuggestionEngine.MATCH_SUBSTRING):
        super().__init__(values, match_mode)
        self.recent_values = []  # Track recent selections
        self.usage_count = {}    # Track frequency
        self.max_recent = 10

    def record_selection(self, value: str):
        """Record that user selected this value"""
        # Update recent list
        if value in self.recent_values:
            self.recent_values.remove(value)
        self.recent_values.insert(0, value)
        self.recent_values = self.recent_values[:self.max_recent]

        # Update usage count
        self.usage_count[value] = self.usage_count.get(value, 0) + 1

    def get_suggestions(self, query: str, max_results: int = 20) -> List[str]:
        """Get suggestions with contextual boosting"""
        base_matches = super().get_suggestions(query, max_results * 2)

        if not query:
            # If empty query, show recent values first
            recent_in_list = [v for v in self.recent_values if v in self.all_values]
            remaining = [v for v in base_matches if v not in recent_in_list]
            return (recent_in_list + remaining)[:max_results]

        # Boost frequently used values
        scored = []
        for match in base_matches:
            score = 0

            # Recent usage boost
            if match in self.recent_values:
                score += 100 - self.recent_values.index(match) * 10

            # Frequency boost
            if match in self.usage_count:
                score += self.usage_count[match] * 5

            scored.append((score, match))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        return [match for _, match in scored[:max_results]]
