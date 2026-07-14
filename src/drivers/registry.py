"""Registry for database drivers.

Drivers register themselves at import time via the @register_driver
decorator. Importing the drivers package binds every shipped driver
and registers it under its name (case-sensitive).
"""
from __future__ import annotations

from typing import Dict, Type

_REGISTRY: Dict[str, Type["BaseDatabaseDriver"]] = {}


def register_driver(name: str):
    """Class decorator registering a driver under ``name``."""
    def decorator(cls):
        from .base import BaseDatabaseDriver
        if not issubclass(cls, BaseDatabaseDriver):
            raise TypeError(f"{cls.__name__} must subclass BaseDatabaseDriver")
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_driver(name: str) -> Type["BaseDatabaseDriver"]:
    """Return a registered driver class by name.

    Raises
    ------
    ValueError
        If no driver is registered under ``name``.
    """
    from .base import BaseDatabaseDriver
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"No driver registered as {name!r}. Available: {available}")
    return _REGISTRY[name]


def available_drivers() -> list[str]:
    """Return sorted names of all registered drivers."""
    return sorted(_REGISTRY.keys())