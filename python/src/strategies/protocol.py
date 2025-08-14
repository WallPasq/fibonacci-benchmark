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

    def clear_cache(self) -> None:
        """Clears the cache, being able to keep the base cases (0 and 1) or completely clear the cache."""
        ...
