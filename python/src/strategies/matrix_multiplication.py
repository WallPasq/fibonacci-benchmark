from typing import TypeAlias

from src.strategies.protocol import FibonacciStrategy

Matrix: TypeAlias = list[list[int]]


class MatrixMultiplication(FibonacciStrategy):
    """Calculates the n-th Fibonacci number using a matrix multiplication approach."""

    @property
    def name(self) -> str:
        return "Matrix Multiplication"

    def _multiply(self, a: Matrix, b: Matrix) -> Matrix:
        """Calculates the product of two 2x2 matrices."""
        result: Matrix = [[0, 0], [0, 0]]

        for i in range(2):
            for j in range(2):
                for k in range(2):
                    result[i][j] += a[i][k] * b[k][j]

        return result

    def _power(self, a: Matrix, n: int) -> Matrix:
        """Calculates the product of a 2x2 matrix multiplied by itself n times."""
        result: Matrix = a.copy()

        for _ in range(n - 2):
            result = self._multiply(result, a)

        return result

    def calculate(self, n: int) -> int:
        if n < 0:
            raise ValueError("n must be greater than or equal to 0.")

        if n <= 1:
            return n

        result: Matrix = [[1, 1], [1, 0]]
        result = self._power(result, n)
        return result[0][0]
