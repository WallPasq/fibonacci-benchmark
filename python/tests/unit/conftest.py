"""This file contains shared helper functions for the unit tests."""

import importlib
import importlib.util
import signal
import sys
from importlib.machinery import ModuleSpec
from multiprocessing import Process
from multiprocessing.connection import Connection
from pathlib import Path
from types import FrameType, ModuleType
from typing import Callable, Optional, TypeAlias
from unittest.mock import Mock

from pytest_mock import MockerFixture

from core.constants import MODULE_BASE
from core.types import ResultType, TaskType
from src.benchmark import FibonacciBenchmark, benchmark_worker
from tests.mocks import (
    MockCacheableFibonacciStrategy,
    MockFibonacciStrategy,
    mock_enter_context_manager,
)

TimeoutHandlerType: TypeAlias = Optional[Callable[[int, Optional[FrameType]], None]]
handler_storage: dict[int, TimeoutHandlerType] = {}


def _capture_handler(signum: int, handler: TimeoutHandlerType):
    """Captures and stores a signal handler for later use in tests."""
    handler_storage[signum] = handler


def _alarm_side_effect(seconds: int):
    """Simulates a signal alarm by invoking the captured handler."""
    if seconds > 0:
        handler: TimeoutHandlerType = handler_storage.get(signal.SIGALRM)

        if handler:
            handler(signal.SIGALRM, None)


def setup_benchmark_worker_mocks(
    mocker: MockerFixture,
    recv_side_effect: list[TaskType],
    perf_counter_side_effect: Optional[list[float]] = None,
    timeout: int = 1,
    trigger_timeout_handler: bool = False,
) -> ResultType:
    """Sets up mocks and runs the benchmark_worker for testing purposes.

    This helper function orchestrates the testing of the `benchmark_worker`
    by creating a controlled environment with mock external dependencies.
    It simulates task reception, signal handling, and performance timing.

    Specifically, it:
    1.  Mocks `multiprocessing.connection.Connection` to control task input
        and capture output.
    2.  Mocks `signal.signal` and `signal.alarm` to simulate timeout events
        without actual waiting.
    3.  Mocks `src.benchmark.perf_counter` to control the measured execution
        time of tasks.
    4.  Calls `benchmark_worker` with the mock components.
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
        "The alarm was expected to be called twice, "
        f"but it was called {mock_alarm.call_count:,} times."
    )

    first_time_call: int = mock_alarm.call_args_list[0][0][0]
    assert first_time_call == timeout, (
        f"The first alarm call was expected to be in {timeout:,} seconds, "
        f"but it was in {first_time_call:,} seconds."
    )

    second_time_call: int = mock_alarm.call_args_list[1][0][0]
    assert second_time_call == 0, (
        "The second alarm call was expected to be in 0 seconds, disabling it, "
        f"but it was in {second_time_call:,} seconds."
    )

    assert mock_conn.close.call_count == 1, (
        "It was expected that the connection would be called once to be closed, "
        f"but it was called {mock_conn.close.call_count:,} times."
    )

    # Return that the benchmark_worker function sends in the Connection.
    return mock_conn.send.call_args_list[0][0][0]


def setup_strategy_discovery_mocks(
    tmp_path: Path,
    mocker: MockerFixture,
    files_content: Optional[list[tuple[str, str]]] = None,
) -> tuple[Mock, Mock]:
    """Sets up a mock file system and import mechanism for discovery tests.

    This helper function prepares a testing environment by:
    1. Creating a temporary directory structure for mock files.
    2. Adding this temporary directory to the system path.
    3. Patching `src.discovery.Path.glob` to "find" these mock files.
    4. Patching `src.discovery.importlib.import_module` to correctly import
       from the temporary directory.

    This allows for isolated testing of strategy loading without relying on the
    actual file system.

    Args:
        tmp_path: The pytest temporary path fixture.
        mocker: The pytest-mock fixture.
        files_content: An optional list of tuples, each containing a filename
            and its content to be written.

    Returns:
        A tuple containing the mock objects for `src.discovery.Path.glob` and
        `src.discovery.importlib.import_module`.
    """
    # A temporary directory.
    module_dir: Path = tmp_path / MODULE_BASE
    module_dir.mkdir()

    # Mocks to search for files in our temporary directory
    mock_glob: Mock = mocker.patch("src.discovery.Path.glob")
    mock_glob.return_value = []

    if files_content:
        # Create the init file so that the temporary directory is recognized as a package.
        files_content += [("__init__.py", "")]

        for file_name, content in files_content:
            (module_dir / file_name).write_text(content)
            mock_glob.return_value.append(module_dir / file_name)

    # Mock the import_module so that it changes the module_name
    original_import_module: Callable[[str], ModuleType] = importlib.import_module

    def _mock_import_module(module_name: str) -> ModuleType:
        """
        Dynamically imports modules from a temporary directory,
        falling back to the original importer.
        """
        module_name = module_name.split(".")[-1]
        file_path: Path = module_dir / f"{module_name}.py"

        if file_path.exists():
            spec: Optional[ModuleSpec] = importlib.util.spec_from_file_location(
                module_name, file_path
            )
            if spec and spec.loader:
                module: ModuleType = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
        # If the module is not in our temporary directory, fall back to the original importer.
        return original_import_module(module_name)

    mock_import_module: Mock = mocker.patch("src.discovery.importlib.import_module")
    mock_import_module.side_effect = _mock_import_module

    return mock_glob, mock_import_module


def setup_FibonacciBenchmark(
    mocker: MockerFixture, num_runs: int = 1, is_cacheable: bool = False
) -> tuple[FibonacciBenchmark, Mock, Mock, Mock]:
    """Sets up a FibonacciBenchmark instance with mock dependencies for testing.

    This helper function creates a controlled environment for testing the
    FibonacciBenchmark class. It isolates the benchmark from its real
    dependencies, such as multiprocessing components and actual Fibonacci
    strategies, by replacing them with mocks.

    Specifically, it:
    1.  Patches the FibonacciBenchmark's context manager to prevent the
        creation of a real Process and Connection.
    2.  Initializes a mock Fibonacci strategy (either cacheable or not)
        based on the `is_cacheable` parameter.
    3.  Creates an instance of FibonacciBenchmark with the mock strategy.
    4.  Assigns mock Process and Connection objects to the benchmark instance.

    Args:
        mocker: The pytest-mock fixture.
        is_cacheable: If True, uses `MockCacheableFibonacciStrategy`;
            otherwise, uses `MockFibonacciStrategy`.

    Returns:
        A tuple containing the configured `FibonacciBenchmark` instance and
        its associated mock objects (strategy, parent connection, and process).
    """
    mocker.patch.object(FibonacciBenchmark, "__enter__", mock_enter_context_manager)

    if is_cacheable:
        strategy = MockCacheableFibonacciStrategy()
    else:
        strategy = MockFibonacciStrategy()

    benchmark = FibonacciBenchmark(strategy=strategy, num_runs=num_runs)
    benchmark.parent = Mock(spec=Connection)
    benchmark.process = Mock(spec=Process)

    return benchmark, strategy, benchmark.parent, benchmark.process
