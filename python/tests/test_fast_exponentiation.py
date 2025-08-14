from src.strategies.fast_exponentiation import FastExponentiation
from src.strategies.protocol import FibonacciStrategy


def test_fast_exponentiation_strategy_conforms_to_protocol():
    """Verify that the fast_exponentiation strategy implements the FibonacciStrategy protocol."""
    strategy = FastExponentiation()
    assert isinstance(strategy, FibonacciStrategy)


def test_fast_exponentiation_strategy_calculates_correctly():
    """Test some known Fibonacci values."""
    strategy = FastExponentiation()
    assert strategy.calculate(0) == 0
    assert strategy.calculate(1) == 1
    assert strategy.calculate(10) == 55
    assert strategy.calculate(20) == 6_765
