import pytest

from src.discovery import load_strategies
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy

_all_fib_strategies, _all_cache_fib_strategies = load_strategies()
_all_fib_strategies += _all_cache_fib_strategies


@pytest.mark.parametrize("strategy", _all_fib_strategies)
def test_strategy_calculates_correctly(strategy: FibonacciStrategy):
    """Test some known Fibonacci values."""
    fibonacci0: int = strategy.calculate(0)
    assert fibonacci0 == 0, (
        f"{strategy.name} of 0 is expected to be 0, got {fibonacci0:,}."
    )

    fibonacci1: int = strategy.calculate(1)
    assert fibonacci1 == 1, (
        f"{strategy.name} of 1 is expected to be 1, got {fibonacci1:,}."
    )

    fibonacci10: int = strategy.calculate(10)
    assert fibonacci10 == 55, (
        f"{strategy.name} of 10 is expected to be 55, got {fibonacci10:,}."
    )

    fibonacci20: int = strategy.calculate(20)
    assert fibonacci20 == 6_765, (
        f"{strategy.name} of 20 is expected to be 6,765, got {fibonacci20:,}."
    )


@pytest.mark.parametrize("strategy", _all_fib_strategies)
def test_strategy_returns_a_value_error_if_n_is_less_than_zero(
    strategy: FibonacciStrategy,
):
    """Tests if the strategy returns an error if the value passed is less than 0."""
    with pytest.raises(ValueError, match="must be greater than or equal to 0."):
        strategy.calculate(-1)


@pytest.mark.parametrize("strategy", _all_cache_fib_strategies)
def test_strategy_clearing_cache(strategy: CacheableFibonacciStrategy):
    """Verify that clearing the cache actually clears the cache."""
    strategy.calculate(10)
    strategy.clear_cache()
    assert strategy.cache_size() == 2, (
        f"The cache size of {strategy.name} is expected to be 2 after clearing, got {strategy.cache_size()}."
    )


@pytest.mark.parametrize("strategy", _all_cache_fib_strategies)
def test_strategy_creates_and_stores_cache(strategy: CacheableFibonacciStrategy):
    """Verifies that the strategy creates and stores the cache correctly."""
    assert strategy.cache_size() == 2, (
        f"The cache size of {strategy.name} is expected to be 2 when initialized, got {strategy.cache_size()}."
    )

    strategy.calculate(10)
    assert strategy.cache_size() == 11, (
        f"It is expected that there will be 11 elements in the cache after calculating {strategy.name} of 10, got {strategy.cache_size()}."
    )
    assert strategy.get_cache_value(10) == 55, (
        f"{strategy.name} of 10 stored in the cache is expected to be 55, got {strategy.get_cache_value(10):,}."
    )

    strategy.calculate(20)
    assert strategy.cache_size() == 21, (
        f"It is expected that there will be 21 elements in the cache after calculating {strategy.name} of 20, got {strategy.cache_size()}."
    )
    assert strategy.get_cache_value(20) == 6_765, (
        f"{strategy.name} of 20 stored in the cache is expected to be 6,765, got {strategy.get_cache_value(20):,}."
    )
