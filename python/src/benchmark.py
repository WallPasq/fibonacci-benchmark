import signal
from math import floor, log10
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from statistics import median
from time import perf_counter
from types import FrameType, TracebackType
from typing import Optional, Type

from core.exceptions import TimeoutSignal
from core.types import ResultType, TaskType
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy


def _timeout_handler(signum: int, handler: Optional[FrameType]):
    """A simple signal handler that raises the custom TimeoutSignal exception."""
    raise TimeoutSignal("Task execution timed out.")


def benchmark_worker(conn: Connection, timeout: int):
    """Executes tasks in a separate process with a timeout.

    This function is designed to be the target of a `multiprocessing.Process`.
    It enters an infinite loop, receiving tasks through a connection. It uses
    `signal.SIGALRM` to enforce a timeout on each task.

    The communication protocol is as follows:
    - The worker receives a task tuple: `(function, args)`.
    - An alarm is set using the `timeout` value. If the task takes too long,
      `_timeout_handler` raises a `TimeoutSignal`.
    - The worker executes `function(*args)` and measures the execution time.
    - On success, the elapsed time (float) is sent back.
    - On timeout, a `TimeoutSignal` exception is sent back.
    - For other exceptions, the exception object is sent back.
    - The worker terminates upon receiving `None`.

    Args:
        conn (Connection): The connection for receiving tasks and sending results.
        timeout (int): The time limit for executing the task in seconds.
    """
    signal.signal(signal.SIGALRM, _timeout_handler)

    while True:
        task: TaskType = conn.recv()

        if task is None:
            conn.close()
            break

        func, args = task
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


class FibonacciBenchmark:
    """
    Manages and executes a benchmark for a single Fibonacci strategy.
    """

    def __init__(
        self,
        strategy: FibonacciStrategy,
        num_runs: int = 5,
        timeout: int = 1,
    ):
        self.strategy: FibonacciStrategy = strategy
        self.num_runs: int = num_runs
        self.timeout: int = timeout

    def run(self) -> tuple[int, int]:
        """
        Runs the full benchmark for the strategy and returns the result.

        Returns:
            tuple[int, int]: The maximum Fibonacci number calculated before
                the time limit and the number of digits in the result.
        """
        print(f"--- Testing: ({self.strategy.name}) ---")
        with self:
            low, high = self._exponential_search()
            best_n: int = self._binary_search(low, high)
            final_fib_num: int = self.strategy.calculate(best_n)
            num_digits: int = floor(log10(final_fib_num)) + 1

            return best_n, num_digits

    def _get_median_runtime(self, n: int) -> float:
        """
        Measures the median runtime for the configured strategy at input size `n`.

        This method executes the `self.strategy.calculate(n)` method multiple times,
        as specified by `self.num_runs`, to obtain a stable performance measurement.
        Each execution happens in a separate process, managed by `self.parent`,
        to safely handle timeouts.

        To ensure fair and independent measurements, it clears the cache for any
        cache-aware strategies (e.g., `CacheableFibonacciStrategy`) before each run.
        The median is used to provide a robust result that is less sensitive to
        outliers than a simple average.

        Args:
            n (int): The input value to be passed to the strategy's `calculate` method.

        Returns:
            float: The median runtime in seconds from all successful runs. If all
                runs fail (e.g., due to timeouts), it returns the instance's
                `self.timeout` value as a failure signal.

        Raises:
            Exception: Propagates any exception that occurs during the execution
                of the strategy in the child process.
        """
        runtimes: list[float] = []

        for _ in range(self.num_runs):
            if isinstance(self.strategy, CacheableFibonacciStrategy):
                self.strategy.clear_cache()

            self.parent.send((self.strategy.calculate, (n,)))
            runtime: ResultType = self.parent.recv()

            if isinstance(runtime, TimeoutSignal):
                continue

            if isinstance(runtime, Exception):
                raise runtime

            runtimes.append(runtime)

        if not runtimes:
            return self.timeout

        return median(runtimes)

    def _exponential_search(self) -> tuple[int, int]:
        """
        Finds a bounding range for a time-limited operation using an exponential search.

        This method tests increasing powers of 2 (n=1, 2, 4, 8...) until the
        median runtime of the operation for `n` exceeds `self.timeout`.

        Returns:
            tuple[int, int]: A tuple `(low, high)`, where `high` is the first power of 2 that
                exceeded the timeout, and `low` is the previous power of 2 that did not.
        """
        n: int = 1
        last_n: int = 1

        while True:
            median_runtime: float = self._get_median_runtime(n)
            print(f"Test {n:,} - median runtime", end=" ")

            if median_runtime < self.timeout:
                print(f"{median_runtime:,.6f}s.")
            else:
                print(f">{self.timeout:,.6f}s.")
                break

            last_n = n
            n *= 2

        return last_n, n

    def _binary_search(self, low: int, high: int) -> int:
        """
        Performs a binary search to find the largest `n` that meets a time constraint.

        This method efficiently searches the integer range between `low` and `high`
        to pinpoint the highest possible value (`n`) for which the median runtime of
        an operation, calculated by `_get_median_runtime(n)`, is less than
        the instance's `self.timeout`.

        It progressively halves the search space until the optimal value is found.

        Args:
            low (int): The lower bound of the search range (inclusive).
            high (int): The upper bound of the search range (inclusive).

        Returns:
            int: The largest integer `n` found within the range whose operation
                runtime did not exceed the timeout.
        """
        best_n: int = low

        while True:
            mid: int = (low + high) // 2
            if mid == 0 or mid == best_n:
                break

            median_runtime: float = self._get_median_runtime(mid)
            print(f"Test {mid:,} - median runtime", end=" ")

            if median_runtime < self.timeout:
                best_n = mid
                low = mid + 1
                print(f"{median_runtime:,.6f}s.")
            else:
                high = mid - 1
                print(f">{self.timeout:,.6f}s.")

        return best_n

    def __enter__(self):
        """Context manager entry: starts the worker process."""
        self.parent, child = Pipe()
        self.process: Process = Process(
            target=benchmark_worker, args=(child, self.timeout)
        )
        self.process.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        """Context manager exit: stops the worker process."""
        self.parent.send(None)
        self.process.join(timeout=self.timeout)
