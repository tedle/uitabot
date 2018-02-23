"""Builds and parses messages for websocket API."""
import json
import math

import uita.exceptions


def parse(message):
    """Parse and validate raw message strings.

    Parameters
    ----------
    message : str
        JSON encoded message to be parsed.

    Returns
    -------
    uita.message.AbstractMessage
        A subclass of `uita.message.AbstractMessage` containing a header and associated data.

    Raises
    ------
    uita.exceptions.MalformedMessage
        If the message string is invalid.
    """
    if len(message) > MAX_CLIENT_MESSAGE_LENGTH:
        raise uita.exceptions.MalformedMessage("Message exceeded maximum length")
    try:
        msg = json.loads(message, parse_int=str, parse_float=str)
    except json.JSONDecoderError:
        raise uita.exceptions.MalformedMessage("Expected JSON encoded object")

    if "header" not in msg or not isinstance(msg["header"], str) or not len(msg["header"]):
        raise uita.exceptions.MalformedMessage("Has no header property")
    if len(msg["header"]) > MAX_HEADER_LENGTH:
        raise uita.exceptions.MalformedMessage("Header exceeds maximum length")

    try:
        header = msg["header"]
        # List of required properties
        for prop in VALID_MESSAGES[header][1]:
            if prop not in msg:
                raise uita.exceptions.MalformedMessage("Missing {} property".format(prop))
        # Message subclass constructor
        del msg["header"]
        return VALID_MESSAGES[header][0](**msg)
    except KeyError:
        raise uita.exceptions.MalformedMessage("Invalid header")


class AbstractMessage():
    """Abstract base class for websocket messaging API.

    Attributes
    ----------
    header : str
        Header defining message type

    """
    header = None

    def __str__(self):
        """Serializes self to JSON encoded message object for network transfer"""
        # Appends header to self.__dict__ serialization because it is a class level attribute
        return json.dumps(dict({"header": self.header}, **self.__dict__))


class AuthCodeMessage(AbstractMessage):
    """Sent by client when authenticating by token request code.

    Attributes
    ----------
    code : str
        Token request code to be sent to Discord API.
    """
    header = "auth.code"
    """"""

    def __init__(self, code):
        self.code = str(code)


class AuthFailMessage(AbstractMessage):
    """Sent by server when authentication fails."""
    header = "auth.fail"
    """"""


class AuthSessionMessage(AbstractMessage):
    """Sent by client when authenticating by session.

    Attributes
    ----------
    handle : str
        Session handle as stored in database.
    secret : str
        Session secret as stored in database.

    """
    header = "auth.session"
    """"""

    def __init__(self, handle, secret):
        self.handle = str(handle)
        self.secret = str(secret)
        if len(self.handle) > MAX_DIGITS_64BIT:
            raise uita.exceptions.MalformedMessage("Session handle exceeds 64-bit number")
        if len(self.secret) > MAX_SESSION_LENGTH:
            raise uita.exceptions.MalformedMessage("Session secret exceeds max possible length")


class AuthSucceedMessage(AbstractMessage):
    """Sent by server when authentication succeeds.

    Parameters
    ----------
    user : uita.types.DiscordUser
        User object to encode.

    Attributes
    ----------
    username : str
        Username for display.
    session_handle : str
        Session authentication handle.
    session_secret : str
        Session authentication secret.

    """
    header = "auth.succeed"
    """"""

    def __init__(self, user):
        self.username = str(user.name)
        self.session_handle = str(user.session.handle)
        self.session_secret = str(user.session.secret)


class ChannelListGetMessage(AbstractMessage):
    """Sent by client requesting a list of every channel the bot can connect to."""
    header = "channel.list.get"
    """"""


class ChannelListSendMessage(AbstractMessage):
    """Sent by server containing a list of every channel the bot can connect to.

    Attributes
    ----------
    channels : list(uita.types.DiscordChannel)
        List of channels to connect to.

    """
    header = "channel.list.send"
    """"""

    def __init__(self, channels):
        self.channels = [channel.__dict__ for channel in channels]


class PlayURLMessage(AbstractMessage):
    """Sent by client requesting a remote song be played.

    Attributes
    ----------
    url : str
        URL to audio resource.

    """
    header = "play.url"
    """"""

    def __init__(self, url):
        self.url = str(url)


class ServerJoinMessage(AbstractMessage):
    """Sent by client containing a server ID to join.

    Attributes
    ----------
    server_id : str
        Server ID to join.

    """
    header = "server.join"
    """"""

    def __init__(self, server_id):
        self.server_id = str(server_id)
        if len(self.server_id) > MAX_DIGITS_64BIT:
            raise uita.exceptions.MalformedMessage("Server ID exceeds 64-bit number")


class ServerListGetMessage(AbstractMessage):
    """Sent by client requesting a list of every server it can connect to."""
    header = "server.list.get"
    """"""


class ServerListSendMessage(AbstractMessage):
    """Sent by server containing a list of every server a user can connect to.

    Attributes
    ----------
    servers : list(uita.types.DiscordServer)
        List of servers to connect to.

    """
    header = "server.list.send"
    """"""

    def __init__(self, servers):
        self.servers = [server.__dict__ for server in servers]


VALID_MESSAGES = {
    AuthCodeMessage.header: (AuthCodeMessage, ["code"]),
    AuthFailMessage.header: (AuthFailMessage, []),
    AuthSessionMessage.header: (AuthSessionMessage, ["handle", "secret"]),
    AuthSucceedMessage.header: (AuthSucceedMessage, [
        "username", "session_handle", "session_secret"
    ]),
    ChannelListGetMessage.header: (ChannelListGetMessage, []),
    ChannelListSendMessage.header: (ChannelListSendMessage, ["channels"]),
    PlayURLMessage.header: (PlayURLMessage, ["url"]),
    ServerJoinMessage.header: (ServerJoinMessage, ["server_id"]),
    ServerListGetMessage.header: (ServerListGetMessage, []),
    ServerListSendMessage.header: (ServerListSendMessage, ["servers"])
}

# Mild length sanitization on any input that is used for indexing
MAX_CLIENT_MESSAGE_LENGTH = 5000
MAX_DIGITS_64BIT = math.ceil(64 * math.log10(2))  # 64 * log 2 = log (2^64)
MAX_HEADER_LENGTH = 50
MAX_SESSION_LENGTH = 64
