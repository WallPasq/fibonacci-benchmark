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
