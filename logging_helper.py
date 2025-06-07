"""Simple logging helper compatible with Nighty."""


def log(msg, type_="INFO"):
    """Print ``msg`` with an optional log level."""
    try:
        print(msg, type_=type_)
    except TypeError:
        print(msg)


