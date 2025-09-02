import importlib
import inspect
from pathlib import Path
from types import ModuleType

from core.constants import MODULE_BASE, MODULE_NAME, PROTOCOL_FILE
from core.exceptions import NoStrategiesFoundError
from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy


def load_strategies() -> tuple[
    list[FibonacciStrategy], list[CacheableFibonacciStrategy]
]:
    """Dynamically loads all Fibonacci calculation strategies.

    This function scans the 'strategies' directory for modules, discovers
    classes that implement the FibonacciStrategy protocol, and then
    categorizes them into non-cacheable and cacheable strategies.

    Returns:
        A tuple containing two lists: the first with non-cacheable
        strategies, and the second with cacheable strategies.

    Raises:
        NoStrategiesFoundError: If no strategies are found.
    """
    # If you change the folder structure or move this file, you will have to change this variable.
    strategies_dir: Path = Path(__file__).parent / MODULE_BASE
    found_strategies: dict[str, FibonacciStrategy] = {}

    for path in strategies_dir.glob("*.py"):
        if path.name.startswith(("_", ".")) or path.name == PROTOCOL_FILE:
            continue

        # If you change the folder structure or move the strategies files, you will have to change this variable.
        module_name: str = MODULE_NAME.format(file_name=path.stem)
        module: ModuleType = importlib.import_module(module_name)

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module_name:
                continue

            strategy = obj()

            if isinstance(strategy, FibonacciStrategy):
                found_strategies[strategy.name] = strategy

    if not found_strategies:
        raise NoStrategiesFoundError("No strategies loaded.")

    all_fib_strategies: list[FibonacciStrategy] = []
    all_cache_fib_strategies: list[CacheableFibonacciStrategy] = []

    for strategy in found_strategies.values():
        if isinstance(strategy, CacheableFibonacciStrategy):
            all_cache_fib_strategies.append(strategy)
        else:
            all_fib_strategies.append(strategy)

    return all_fib_strategies, all_cache_fib_strategies
