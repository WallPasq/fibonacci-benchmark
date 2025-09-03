from itertools import chain, repeat
from math import isclose
from multiprocessing import Process
from multiprocessing.connection import Connection
from typing import Callable, Iterator, cast
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from core.exceptions import TimeoutSignal
from core.types import ResultType
from src.benchmark import FibonacciBenchmark
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy


class MockFibonacciStrategy(FibonacciStrategy):
    """A mock for the FibonacciStrategy class."""

    @property
    def name(self) -> str:
        return "Mocked Fibonacci"

    def calculate(self, n: int) -> int:
        return n


class MockCacheableFibonacciStrategy(CacheableFibonacciStrategy):
    """A mock for the CacheableFibonacciStrategy class."""

    _cache: list[int] = []
    clear_cache_call_count: int = 0

    @property
    def name(self) -> str:
        return "Mocked Cacheable Fibonacci"

    def calculate(self, n: int) -> int:
        return n

    def clear_cache(self):
        self.clear_cache_call_count += 1

    def cache_size(self) -> int:
        return 0

    def get_cache_value(self, n: int) -> int:
        return n


def _mocked_enter_context_manager(self: FibonacciBenchmark) -> FibonacciBenchmark:
    """
    A mocked __enter__ for the FibonacciBenchmark context manager,
    to avoid creating a Connection and Process.
    """
    return self


def test_FibonacciBenchmark_run_successful(mocker: MockerFixture):
    """
    Tests that `FibonacciBenchmark.run` correctly finds the optimal `n`
    based on a series of mocked worker execution times.
    """
    strategy: MockFibonacciStrategy = MockFibonacciStrategy()
    mocker.patch.object(FibonacciBenchmark, "__enter__", _mocked_enter_context_manager)
    benchmark: FibonacciBenchmark = FibonacciBenchmark(
        strategy=strategy, num_runs=1, timeout=1
    )
    benchmark.parent = Mock(spec=Connection)
    benchmark.process = Mock(spec=Process)

    benchmark.parent.recv.side_effect = [0.5, 0.9, 1.2, 0.99, 1.2]
    best_n, num_digits = benchmark.run()

    assert best_n == 3, (
        "Due to the defined return times in recv.side_effect, "
        f"the result should have been 3, but it was {best_n:,}."
    )

    assert num_digits == 1, (
        f"The number of digits in 3 is 1, but it obtained {num_digits:,}."
    )

    assert benchmark.process.join.call_count == 1, (
        "The join method of the process should have been called once to close it, "
        f"but it was called {benchmark.process.join.call_count:,} times."
    )

    send_number_calls: int = len(benchmark.parent.send.call_args_list)
    assert send_number_calls == 6, (
        "It was expected that 6 calls would be made to the send method, "
        f"but {send_number_calls:,} were made."
    )

    # Expected returns from _exponential_search and _binary_search
    for i, n in enumerate([1, 2, 4, 3, 4]):
        value_sent: tuple[Callable[[int], int], int] = (
            benchmark.parent.send.call_args_list[i][0][0]
        )
        assert value_sent == (strategy.calculate, (n,)), (
            f"The {i + 1}th call to the send method should have sent the"
            f"tuple (MockFibonacciStrategy.calculate, {n:,}), but it sent {value_sent} instead."
        )

    value_sent = benchmark.parent.send.call_args_list[-1][0][0]
    assert value_sent is None, (
        f"The last call to the send method should have sent None, but it sent {value_sent} instead."
    )


def test_FibonacciBenchmark_clear_cache_CacheableFibonacciStrategy(
    mocker: MockerFixture,
):
    """
    Tests that `clear_cache` is called on a `CacheableFibonacciStrategy`
    before each run to ensure fair measurements.
    """
    strategy: MockCacheableFibonacciStrategy = MockCacheableFibonacciStrategy()
    mocker.patch.object(FibonacciBenchmark, "__enter__", _mocked_enter_context_manager)
    benchmark: FibonacciBenchmark = FibonacciBenchmark(
        strategy=strategy, num_runs=1, timeout=1
    )
    benchmark.parent = Mock(spec=Connection)
    benchmark.process = Mock(spec=Process)

    benchmark.parent.recv.side_effect = [0.5, 0.9, 1.2, 0.99, 1.2]
    benchmark.run()
    clear_cache_call_count: int = cast(
        MockCacheableFibonacciStrategy, benchmark.strategy
    ).clear_cache_call_count

    assert clear_cache_call_count == 5, (
        "The clear_cache method of CacheableFibonacciStrategy should be called 5 times, "
        f"but it was called {clear_cache_call_count:,} times."
    )


