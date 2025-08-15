from src.strategies.protocol import FibonacciStrategy


class Recursive(FibonacciStrategy):
    """Calculates the n-th Fibonacci number using a simple recursive approach."""

    @property
    def name(self) -> str:
        return "Recursive"

    def calculate(self, n: int) -> int:
        if n <= 1:
            return n

        return self.calculate(n - 1) + self.calculate(n - 2)
