"""Package entrypoint. Importing src.drivers registers all built-in drivers."""
from .registry import register_driver, get_driver, available_drivers  # re-export
from .base import BaseDatabaseDriver, DriverField                    # re-export

# Import each driver module for its registration side-effect.
from . import sqlite_driver    # noqa: F401
from . import postgres_driver  # noqa: F401
from . import mysql_driver     # noqa: F401
from . import mongodb_driver   # noqa: F401

ALL_DRIVERS = available_drivers()

__all__ = [
    "BaseDatabaseDriver", "DriverField",
    "register_driver", "get_driver", "available_drivers",
    "ALL_DRIVERS",
]