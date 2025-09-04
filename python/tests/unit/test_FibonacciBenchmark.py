from itertools import chain, repeat
from math import isclose
from typing import Iterator
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from core.exceptions import TimeoutSignal
from core.types import ResultType
from src.benchmark import FibonacciBenchmark
from tests.mocks import NUM_DIGITS_LARGE_NUMBER
from tests.unit.conftest import setup_FibonacciBenchmark


def _assert_parent_send_calls(
    parent_mock: Mock,
    process_mock: Mock,
    strategy_calculate: Mock,
    expected_ns: list[int],
):
    """Helper function to assert calls to parent.send."""
    expected_total_calls: int = len(expected_ns) + 1
    assert parent_mock.send.call_count == expected_total_calls, (
        f"Expected {expected_total_calls} calls to send, but found {parent_mock.send.call_count:,}"
    )

    for i, n in enumerate(expected_ns):
        value_sent = parent_mock.send.call_args_list[i][0][0]
        assert value_sent == (strategy_calculate, (n,)), (
            f"Mismatch in call {i + 1}: expected ({strategy_calculate.__qualname__}, ({n},)), got {value_sent}"
        )

    last_value_sent = parent_mock.send.call_args_list[-1][0][0]
    assert last_value_sent is None, (
        f"Expected last call to be None, but got {last_value_sent}"
    )

    assert process_mock.join.call_count == 1, (
        "The join method of the process should have been called once to close it, "
        f"but it was called {process_mock.join.call_count:,} times."
    )


def test_FibonacciBenchmark_FibonacciStrategy_run_successful(mocker: MockerFixture):
    """
    Tests that `FibonacciBenchmark.run` correctly finds the optimal `n`
    based on a series of mock worker execution times.
    """
    benchmark, strategy, parent, process = setup_FibonacciBenchmark(mocker)

    parent.recv.side_effect = [0.5, 0.9, 1.2, 0.99, 1.2]
    best_n, num_digits = benchmark.run()

    assert best_n == 3, (
        "Due to the defined return times in recv.side_effect, "
        f"the result should have been 3, but it was {best_n:,}."
    )
    assert num_digits == 1, (
        f"The number of digits in 2 is 1, but it obtained {num_digits:,}."
    )

    expected_ns: list[int] = [1, 2, 4, 3, 4]
    _assert_parent_send_calls(parent, process, strategy.calculate, expected_ns)


def test_FibonacciBenchmark_CacheableFibonacciStrategy_clear_cache_and_run_successful(
    mocker: MockerFixture,
):
    """
    Tests that `clear_cache` is called on a `CacheableFibonacciStrategy`
    before each run to ensure fair measurements and if it correctly finds
    the optimal `n` based on a series of mock worker execution times.
    """
    benchmark, strategy, parent, process = setup_FibonacciBenchmark(
        mocker, is_cacheable=True
    )

    parent.recv.side_effect = [0.5, 0.9, 1.2, 0.99, 1.2]
    best_n, num_digits = benchmark.run()

    assert best_n == 3, (
        "Due to the defined return times in recv.side_effect, "
        f"the result should have been 3, but it was {best_n:,}."
    )
    assert num_digits == 1, (
        f"The number of digits in 2 is 1, but it obtained {num_digits:,}."
    )

    assert strategy.clear_cache.call_count == 5, (
        "The clear_cache method of CacheableFibonacciStrategy should be called 5 times, "
        f"but it was called {strategy.clear_cache.call_count:,} times."
    )

    expected_ns: list[int] = [1, 2, 4, 3, 4]
    _assert_parent_send_calls(parent, process, strategy.calculate, expected_ns)


def test_FibonacciBenchmark_raises_ValueError(mocker: MockerFixture):
    """
    Tests that `FibonacciBenchmark.run` correctly propagates exceptions
    received from the worker process.
    """
    benchmark, strategy, parent, process = setup_FibonacciBenchmark(mocker)

    # This needs to be done so that Mock sends the exception using the send command instead of raising it.
    simulated_error = ValueError("Simulated error.")
    recv_side_effect: Iterator[ResultType] = iter([0.5, 0.8, 0.9, simulated_error])
    parent.recv.side_effect = lambda: next(recv_side_effect)

    with pytest.raises(ValueError, match="Simulated error."):
        benchmark.run()

    expected_ns: list[int] = [1, 2, 4, 8]
    _assert_parent_send_calls(parent, process, strategy.calculate, expected_ns)


def test_FibonacciBenchmark_run_handles_timeouts_and_verifies_large_number_digits(
    mocker: MockerFixture,
):
    """
    Tests whether `FibonacciBenchmark.run` correctly identifies the last successful `n`,
    calculates the number of digits for its large result, and whether the average execution
    time calculation ignores `TimeoutSignal` exceptions.
    """
    benchmark, strategy, parent, process = setup_FibonacciBenchmark(mocker, num_runs=3)

    # Creates a spy to obtain the values returned by _get_median_runtime.
    spy_get_median_runtime = mocker.spy(FibonacciBenchmark, "_get_median_runtime")
    simulated_timeout = TimeoutSignal("Simulated timeout.")

    # Repeats the TimeoutSignal indefinitely to test whether it is ignored,
    # and the method returns the highest value found.
    recv_side_effect = chain(
        iter([0.3, 0.3, 0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8, 0.9]),
        repeat(simulated_timeout),
    )
    parent.recv.side_effect = lambda: next(recv_side_effect)
    best_n, num_digits = benchmark.run()

    assert best_n == 8, (
        "Due to the defined return times in recv.side_effect, "
        f"the result should have been 8, but it was {best_n:,}."
    )
    assert num_digits == NUM_DIGITS_LARGE_NUMBER, (
        f"The number of digits in 10 raised to the power of {NUM_DIGITS_LARGE_NUMBER - 1:,} "
        f"is {NUM_DIGITS_LARGE_NUMBER:,}, but it obtained {num_digits:,}."
    )

    for i, median in enumerate([0.3, 0.5, 0.7, 0.9]):
        assert isclose(spy_get_median_runtime.spy_return_list[i], median), (
            f"The {i + 1}th median should have been {median:,} but was "
            f"{spy_get_median_runtime.spy_return_list[i]:,}."
        )

    expected_ns: list[int] = [n for n in [1, 2, 4, 8, 16, 12, 9] for _ in range(3)]
    _assert_parent_send_calls(parent, process, strategy.calculate, expected_ns)
