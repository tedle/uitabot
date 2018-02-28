"""Authenticates Discord users."""

from collections import namedtuple

import uita.discord_api
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


async def verify_session(session, database, config, loop):
    """Authenticates a user session against sessions database and Discord API.

    Parameters
    ----------
    session : uita.auth.Session
        Session to compare against database.
    database : uita.database.Database
        Database containing valid sessions.
    config : uita.config.Config
        Configuration options containing API keys.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach blocking request threads to.

    Returns
    -------
    uita.types.DiscordUser
        User object of authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    token = database.get_access_token(session)
    if token is not None:
        try:
            user = await uita.discord_api.get("/users/@me", token, loop)
            return uita.types.DiscordUser(
                id=user["id"],
                name=user["username"],
                session=session,
                active_server_id=None
            )
        except uita.exceptions.AuthenticationError:
            database.delete_session(session)
    raise uita.exceptions.AuthenticationError("Session authentication failed")


async def verify_code(code, database, config, loop):
    """Authenticates a user by passing an access code to the Discord API in exchange for a token.

    On success, creates and stores a session in the local database.

    Parameters
    ----------
    code : str
        Access code to authenticate.
    database : uita.database.Database
        Database containing valid sessions.
    config : uita.config.Config
        Configuration options containing API keys.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach blocking request threads to.

    Returns
    -------
    uita.auth.Session
        Session object for authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If authentication fails.

    """
    api_data = await uita.discord_api.auth(code, config, loop)
    return database.add_session(
        api_data["access_token"],
        api_data["expires_in"]
    )
