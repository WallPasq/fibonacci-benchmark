import importlib
import inspect
from pathlib import Path
from types import ModuleType

from src.strategies.protocol import CacheableFibonacciStrategy, FibonacciStrategy

# If you rename the strategies folder, you will have to change this constant.
MODULE_BASE: str = "strategies"


class NoStrategiesFoundError(Exception):
    """Raised when no Fibonacci strategies are discovered."""

    pass


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
    protocol_file: str = f"{FibonacciStrategy.__module__.split('.')[-1]}.py"

    for path in strategies_dir.glob("*.py"):
        if path.name.startswith(("_", ".")) or path.name == protocol_file:
            continue

        # If you change the folder structure or move the strategies files, you will have to change this variable.
        module_name: str = f"src.{MODULE_BASE}.{path.stem}"
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


if __name__ == "__main__":
    all_fib_strategies, all_cache_fib_strategies = load_strategies()

    if all_cache_fib_strategies:
        names: list[str] = [strategy.name for strategy in all_cache_fib_strategies]
        print("Loaded cacheable Fibonacci strategies:", ", ".join(names))

    if all_fib_strategies:
        names: list[str] = [strategy.name for strategy in all_fib_strategies]
        print("Loaded Fibonacci strategies (without cache):", ", ".join(names))
