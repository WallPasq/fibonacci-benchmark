from src.strategies.protocol import CacheableFibonacciStrategy


class Memoization(CacheableFibonacciStrategy):
    """Calculates the n-th Fibonacci number using a recursive approach with memoization."""

    def __init__(self) -> None:
        """Initializes the cache."""
        self.clear_cache()

    @property
    def name(self) -> str:
        return "Memoization"

    def clear_cache(self) -> None:
        self._cache = [0, 1]

    def calculate(self, n: int) -> int:
        if n < len(self._cache):
            return self._cache[n]

        self._cache.append(self.calculate(n - 1) + self.calculate(n - 2))
        return self._cache[n]
