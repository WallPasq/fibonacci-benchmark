from src.strategies.memoization import Memoization
from src.strategies.protocol import CacheableFibonacciStrategy


def test_memoization_strategy_conforms_to_protocol():
    """Verify that the memoization strategy implements the CacheableFibonacciStrategy protocol."""
    strategy = Memoization()
    assert isinstance(strategy, CacheableFibonacciStrategy)


def test_memoization_strategy_calculates_correctly():
    """Test some known Fibonacci values."""
    strategy = Memoization()
    assert strategy.calculate(0) == 0
    assert strategy.calculate(1) == 1
    assert strategy.calculate(10) == 55
    assert strategy.calculate(20) == 6_765


def test_memoization_strategy_creates_and_stores_cache():
    """Verifies that the memoization strategy creates and stores the cache correctly."""
    strategy = Memoization()
    assert len(strategy._cache) == 2  # pyright: ignore[reportPrivateUsage]
    strategy.calculate(10)
    assert strategy._cache[10] == 55  # pyright: ignore[reportPrivateUsage]
    strategy.calculate(20)
    assert strategy._cache[20] == 6_765  # pyright: ignore[reportPrivateUsage]


def test_memoization_clearing_cache():
    """Verify that clearing the cache actually clears the cache."""
    strategy = Memoization()
    strategy.calculate(10)
    strategy.clear_cache()
    assert len(strategy._cache) == 2  # pyright: ignore[reportPrivateUsage]
