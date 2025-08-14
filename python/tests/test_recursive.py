from src.strategies.protocol import FibonacciStrategy
from src.strategies.recursive import Recursive


def test_recursive_strategy_conforms_to_protocol():
    """Verify that the recursive strategy implements the FibonacciStrategy protocol."""
    strategy = Recursive()
    assert isinstance(strategy, FibonacciStrategy)


def test_recursive_strategy_calculates_correctly():
    """Test some known Fibonacci values."""
    strategy = Recursive()
    assert strategy.calculate(0) == 0
    assert strategy.calculate(1) == 1
    assert strategy.calculate(10) == 55
    assert strategy.calculate(20) == 6_765
