"""Defines Discord user data."""

from collections import namedtuple


User = namedtuple("User", ["name", "session"])
"""Container for Discord user data.

Parameters
----------
name : str
    User name.
session : uita.auth.Session
    Session authentication data.

Attributes
----------
name : str
    User name.
session : uita.auth.Session
    Session authentication data.

"""
