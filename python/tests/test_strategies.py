import pytest

from src.discovery import load_strategies
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy

all_fib_strategies, all_cache_fib_strategies = load_strategies()
all_fib_strategies += all_cache_fib_strategies


@pytest.mark.parametrize("strategy", all_fib_strategies)
def test_strategy_calculates_correctly(strategy: FibonacciStrategy):
    """Test some known Fibonacci values."""
    assert strategy.calculate(0) == 0
    assert strategy.calculate(1) == 1
    assert strategy.calculate(10) == 55
    assert strategy.calculate(20) == 6_765


@pytest.mark.parametrize("strategy", all_cache_fib_strategies)
def test_strategy_clearing_cache(strategy: CacheableFibonacciStrategy):
    """Verify that clearing the cache actually clears the cache."""
    strategy.calculate(10)
    strategy.clear_cache()
    assert strategy.cache_size() == 2


@pytest.mark.parametrize("strategy", all_cache_fib_strategies)
def test_strategy_creates_and_stores_cache(strategy: CacheableFibonacciStrategy):
    """Verifies that the strategy creates and stores the cache correctly."""
    assert strategy.cache_size() == 2
    strategy.calculate(10)
    assert strategy.get_cache_value(10) == 55
    strategy.calculate(20)
    assert strategy.get_cache_value(20) == 6_765
