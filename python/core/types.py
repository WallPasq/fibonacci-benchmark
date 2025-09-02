"""
Stores application-specific type aliases and custom data types.
"""

from typing import Any, Callable, Optional, TypeAlias

Matrix: TypeAlias = list[list[int]]
TaskType: TypeAlias = Optional[tuple[Callable[..., Any], tuple[Any, ...]]]
ResultType: TypeAlias = float | Exception
