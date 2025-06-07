"""Simple logging helper compatible with Nighty.

Nighty patches ``print`` to accept a ``type_`` parameter for log levels.
This module provides ``log`` that tries to use that parameter when
available and falls back to a plain ``print`` call otherwise.
"""

def log(msg, type_: str = "INFO") -> None:
    """Print ``msg`` using the ``type_`` keyword if ``print`` supports it."""
    try:  # pragma: no cover - depends on Nighty's monkey patching
        print(msg, type_=type_)
    except TypeError:
        print(msg)

