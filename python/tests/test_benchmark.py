from math import isclose
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from time import sleep
from typing import Generator

import pytest

from src.benchmark import ResultType, TaskType, TimeoutSignal, benchmark_worker

TIMEOUT: int = 1


@pytest.fixture
def parent() -> Generator[Connection, None, None]:
    """A fixture to set up and tear down the benchmark worker process."""
    parent, child = Pipe()
    process = Process(target=benchmark_worker, args=(child,))
    process.start()

    yield parent

    parent.send(None)
    process.join(timeout=float(TIMEOUT))
    assert not process.is_alive(), (
        f"The process {process.pid} should have been terminated, but remained alive and became a zombie process."
    )


def _assert_successful_task(parent: Connection, task: TaskType, expected_time: float):
    """Sends a task to the worker and asserts it completes successfully in time."""
    parent.send(task)
    result: ResultType = parent.recv()

    assert not isinstance(result, Exception), (
        f"The process is not expected to become an exception, but {result.__class__.__name__} was obtained."
    )
    assert isclose(result, expected_time, abs_tol=0.05), (
        f"The process should have taken around {expected_time:,.2f} seconds, but it took {result:,.2f} seconds."
    )


def test_worker_process_success(parent: Connection):
    """Tests a simple, successful task completion."""
    expected_time: float = 0.1
    task: TaskType = (sleep, (expected_time,), TIMEOUT)
    _assert_successful_task(parent, task, expected_time)


def test_worker_handles_timeout_and_continues(parent: Connection):
    """Tests timeout and worker recovery."""
    expected_time1: float = float(TIMEOUT) * 1.5
    task1: TaskType = (sleep, (expected_time1,), TIMEOUT)
    parent.send(task1)
    result1: ResultType = parent.recv()
    assert isinstance(result1, TimeoutSignal), (
        f"It is expected that the result that takes longer than the timeout will return TimeoutSignal, but {result1.__class__.__name__} was obtained."
    )

    expected_time2: float = 0.1
    task2: TaskType = (sleep, (expected_time2,), TIMEOUT)
    _assert_successful_task(parent, task2, expected_time2)
