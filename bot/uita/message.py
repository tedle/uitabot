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
    except (json.JSONDecodeError, TypeError):
        raise uita.exceptions.MalformedMessage("Expected JSON encoded object")

    # Ensure message header exists and is properly formatted
    if "header" not in msg or not isinstance(msg["header"], str) or not len(msg["header"]):
        raise uita.exceptions.MalformedMessage("Has no header property")
    if len(msg["header"]) > MAX_HEADER_LENGTH:
        raise uita.exceptions.MalformedMessage("Header exceeds maximum length")

    try:
        header = msg["header"]
        # Validate that all the required properties for a given message type are here
        for prop in VALID_MESSAGES[header][1]:
            if prop not in msg:
                raise uita.exceptions.MalformedMessage("Missing {} property".format(prop))
        # Construct a message directly with the JSON decoded dictionary
        # Header is hardcoded in and constructor will not accept it
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


class ChannelJoinMessage(AbstractMessage):
    """Sent by client containing a channel ID to join.

    Attributes
    ----------
    channel_id : str
        Channel ID to join.

    """
    header = "channel.join"
    """"""

    def __init__(self, channel_id):
        self.channel_id = str(channel_id)
        if len(self.channel_id) > MAX_DIGITS_64BIT:
            raise uita.exceptions.MalformedMessage("Channel ID exceeds 64-bit number")
        if len(self.channel_id) == 0:
            raise uita.exceptions.MalformedMessage("Channel ID is empty")


class ChannelLeaveMessage(AbstractMessage):
    """Sent by client containing when leaving a channel."""
    header = "channel.leave"
    """"""


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
        self.channels = [{
            "id": channel.id,
            "name": channel.name,
            "position": channel.position
        } for channel in channels]


class ErrorFileInvalidMessage(AbstractMessage):
    """Sent when an uploaded file has invalid audio data.

    Attributes
    ----------
    error : str
        Description of file error.

    """
    header = "error.file.invalid"
    """"""

    def __init__(self, error):
        self.error = error


class ErrorQueueFullMessage(AbstractMessage):
    """Sent when a requested URL cannot be played."""
    header = "error.queue.full"
    """"""


class ErrorUrlInvalidMessage(AbstractMessage):
    """Sent when a requested URL cannot be played."""
    header = "error.url.invalid"
    """"""


class FileUploadStartMessage(AbstractMessage):
    """Sent by client initiating a file upload procedure.

    Attributes
    ----------
    size : int
        File size in bytes.

    """
    header = "file.upload.start"
    """"""

    def __init__(self, size):
        self.size = int(size)


class FileUploadCompleteMessage(AbstractMessage):
    """Sent by server signaling a completed file upload"""
    header = "file.upload.complete"
    """"""


class HeartbeatMessage(AbstractMessage):
    """Sent by client every 60 seconds to keep connection alive."""
    header = "heartbeat"
    """"""


class PlayQueueGetMessage(AbstractMessage):
    """Sent by client requesting playback queue state."""
    header = "play.queue.get"
    """"""


class PlayQueueMoveMessage(AbstractMessage):
    """Sent by client to move a track to a new position in the queue..

    Attributes
    ----------
    id : str
        ID of track to be removed.
    position : int
        Queue index to be moved to.

    """
    header = "play.queue.move"
    """"""

    def __init__(self, id, position):
        self.id = str(id)
        self.position = int(position)
        if len(self.id) > MAX_TRACK_ID_LENGTH:
            raise uita.exceptions.MalformedMessage("Track ID exceeds max possible length")
        if self.position < 0:
            raise uita.exceptions.MalformedMessage("Track position is less than 0")


class PlayQueueRemoveMessage(AbstractMessage):
    """Sent by client containing track ID to be removed.

    Attributes
    ----------
    id : str
        ID of track to be removed.

    """
    header = "play.queue.remove"
    """"""

    def __init__(self, id):
        self.id = str(id)
        if len(self.id) > MAX_TRACK_ID_LENGTH:
            raise uita.exceptions.MalformedMessage("Track ID exceeds max possible length")


class PlayQueueSendMessage(AbstractMessage):
    """Sent by server containing playback queue state.

    Attributes
    ----------
    queue : list(uita.audio.Track)
        List of tracks that are currently queued.

    """
    header = "play.queue.send"
    """"""

    def __init__(self, queue):
        self.queue = [{
            "id": track.id,
            "url": track.url or "",
            "title": track.title,
            "duration": track.duration,
            "live": track.live,
            "thumbnail": track.user.avatar
        } for track in queue]


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
        if len(self.url) > MAX_URL_LENGTH:
            raise uita.exceptions.MalformedMessage("Play URL exceeds max length")


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
        if len(self.server_id) == 0:
            raise uita.exceptions.MalformedMessage("Server ID is empty")


class ServerKickMessage(AbstractMessage):
    """Sent by server when user can no longer access their current Discord server.."""
    header = "server.kick"
    """"""


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
        self.servers = [{
            "id": server.id,
            "name": server.name,
            "icon": server.icon
        } for server in servers]


# Dictionary for validating message data provided by clients
VALID_MESSAGES = {
    AuthCodeMessage.header: (AuthCodeMessage, ["code"]),
    AuthFailMessage.header: (AuthFailMessage, []),
    AuthSessionMessage.header: (AuthSessionMessage, ["handle", "secret"]),
    AuthSucceedMessage.header: (AuthSucceedMessage, [
        "username", "session_handle", "session_secret"
    ]),
    ChannelJoinMessage.header: (ChannelJoinMessage, ["channel_id"]),
    ChannelLeaveMessage.header: (ChannelLeaveMessage, []),
    ChannelListGetMessage.header: (ChannelListGetMessage, []),
    ChannelListSendMessage.header: (ChannelListSendMessage, ["channels"]),
    ErrorFileInvalidMessage.header: (ErrorFileInvalidMessage, ["error"]),
    ErrorQueueFullMessage.header: (ErrorQueueFullMessage, []),
    ErrorUrlInvalidMessage.header: (ErrorUrlInvalidMessage, []),
    FileUploadStartMessage.header: (FileUploadStartMessage, ["size"]),
    FileUploadCompleteMessage.header: (FileUploadCompleteMessage, []),
    HeartbeatMessage.header: (HeartbeatMessage, []),
    PlayQueueGetMessage.header: (PlayQueueGetMessage, []),
    PlayQueueMoveMessage.header: (PlayQueueMoveMessage, ["id", "position"]),
    PlayQueueRemoveMessage.header: (PlayQueueRemoveMessage, ["id"]),
    PlayQueueSendMessage.header: (PlayQueueSendMessage, ["queue"]),
    PlayURLMessage.header: (PlayURLMessage, ["url"]),
    ServerJoinMessage.header: (ServerJoinMessage, ["server_id"]),
    ServerKickMessage.header: (ServerKickMessage, []),
    ServerListGetMessage.header: (ServerListGetMessage, []),
    ServerListSendMessage.header: (ServerListSendMessage, ["servers"])
}

# Mild length sanitization on any input that is used for indexing
MAX_CLIENT_MESSAGE_LENGTH = 5000
MAX_DIGITS_64BIT = math.ceil(64 * math.log10(2))  # 64 * log 2 = log (2^64)
MAX_HEADER_LENGTH = 50
MAX_SESSION_LENGTH = 64
MAX_TRACK_ID_LENGTH = 32
MAX_URL_LENGTH = 2000
