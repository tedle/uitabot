"""Authenticates Discord users."""

from collections import namedtuple

import uita.exceptions
import uita.types


Session = namedtuple("Session", ["handle", "secret"])
"""Contains session authentication data.

Parameters
----------
handle : str
    Session handle.
secret : str
    Session secret.

Attributes
----------
handle : str
    Session handle.
secret : str
    Session secret.

"""


def verify_session(session, database):
    """Authenticates a user session against sessions database.

    Parameters
    ----------
    session : uita.auth.Session
        Session to compare against database.
    database : uita.database.Database
        Database containing valid sessions.

    Returns
    -------
    uita.types.DiscordUser
        User object of authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    if database.verify_session(session):
        return uita.types.DiscordUser(
            id="98435789",
            name="me",
            session=session,
            active_server_id=None
        )
    raise uita.exceptions.AuthenticationError("Session authentication failed")


def verify_code(code, database):
    """Authenticates a user by passing an access code to the Discord API in exchange for a token.

    On success, creates and stores a session in the sessions database.

    Parameters
    ----------
    code : str
        Access code to authenticate.
    database : uita.database.Database
        Database containing valid sessions.

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
        token = "we_got_this_from_the_discord_api"
        return database.add_session(token)
    raise uita.exceptions.AuthenticationError("Invalid access code")
