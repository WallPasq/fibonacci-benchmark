import importlib
import importlib.util
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from core.constants import MODULE_BASE, MODULE_NAME, PROTOCOL_FILE
from core.exceptions import NoStrategiesFoundError
from src.discovery import load_strategies
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy


class MockFibonacciStrategy(FibonacciStrategy):
    """A mock for the FibonacciStrategy class, to perform tests without relying on the actual files."""

    # Mock to return the name that corresponds to the function's operation.
    __module__: str = MODULE_NAME.format(file_name="mocked_fibonacci")

    @property
    def name(self) -> str:
        return "Mocked Fibonacci"

    def calculate(self, n: int) -> int:
        return n


class MockCacheableFibonacciStrategy(CacheableFibonacciStrategy):
    """A mock for the CacheableFibonacciStrategy class, to perform tests without relying on the actual files."""

    # Mock to return the name that corresponds to the function's operation.
    __module__: str = MODULE_NAME.format(file_name="mocked_cacheable_fibonacci")

    @property
    def name(self) -> str:
        return "Mocked Cacheable Fibonacci"

    def calculate(self, n: int) -> int:
        return n

    def clear_cache(self):
        pass

    def cache_size(self) -> int:
        return 0

    def get_cache_value(self, n: int) -> int:
        return n


class NotAStrategy:
    """This class does not inherit from FibonacciStrategy, to test whether it is ignored."""

    pass


def _setup_strategy_discovery_mocks(
    tmp_path: Path,
    mocker: MockerFixture,
    files_content: Optional[list[tuple[str, str]]] = None,
):
    """Sets up a mocked file system and import mechanism for discovery tests.

    This helper function prepares a testing environment by:
    1. Creating a temporary directory structure for mocked files.
    2. Adding this temporary directory to the system path.
    3. Patching `pathlib.Path.glob` to "find" these mocked files.
    4. Patching `importlib.import_module` to correctly import from the
       temporary directory.

    This allows for isolated testing of strategy loading without relying on the
    actual file system.

    Args:
        tmp_path: The pytest temporary path fixture, used to modify `sys.path`.
        mocker: The pytest-mock fixture.
        monkeypatch: The pytest monkeypatch fixture.
        files_content: An optional list of tuples, each containing a filename
            and its content to be written.
    """
    # A temporary directory.
    module_dir: Path = tmp_path / MODULE_BASE
    module_dir.mkdir()

    # Mocks to search for files in our temporary directory
    mock_glob: Mock = mocker.patch("pathlib.Path.glob")
    mock_glob.return_value = []

    # Create the init file so that the temporary directory is recognized as a package.
    (module_dir / "__init__.py").write_text("")
    mock_glob.return_value.append(module_dir / "__init__.py")

    if files_content:
        for file_name, content in files_content:
            (module_dir / file_name).write_text(content)
            mock_glob.return_value.append(module_dir / file_name)

    # Mock the import_module so that it changes the module_name
    original_import_module: Callable[[str], ModuleType] = importlib.import_module

    def mocked_import_module(module_name: str) -> ModuleType:
        module_name = module_name.split(".")[-1]
        file_path: Path = module_dir / f"{module_name}.py"

        if file_path.exists():
            spec: Optional[ModuleSpec] = importlib.util.spec_from_file_location(
                module_name, file_path
            )
            if spec and spec.loader:
                module: ModuleType = importlib.util.module_from_spec(spec)
                print(module)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
        # If the module is not in our temporary directory, fall back to the original importer.
        return original_import_module(module_name)

    mock_import_module: Mock = mocker.patch("importlib.import_module")
    mock_import_module.side_effect = mocked_import_module


def test_load_strategies_successfully(tmp_path: Path, mocker: MockerFixture):
    """Tests whether the function successfully discovers and categorizes strategies."""

    files_content: list[tuple[str, str]] = [
        (
            "mocked_fibonacci.py",
            "from tests.test_discovery import MockFibonacciStrategy",
        ),  # It should be classified as FibonacciStrategy.
        (
            "mocked_cacheable_fibonacci.py",
            "from tests.test_discovery import MockCacheableFibonacciStrategy",
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
            "from tests.test_discovery import NotAStrategy",
        ),  # It should not be imported, as it does not follow the FibonacciStrategy protocol.
    ]

    _setup_strategy_discovery_mocks(tmp_path, mocker, files_content)
    fib_strategies, cache_fib_strategies = load_strategies()

    assert len(fib_strategies) == 1, (
        f"Only one FibonacciStrategy is expected to be returned, but {len(fib_strategies):,} were returned."
    )
    assert len(cache_fib_strategies) == 1, (
        f"Only one CacheableFibonacciStrategy is expected to be returned, but {len(cache_fib_strategies):,} were returned."
    )
    assert fib_strategies[0].name == "Mocked Fibonacci", (
        f"The name of the returned strategy should be Mocked Fibonacci, but it returned {fib_strategies[0].name}."
    )
    assert cache_fib_strategies[0].name == "Mocked Cacheable Fibonacci", (
        f"The name of the returned strategy should be Mocked Cacheable Fibonacci, but it returned {cache_fib_strategies[0].name}."
    )


def test_load_strategies_when_no_strategies_are_found(
    tmp_path: Path, mocker: MockerFixture
):
    """
    Tests whether the NoStrategiesFoundError exception is raised when the directory is empty.
    """

    _setup_strategy_discovery_mocks(tmp_path, mocker)

    with pytest.raises(NoStrategiesFoundError, match="No strategies loaded."):
        load_strategies()
