"""Defines Discord user data."""

from collections import namedtuple


User = namedtuple("User", ["name"])
"""Contains Discord user data.

Parameters
----------
name : str
    User name.

Attributes
----------
name : str
    User name.

"""
