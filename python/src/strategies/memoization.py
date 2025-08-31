from src.strategies.protocol import CacheableFibonacciStrategy


class Memoization(CacheableFibonacciStrategy):
    """Calculates the n-th Fibonacci number using a recursive approach with memoization."""

    _cache: list[int] = [0, 1]

    @property
    def name(self) -> str:
        return "Memoization"

    def clear_cache(self):
        self._cache = [0, 1]

    def cache_size(self) -> int:
        return len(self._cache)

    def get_cache_value(self, n: int) -> int:
        return self._cache[n]

    def calculate(self, n: int) -> int:
        if n < 0:
            raise ValueError("n must be greater than or equal to 0.")

        if n < self.cache_size():
            return self.get_cache_value(n)

        self._cache.append(self.calculate(n - 1) + self.calculate(n - 2))
        return self.get_cache_value(n)
