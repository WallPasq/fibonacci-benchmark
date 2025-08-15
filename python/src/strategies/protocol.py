from typing import Protocol, runtime_checkable


@runtime_checkable
class FibonacciStrategy(Protocol):
    """Defines the common interface for all Fibonacci calculation strategies."""

    @property
    def name(self) -> str:
        """Returns the name of the strategy."""
        ...

    def calculate(self, n: int) -> int:
        """Calculates the n-th Fibonacci number."""
        ...


@runtime_checkable
class CacheableFibonacciStrategy(FibonacciStrategy, Protocol):
    """Defines the common interface for Fibonacci calculation strategies that have caching (like memoization)."""

    _cache: list[int]

    def clear_cache(self) -> None:
        """Clears the cache, being able to keep the base cases (0 and 1) or completely clear the cache."""
        ...

    def cache_size(self) -> int:
        """Returns the total number of values in the cache."""
        ...

    def get_cache_value(self, n: int) -> int:
        """Returns a value that is stored in the cache by its index."""
        ...
