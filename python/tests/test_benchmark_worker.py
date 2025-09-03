import signal
from multiprocessing.connection import Connection
from types import FrameType
from typing import Callable, Optional, TypeAlias
from unittest.mock import Mock

from pytest_mock import MockerFixture

from core.exceptions import TimeoutSignal
from core.types import ResultType, TaskType
from src.benchmark import benchmark_worker

TimeoutHandlerType: TypeAlias = Optional[Callable[[int, Optional[FrameType]], None]]


def _dummy_task(n: int) -> int:
    """A simple function to use as a task in our tests."""
    if n < 0:
        raise ValueError("n must be greater than or equal to 0.")

    return n


def _setup_benchmark_worker_signal_and_perf_counter_mocks(
    mocker: MockerFixture,
    recv_side_effect: list[TaskType],
    perf_counter_side_effect: Optional[list[float]] = None,
    timeout: int = 1,
    trigger_timeout_handler: bool = False,
) -> ResultType:
    """Sets up mocks and runs the benchmark_worker for testing purposes.

    This helper function orchestrates the testing of the `benchmark_worker`
    by creating a controlled environment with mocked external dependencies.
    It simulates task reception, signal handling, and performance timing.

    Specifically, it:
    1.  Mocks `multiprocessing.connection.Connection` to control task input
        and capture output.
    2.  Mocks `signal.signal` and `signal.alarm` to simulate timeout events
        without actual waiting.
    3.  Mocks `src.benchmark.perf_counter` to control the measured execution
        time of tasks.
    4.  Calls `benchmark_worker` with the mocked components.
    5.  Performs a standard set of assertions to verify that the worker
        interacts correctly with the mocks (e.g., setting and clearing alarms,
        sending results, closing the connection).

    Args:
        mocker: The pytest-mock fixture.
        recv_side_effect: A list of tasks for the connection mock to "receive".
            The worker loop terminates when it receives `None`.
        perf_counter_side_effect: An optional side effect for `time.perf_counter`
            to simulate task execution times.
        timeout: The timeout value in seconds to be passed to the worker and
            used in assertions.
        trigger_timeout_handler: If True, simulates a timeout by directly
            triggering the timeout handler.

    Returns:
        The value sent back by the worker over the connection, which
        represents the result of the task. This is either the execution
        time as a float or an exception object.
    """
    mock_conn: Mock = Mock(spec=Connection)
    mock_conn.recv.side_effect = recv_side_effect
    mock_signal: Mock = mocker.patch("signal.signal")
    mock_alarm: Mock = mocker.patch("signal.alarm")

    # Tests whether the _timeout_handler is triggered.
    if trigger_timeout_handler:
        handler_storage: dict[int, TimeoutHandlerType] = {}

        def _capture_handler(signum: int, handler: TimeoutHandlerType):
            handler_storage[signum] = handler

        def _alarm_side_effect(seconds: int):
            if seconds > 0:
                handler: TimeoutHandlerType = handler_storage.get(signal.SIGALRM)

                if handler:
                    handler(signal.SIGALRM, None)

        mock_signal.side_effect = _capture_handler
        mock_alarm.side_effect = _alarm_side_effect

    # Sets values for perf_counter to return.
    if perf_counter_side_effect:
        mocker.patch("src.benchmark.perf_counter", side_effect=perf_counter_side_effect)

    benchmark_worker(mock_conn, timeout=timeout)

    assert mock_conn.recv.called, (
        "The connection is expected to receive something, but it has not received anything."
    )

    assert mock_conn.send.called, (
        "The connection is expected to send something, but it has not sent anything."
    )

    assert mock_alarm.call_count == 2, (
        f"The alarm was expected to be called twice, but it was called {mock_alarm.call_count:,} times."
    )

    first_time_call: int = mock_alarm.call_args_list[0][0][0]
    assert first_time_call == timeout, (
        f"The first alarm call was expected to be in {timeout:,} seconds, but it was in {first_time_call:,} seconds."
    )

    second_time_call: int = mock_alarm.call_args_list[1][0][0]
    assert second_time_call == 0, (
        "It was expected that the second call to the alarm would deactivate it, "
        f"passing 0 seconds as an argument, but {second_time_call:,} seconds were passed instead."
    )

    assert mock_conn.close.call_count == 1, (
        "It was expected that the connection would be called once to be closed, "
        f"but it was called {mock_conn.close.call_count:,} times."
    )

    return mock_conn.send.call_args_list[0][0][0]


def test_benchmark_worker_successful_task(mocker: MockerFixture):
    """
    Tests whether benchmark_worker successfully executes a task,
    measures the execution time, and sends the result back to the connection.
    """
    send_return: ResultType = _setup_benchmark_worker_signal_and_perf_counter_mocks(
        mocker,
        [(_dummy_task, (5,)), None],
        perf_counter_side_effect=[1.0, 1.5],
        timeout=5,
    )

    assert send_return == 0.5, (
        f"The function was expected to return 0.5 (1.5 - 1.0), but it returned {send_return:,}."
    )


def test_benchmark_worker_task_timeout(mocker: MockerFixture):
    """
    Tests timeout behavior without actually waiting. We use a mock to simulate that the operating
    system alarm has been triggered, causing the `TimeoutSignal` exception to be raised.
    """
    send_return: ResultType = _setup_benchmark_worker_signal_and_perf_counter_mocks(
        mocker,
        [(_dummy_task, (1,)), None],
        trigger_timeout_handler=True,
    )

    assert isinstance(send_return, TimeoutSignal), (
        f"The return was expected to be TimeoutSignal, but it returned {send_return.__class__.__name__}."
    )


def test_benchmark_worker_sends_errors(mocker: MockerFixture):
    """
    Tests whether the function is able to send errors if they are raised during task execution.
    """
    send_return: ResultType = _setup_benchmark_worker_signal_and_perf_counter_mocks(
        mocker, [(_dummy_task, (-5,)), None]
    )

    assert (
        isinstance(send_return, ValueError)
        and str(send_return) == "n must be greater than or equal to 0."
    ), (
        "The return value was expected to be a ValueError 'n must be greater than or equal to 0.', "
        f"but it received a {send_return.__class__.__name__} '{str(send_return)}'."
    )
