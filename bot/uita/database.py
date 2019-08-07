"""Manages database connections and queries."""

import sqlite3
import os
import binascii
import hmac
from typing import cast, Optional
from typing_extensions import Final

import uita.auth


class Database():
    """Holds a single database connection and generates queries.

    Args:
        uri: URI pointing to database resource. Can either be a filename or ``:memory:``.

    """
    def __init__(self, uri: str) -> None:
        self._connection = sqlite3.connect(uri)
        c = self._connection.cursor()
        c.executescript(_INIT_DATABASE_QUERY)
        self._connection.commit()

    def maintenance(self) -> None:
        """Performs database maintenance.

        Currently only deletes expired sessions.

        """
        c = self._connection.cursor()
        c.execute(_PRUNE_OLD_SESSIONS_QUERY)
        self._connection.commit()

    def add_session(self, token: str, expiry: int) -> uita.auth.Session:
        """Creates and inserts a new user session into database.

        Args:
            token: User authentication token to associate new session with.
            expiry: Time from creation of token that it is valid for in seconds.

        Returns:
            Session object for authenticating user.

        """
        c = self._connection.cursor()
        # Generate cryptographically secure 64 char long hex string for session secret
        secret = binascii.hexlify(os.urandom(32)).decode()
        c.execute(_ADD_SESSION_QUERY, (secret, token, expiry))
        self._connection.commit()
        return uita.auth.Session(handle=c.lastrowid, secret=secret)

    def delete_session(self, session: uita.auth.Session) -> None:
        """Deletes a given session from the database.

        Useful for session expiry, user logout, etc.

        Args:
            session: Session object to be deleted.

        """
        c = self._connection.cursor()
        c.execute(_DELETE_SESSION_QUERY, (session.handle,))
        self._connection.commit()

    def get_access_token(self, session: uita.auth.Session) -> Optional[str]:
        """Verifies whether a given session is valid and returns an access token if so.

        Args:
            session: Session to compare against database.

        Returns:
            Access token if session is valid, `None` otherwise.

        """
        c = self._connection.cursor()
        c.execute(_GET_SESSION_QUERY, (session.handle,))
        db_session = c.fetchone()
        if db_session is None:
            return None
        if hmac.compare_digest(db_session[0], session.secret):
            return cast(str, db_session[1])
        return None

    def set_server_role(self, server_id: str, role_id: Optional[str]) -> None:
        """Configures the required role setting for a server.

        Args:
            server_id: Server ID to change setting for.
            role_id: Role ID for required role to use bot commands. `None` for free access.

        """
        c = self._connection.cursor()
        c.execute(_SET_SERVER_ROLE_QUERY, (server_id, role_id))
        self._connection.commit()

    def get_server_role(self, server_id: str) -> Optional[str]:
        """Retrieves the required role setting for a server.

        Args:
            server_id: Server ID to change setting for.

        Returns:
            Role ID if server has configured this setting, `None` otherwise.

        """
        c = self._connection.cursor()
        c.execute(_GET_SERVER_ROLE_QUERY, (server_id,))
        role = c.fetchone()
        if role is None:
            return None
        return cast(str, role[0])


_INIT_DATABASE_QUERY: Final = """
CREATE TABLE IF NOT EXISTS sessions (
    handle INTEGER PRIMARY KEY,
    secret TEXT UNIQUE,
    token TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry INT
);
CREATE TABLE IF NOT EXISTS server_roles (
    server_id TEXT PRIMARY KEY,
    role_id TEXT
);"""

_ADD_SESSION_QUERY: Final = """
INSERT OR REPLACE INTO sessions(
    secret,
    token,
    expiry
)
VALUES(?, ?, ?)"""

_DELETE_SESSION_QUERY: Final = """
DELETE FROM sessions WHERE handle=?"""

_PRUNE_OLD_SESSIONS_QUERY: Final = """
DELETE FROM sessions WHERE ((strftime('%s', created) + expiry) - strftime('%s', 'now'))<=0"""

_GET_SESSION_QUERY: Final = """
SELECT secret, token FROM sessions WHERE handle=?"""

_SET_SERVER_ROLE_QUERY: Final = """
INSERT OR REPLACE INTO server_roles(
    server_id,
    role_id
)
VALUES(?, ?)"""

_GET_SERVER_ROLE_QUERY: Final = """
SELECT role_id FROM server_roles WHERE server_id=?"""
