"""Simple logging helper compatible with Nighty.

Nighty patches ``print`` to accept a ``type_`` parameter for log levels.
This module provides ``log`` that tries to use that parameter when
available and falls back to a plain ``print`` call otherwise.
"""

import inspect

_HAS_TYPE_PARAM = 'type_' in inspect.signature(print).parameters


def log(msg, type_: str = "INFO") -> None:
    """Print a message using Nighty's log format when possible."""
    if _HAS_TYPE_PARAM:
        print(msg, type_=type_)
    else:
        print(msg)

