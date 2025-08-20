import signal
from multiprocessing.connection import Connection
from time import perf_counter
from types import FrameType
from typing import Any, Callable, TypeAlias

TaskType: TypeAlias = tuple[Callable[..., Any], tuple[Any, ...], int] | None
ResultType: TypeAlias = float | Exception


class TimeoutSignal(Exception):
    """Raised when the subprocess takes longer than the defined timeout."""

    pass


def _timeout_handler(signum: int, frame: FrameType | None) -> None:
    """A simple signal handler that raises the custom TimeoutSignal exception."""
    raise TimeoutSignal("Task execution timed out.")


def benchmark_worker(conn: Connection):
    """Executes tasks in a separate process with a timeout.

    This function is designed to be the target of a `multiprocessing.Process`.
    It enters an infinite loop, receiving tasks through a connection. It uses
    `signal.SIGALRM` to enforce a timeout on each task.

    The communication protocol is as follows:
    - The worker receives a task tuple: `(function, args, timeout)`.
    - An alarm is set using the `timeout` value. If the task takes too long,
      `_timeout_handler` raises a `TimeoutSignal`.
    - The worker executes `function(*args)` and measures the execution time.
    - On success, the elapsed time (float) is sent back.
    - On timeout, a `TimeoutSignal` exception is sent back.
    - For other exceptions, the exception object is sent back.
    - The worker terminates upon receiving `None`.

    Args:
        conn: The connection for receiving tasks and sending results.
    """
    signal.signal(signal.SIGALRM, _timeout_handler)

    while True:
        task: TaskType = conn.recv()

        if task is None:
            conn.close()
            break

        func, args, timeout = task
        result: ResultType

        try:
            signal.alarm(timeout)

            start_time: float = perf_counter()
            func(*args)
            end_time: float = perf_counter()
            result = end_time - start_time
        except Exception as e:
            result = e
        finally:
            signal.alarm(0)

        conn.send(result)
