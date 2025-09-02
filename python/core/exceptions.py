"""
Stores custom application exceptions.
"""


class TimeoutSignal(Exception):
    """Raised when the subprocess takes longer than the defined timeout."""

    pass


class NoStrategiesFoundError(Exception):
    """Raised when no Fibonacci strategies are discovered."""

    pass
