from src.strategies.matrix_multiplication import Matrix, MatrixMultiplication
from src.strategies.protocol import FibonacciStrategy


class FastExponentiation(MatrixMultiplication, FibonacciStrategy):
    """Calculates the n-th Fibonacci number using a fast exponentiation approach."""

    @property
    def name(self) -> str:
        return "Fast Exponentiation"

    def _power(self, a: Matrix, n: int) -> Matrix:
        """Calculates the product of a 2x2 matrix using the fast exponentiation method."""
        if n < 1:
            raise ValueError("n must be greater than 0.")

        n_power: int = n - 1
        base: Matrix = a.copy()
        result: Matrix = [[1, 0], [0, 1]]

        while n_power > 0:
            if n_power % 2 > 0:
                result = self._multiply(result, base)

            base = self._multiply(base, base)
            n_power //= 2

        return result
