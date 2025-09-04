from pytest_mock import MockerFixture

from core.exceptions import TimeoutSignal
from core.types import ResultType
from tests.mocks import dummy_calculate
from tests.unit.conftest import setup_benchmark_worker_mocks


def test_benchmark_worker_successful_task(mocker: MockerFixture):
    """
    Tests whether benchmark_worker successfully executes a task,
    measures the execution time, and sends the result back to the connection.
    """
    send_return: ResultType = setup_benchmark_worker_mocks(
        mocker,
        [(dummy_calculate, (5,)), None],
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
    send_return: ResultType = setup_benchmark_worker_mocks(
        mocker,
        [(dummy_calculate, (1,)), None],
        trigger_timeout_handler=True,
    )

    assert isinstance(send_return, TimeoutSignal), (
        f"The return was expected to be TimeoutSignal, but it returned {send_return.__class__.__name__}."
    )


def test_benchmark_worker_sends_errors(mocker: MockerFixture):
    """
    Tests whether the function is able to send errors if they are raised during task execution.
    """
    send_return: ResultType = setup_benchmark_worker_mocks(
        mocker, [(dummy_calculate, (-5,)), None]
    )

    assert (
        isinstance(send_return, ValueError)
        and str(send_return) == "n must be greater than or equal to 0."
    ), (
        "The return value was expected to be a ValueError 'n must be greater than or equal to 0.', "
        f"but it received a {send_return.__class__.__name__} '{str(send_return)}'."
    )
