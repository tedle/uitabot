"""Manages database connections and queries."""

import sqlite3


class Database():
    """Holds a single database connection and generates queries.

    Parameters
    ----------
    uri : str
        URI pointing to database resource. Can either be a filename or `:memory:`.

    """
    def __init__(self, uri):
        self._connection = sqlite3.connect(uri)
