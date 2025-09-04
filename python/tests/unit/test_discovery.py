from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from core.constants import PROTOCOL_FILE
from core.exceptions import NoStrategiesFoundError
from src.discovery import load_strategies
from tests.unit.conftest import setup_strategy_discovery_mocks


def test_load_strategies_successfully(tmp_path: Path, mocker: MockerFixture):
    """Tests whether the function successfully discovers and categorizes strategies."""
    files_content: list[tuple[str, str]] = [
        (
            "mock_fibonacci.py",
            "from tests.mocks import MockFibonacciStrategy",
        ),  # It should be classified as FibonacciStrategy.
        (
            "mock_cacheable_fibonacci.py",
            "from tests.mocks import MockCacheableFibonacciStrategy",
        ),  # It should be classified as CacheableFibonacciStrategy.
        (
            PROTOCOL_FILE,
            "class FibonacciStrategy: pass",
        ),  # It should be ignored, because it's PROTOCOL_FILE
        (
            ".internal.py",
            "class Internal: pass",
        ),  # It should be ignored, because it starts with .
        (
            "not_a_strategy.py",
            "from tests.mocks import NotAStrategy",
        ),  # It should not be imported, as it does not follow the FibonacciStrategy protocol.
    ]

    setup_strategy_discovery_mocks(tmp_path, mocker, files_content)
    fib_strategies, cache_fib_strategies = load_strategies()

    assert len(fib_strategies) == 1, (
        "Only one FibonacciStrategy is expected to be returned, "
        f"but {len(fib_strategies):,} were returned."
    )

    assert len(cache_fib_strategies) == 1, (
        "Only one CacheableFibonacciStrategy is expected to be returned, "
        f"but {len(cache_fib_strategies):,} were returned."
    )

    assert fib_strategies[0].name == "Mock Fibonacci", (
        "The name of the returned strategy should be Mock Fibonacci, "
        f"but it returned {fib_strategies[0].name}."
    )

    assert cache_fib_strategies[0].name == "Mock Cacheable Fibonacci", (
        "The name of the returned strategy should be Mock Cacheable Fibonacci, "
        f"but it returned {cache_fib_strategies[0].name}."
    )


def test_load_strategies_when_no_strategies_are_found(
    tmp_path: Path, mocker: MockerFixture
):
    """
    Tests whether the NoStrategiesFoundError exception is raised when the directory is empty.
    """
    setup_strategy_discovery_mocks(tmp_path, mocker)

    with pytest.raises(NoStrategiesFoundError, match="No strategies loaded."):
        load_strategies()
