from src.strategies.iterative import Iterative
from src.strategies.protocol import FibonacciStrategy


def test_iterative_strategy_conforms_to_protocol():
    """Verify that the iterative strategy implements the FibonacciStrategy protocol."""
    assert isinstance(Iterative, FibonacciStrategy)


def test_iterative_strategy_calculates_correctly():
    """Test some known Fibonacci values."""
    strategy = Iterative()
    assert strategy.calculate(0) == 0
    assert strategy.calculate(1) == 1
    assert strategy.calculate(10) == 55
    assert strategy.calculate(20) == 6_765
