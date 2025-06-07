"""Utility logging helper for Nighty scripts."""

def log(msg, type_="INFO"):
    """Safe log that works with or without Nighty's patched print."""
    try:
        print(msg, type_=type_)
    except TypeError:
        print(msg)
