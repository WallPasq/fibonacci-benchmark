"""
Stores global project constants.
"""

from src.strategies.protocol import FibonacciStrategy

MODULE_BASE: str = "strategies"
MODULE_NAME: str = f"src.{MODULE_BASE}" + ".{file_name}"
PROTOCOL_FILE: str = f"{FibonacciStrategy.__module__.split('.')[-1]}.py"
