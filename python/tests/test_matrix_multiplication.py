from src.strategies.matrix_multiplication import MatrixMultiplication
from src.strategies.protocol import FibonacciStrategy


def test_matrix_multiplication_strategy_conforms_to_protocol():
    """Verify that the matrix_multiplication strategy implements the FibonacciStrategy protocol."""
    strategy = MatrixMultiplication()
    assert isinstance(strategy, FibonacciStrategy)


def test_matrix_multiplication_strategy_calculates_correctly():
    """Test some known Fibonacci values."""
    strategy = MatrixMultiplication()
    assert strategy.calculate(0) == 0
    assert strategy.calculate(1) == 1
    assert strategy.calculate(10) == 55
    assert strategy.calculate(20) == 6_765
