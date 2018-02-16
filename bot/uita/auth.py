"""Authenticates Discord users."""

import uita.exceptions
import uita.user


def verify_session(user_id, session_id, database):
    """Authenticates a user session ID against sessions database.

    Parameters
    ----------
    user_id : str
        User ID to authenticate.
    session_id : str
        Session ID to compare against database.
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
    if user_id == "me" and session_id == "12345":
        return uita.user.User(name="me")
    raise uita.exceptions.AuthenticationError("Not implemented yet")


def verify_token(token, database):
    """Authenticates a user by passing a token to the Discord API.

    On success, creates and stores a session in the sessions database.

    Parameters
    ----------
    token : str
        Token to authenticate.
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
    raise uita.exceptions.AuthenticationError("Not implemented yet")
    return None
