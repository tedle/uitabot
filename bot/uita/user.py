"""Defines Discord user data."""

from collections import namedtuple


User = namedtuple("User", ["name"])
User.__doc__ = """Contains Discord user data

    Parameters
    ----------
    name : str
        User name

    Attributes
    ----------
    name : str
        User name

    """
