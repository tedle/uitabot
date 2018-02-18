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

    def add_session(self, token):
        """Creates and inserts a new user session into database.

        Parameters
        ----------
        token : str
            User authentication token to associate new session with.

        Returns
        -------
        uita.auth.Session
            Session object for authenticating user.

        """
        c = self._connection.cursor()
        secret = binascii.hexlify(os.urandom(32)).decode()
        c.execute(_ADD_SESSION_QUERY, (secret, token))
        return uita.auth.Session(handle=c.lastrowid, secret=secret)

    def verify_session(self, session):
        """Verifies whether a given session is valid.

        Parameters
        ----------
        session : uita.auth.Session
            Session to compare against database.

        Returns
        -------
        bool
            True if session is valid.

        """
        c = self._connection.cursor()
        c.execute(_GET_SESSION_QUERY, (session.handle,))
        db_session = c.fetchone()
        if db_session is None:
            return False
        return hmac.compare_digest(db_session[0], session.secret)


_INIT_DATABASE_QUERY = """
CREATE TABLE IF NOT EXISTS sessions (
    handle INTEGER PRIMARY KEY,
    secret TEXT UNIQUE,
    token TEXT UNIQUE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);"""

_ADD_SESSION_QUERY = """
INSERT OR REPLACE INTO sessions(
    secret,
    token
)
VALUES(?, ?)"""

_GET_SESSION_QUERY = """
SELECT secret FROM sessions WHERE handle=?
"""