def test_FibonacciBenchmark_raises_ValueError(mocker: MockerFixture):
    """
    Tests that `FibonacciBenchmark.run` correctly propagates exceptions
    received from the worker process.
    """
    strategy: MockFibonacciStrategy = MockFibonacciStrategy()
    mocker.patch.object(FibonacciBenchmark, "__enter__", _mocked_enter_context_manager)
    benchmark: FibonacciBenchmark = FibonacciBenchmark(
        strategy=strategy, num_runs=1, timeout=1
    )
    benchmark.parent = Mock(spec=Connection)
    benchmark.process = Mock(spec=Process)

    # This needs to be done so that Mock sends the exception using the send command instead of raising it.
    simulated_error: ValueError = ValueError("Simulated error.")
    recv_side_effect: Iterator[ResultType] = iter([0.5, 0.8, 0.9, simulated_error])
    benchmark.parent.recv.side_effect = lambda: next(recv_side_effect)

    # Should return an error when testing 8 in _exponential_search
    with pytest.raises(ValueError):
        benchmark.run()

    assert benchmark.process.join.call_count == 1, (
        "The join method of the process should have been called once to close it, "
        f"but it was called {benchmark.process.join.call_count:,} times."
    )

    send_number_calls: int = len(benchmark.parent.send.call_args_list)
    assert send_number_calls == 5, (
        "It was expected that 5 calls would be made to the send method, "
        f"but {send_number_calls:,} were made."
    )

    # Expected returns from _exponential_search
    for i, n in enumerate([1, 2, 4, 8]):
        value_sent: tuple[Callable[[int], int], int] = (
            benchmark.parent.send.call_args_list[i][0][0]
        )
        assert value_sent == (strategy.calculate, (n,)), (
            f"The {i + 1}th call to the send method should have sent the"
            f"tuple (MockFibonacciStrategy.calculate, {n:,}), but it sent {value_sent} instead."
        )

    value_sent = benchmark.parent.send.call_args_list[-1][0][0]
    assert value_sent is None, (
        f"The last call to the send method should have sent None, but it sent {value_sent} instead."
    )


def test_FibonacciBenchmark_handles_TimeoutSignal_correctly(mocker: MockerFixture):
    """
    Tests that `_get_median_runtime` correctly handles `TimeoutSignal` by
    ignoring timed-out runs when calculating the median.
    """
    strategy: MockFibonacciStrategy = MockFibonacciStrategy()
    mocker.patch.object(FibonacciBenchmark, "__enter__", _mocked_enter_context_manager)

    # Mock get_median_runtimes to store the returned medians.
    medians: list[float] = []
    real_get_median_runtime: Callable[[FibonacciBenchmark, int], int] = getattr(
        FibonacciBenchmark, "_get_median_runtime"
    )

    def _mock_get_median_runtime(self: FibonacciBenchmark, n: int) -> int:
        median: float = real_get_median_runtime(self, n)
        medians.append(median)
        return median

    mocker.patch.object(
        FibonacciBenchmark, "_get_median_runtime", _mock_get_median_runtime
    )

    benchmark: FibonacciBenchmark = FibonacciBenchmark(
        strategy=strategy, num_runs=3, timeout=1
    )
    benchmark.parent = Mock(spec=Connection)
    benchmark.process = Mock(spec=Process)

    # This needs to be done so that Mock sends the exception using the send command instead of raising it.
    simulated_timeout: TimeoutSignal = TimeoutSignal("Simulated timeout.")
    recv_side_effect: Iterator[ResultType] = chain(
        iter(
            [
                0.3,
                0.3,  # Should return a value close to 0.3 (median of three runs)
                0.3,
                0.4,
                0.5,  # Should return a value close to 0.5 (median of three runs)
                0.5,
                0.6,
                0.7,  # Should return a value close to 0.7 (median of three runs)
                0.8,
                0.9,  # Should return a value close to 0.9 (simulated_timeout should be ignored)
            ]
        ),
        repeat(simulated_timeout),
    )

    benchmark.parent.recv.side_effect = lambda: next(recv_side_effect)

    best_n, num_digits = benchmark.run()

    assert best_n == 8, (
        "Due to the defined return times in recv.side_effect, "
        f"the result should have been 8, but it was {best_n:,}."
    )

    assert num_digits == 1, (
        f"The number of digits in 8 is 1, but it obtained {num_digits:,}."
    )

    for i, median in enumerate([0.3, 0.5, 0.7, 0.9]):
        assert isclose(medians[i], median), (
            f"The {i + 1}th median should have been {median:,} but was {medians[i]:,}."
        )

    assert benchmark.process.join.call_count == 1, (
        "The join method of the process should have been called once to close it, "
        f"but it was called {benchmark.process.join.call_count:,} times."
    )

    send_number_calls: int = len(benchmark.parent.send.call_args_list)
    assert send_number_calls == 22, (
        "It was expected that 22 calls would be made to the send method, "
        f"but {send_number_calls:,} were made."
    )

    # Expected returns from _exponential_search and _binary_search
    for i, n in enumerate([n for n in [1, 2, 4, 8, 16, 12, 9] for _ in range(3)]):
        value_sent: tuple[Callable[[int], int], tuple[int]] = (
            benchmark.parent.send.call_args_list[i][0][0]
        )
        assert value_sent == (strategy.calculate, (n,)), (
            f"The {i + 1}th call to the send method should have sent the "
            f"tuple (MockFibonacciStrategy.calculate, {n:,}), but it sent {value_sent} instead."
        )

    value_sent = benchmark.parent.send.call_args_list[-1][0][0]
    assert value_sent is None, (
        f"The last call to the send method should have sent None, but it sent {value_sent} instead."
    )
