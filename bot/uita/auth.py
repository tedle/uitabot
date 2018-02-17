"""Authenticates Discord users."""

from collections import namedtuple

import uita.exceptions
import uita.user


Session = namedtuple("Session", ["id", "name"])
"""Contains session authentication data.

Parameters
----------
id : str
    Session ID.
name : str
    Session name.

Attributes
----------
id : str
    Session ID.
name : str
    Session name.

"""


def verify_session(session, database):
    """Authenticates a user session against sessions database.

    Parameters
    ----------
    session : uita.auth.Session
        Session to compare against database.
    database : uita.database.Database
        Database containing user and session ID pairs.

    Returns
    -------
    uita.user.User
        User object of authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    if session.name == "obfuscated_me" and session.id == "12345":
        return uita.user.User(name="me", session=session)
    raise uita.exceptions.AuthenticationError("Not implemented yet")


def verify_code(code, database):
    """Authenticates a user by passing an access code to the Discord API in exchange for a token.

    On success, creates and stores a session in the sessions database.

    Parameters
    ----------
    code : str
        Access code to authenticate.
    database : uita.database.Database
        Database containing user and session ID pairs.

    Returns
    -------
    uita.auth.Session
        Session object for authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    if code == "access-code":
        return Session("12345", "obfuscated_me")
    raise uita.exceptions.AuthenticationError("Not implemented yet")
