from src.strategies.protocol import FibonacciStrategy


class Iterative(FibonacciStrategy):
    """Calculates the n-th Fibonacci number using a simple iterative approach."""

    @property
    def name(self) -> str:
        return "Iterative"

    def calculate(self, n: int) -> int:
        if n < 0:
            raise ValueError("n must be greater than or equal to 0.")

        if n <= 1:
            return n

        a: int = 0
        b: int = 1

        for _ in range(n - 1):
            a, b = b, a + b

        return b
