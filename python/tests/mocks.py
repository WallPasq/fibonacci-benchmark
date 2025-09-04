"""A collection of mock objects and functions for testing purposes."""

from typing import Any
from unittest.mock import Mock

from core.constants import MODULE_NAME
from src.benchmark import FibonacciBenchmark
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy

NUM_DIGITS_LARGE_NUMBER: int = 1_048_577
LARGE_NUMBER: int = 10 ** (NUM_DIGITS_LARGE_NUMBER - 1)


def dummy_calculate(n: int) -> int:
    """
    A simple function to use as a task in our tests.
    Returns the first 8 Fibonacci numbers, or raises an exception.
    """
    fibonacci_numbers: list[int] = [0, 1, 1, 2, 3, 5, 8, 13]

    if n < 0:
        raise ValueError("n must be greater than or equal to 0.")

    if n >= len(fibonacci_numbers):
        # Returns a large number to validate the digit count.
        return LARGE_NUMBER

    return fibonacci_numbers[n]


def mock_enter_context_manager(self: FibonacciBenchmark) -> FibonacciBenchmark:
    """
    A mock __enter__ for the FibonacciBenchmark context manager,
    to avoid creating a Connection and Process.
    """
    return self


class MockFibonacciStrategy(Mock):
    """A mock for the FibonacciStrategy class."""

    __module__: str = MODULE_NAME.format(file_name="mock_fibonacci")

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[Any, Any]):
        super().__init__(spec=FibonacciStrategy, *args, **kwargs)

    @property
    def name(self) -> str:
        return "Mock Fibonacci"

    def calculate(self, n: int) -> int:
        return dummy_calculate(n)


class MockCacheableFibonacciStrategy(Mock):
    """A mock for the CacheableFibonacciStrategy class."""

    __module__ = MODULE_NAME.format(file_name="mock_cacheable_fibonacci")

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[Any, Any]):
        super().__init__(spec=CacheableFibonacciStrategy, *args, **kwargs)

    @property
    def name(self) -> str:
        return "Mock Cacheable Fibonacci"

    def calculate(self, n: int) -> int:
        return dummy_calculate(n)


class NotAStrategy:
    """
    This class does not inherit from FibonacciStrategy,
    to test whether it is ignored.
    """

    pass
