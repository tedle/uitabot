"""Defines Discord user data."""

import namedtuple


User = namedtuple("User", ["id"])
User.__doc__ = """Contains Discord user data

    Parameters
    ----------
    id : str
        User ID

    Attributes
    ----------
    id : str
        User ID

    """
