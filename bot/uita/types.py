"""Defines various container types."""


class DiscordChannel():
    """Container for Discord channel data.

    Parameters
    ----------
    id : str
        Unique channel ID.
    name : str
        Channel name.

    Attributes
    ----------
    id : str
        Unique channel ID.
    name : str
        Channel name.

    """
    def __init__(self, id, name):
        self.id = id
        self.name = name


class DiscordServer():
    """Container for Discord server data.

    Parameters
    ----------
    id : str
        Unique server ID.
    name : str
        Server name.

    Attributes
    ----------
    id : str
        Unique server ID.
    name : str
        Server name.

    """
    def __init__(self, id, name):
        self.id = id
        self.name = name


class DiscordUser():
    """Container for Discord user data.

    Parameters
    ----------
    id : str
        Unique user ID.
    name : str
        User name.
    session : uita.auth.Session
        Session authentication data.
    active_server : uita.types.DiscordServer
        Discord server that user has joined. None if user has not joined a server yet.

    Attributes
    ----------
    id : str
        Unique user ID.
    name : str
        User name.
    session : uita.auth.Session
        Session authentication data.
    active_server : uita.types.DiscordServer
        Discord server that user has joined. None if user has not joined a server yet.

    """
    def __init__(self, id, name, session, active_server):
        self.id = id
        self.name = name
        self.session = session
        self.active_server = active_server
