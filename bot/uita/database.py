"""Manages database connections and queries."""

import sqlite3
import os
import binascii
import hmac

import uita.auth


class Database():
    """Holds a single database connection and generates queries.

    Parameters
    ----------
    uri : str
        URI pointing to database resource. Can either be a filename or ``:memory:``.

    """
    def __init__(self, uri):
        self._connection = sqlite3.connect(uri)
        c = self._connection.cursor()
        c.execute(_INIT_DATABASE_QUERY)
        self._connection.commit()

    def maintenance(self):
        """Performs database maintenance.

        Currently only deletes expired sessions.

        """
        c = self._connection.cursor()
        c.execute(_PRUNE_OLD_SESSIONS_QUERY)
        self._connection.commit()

    def add_session(self, token, expiry):
        """Creates and inserts a new user session into database.

        Parameters
        ----------
        token : str
            User authentication token to associate new session with.
        expiry : int
            Time from creation of token that it is valid for in seconds.

        Returns
        -------
        uita.auth.Session
            Session object for authenticating user.

        """
        c = self._connection.cursor()
        # Generate cryptographically secure 64 char long hex string for session secret
        secret = binascii.hexlify(os.urandom(32)).decode()
        c.execute(_ADD_SESSION_QUERY, (secret, token, expiry))
        self._connection.commit()
        return uita.auth.Session(handle=c.lastrowid, secret=secret)

    def delete_session(self, session):
        """Deletes a given session from the database.

        Useful for session expiry, user logout, etc.

        Parameters
        ----------
        session : uita.auth.Session
            Session object to be deleted.

        """
        c = self._connection.cursor()
        c.execute(_DELETE_SESSION_QUERY, (session.handle,))
        self._connection.commit()

    def get_access_token(self, session):
        """Verifies whether a given session is valid and returns an access token if so.

        Parameters
        ----------
        session : uita.auth.Session
            Session to compare against database.

        Returns
        -------
        str
            Access token if session is valid, `None` otherwise.

        """
        c = self._connection.cursor()
        c.execute(_GET_SESSION_QUERY, (session.handle,))
        db_session = c.fetchone()
        if db_session is None:
            return None
        if hmac.compare_digest(db_session[0], session.secret):
            return db_session[1]
        return None


_INIT_DATABASE_QUERY = """
CREATE TABLE IF NOT EXISTS sessions (
    handle INTEGER PRIMARY KEY,
    secret TEXT UNIQUE,
    token TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry INT
);"""

_ADD_SESSION_QUERY = """
INSERT OR REPLACE INTO sessions(
    secret,
    token,
    expiry
)
VALUES(?, ?, ?)"""

_DELETE_SESSION_QUERY = """
DELETE FROM sessions WHERE handle=?"""

_PRUNE_OLD_SESSIONS_QUERY = """
DELETE FROM sessions WHERE ((strftime('%s', created) + expiry) - strftime('%s', 'now'))<=0"""

_GET_SESSION_QUERY = """
SELECT secret, token FROM sessions WHERE handle=?"""
