"""Builds and parses messages for websocket API."""
import json

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
    try:
        msg = json.loads(message, parse_int=str, parse_float=str)
    except json.JSONDecoderError:
        raise uita.exceptions.MalformedMessage("Expected JSON encoded object")

    if "header" not in msg or not isinstance(msg["header"], str) or not len(msg["header"]):
        raise uita.exceptions.MalformedMessage("Has no header property")

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
        self.code = code


class AuthFailMessage(AbstractMessage):
    """Sent by server when authentication fails."""
    header = "auth.fail"
    """"""


class AuthSessionMessage(AbstractMessage):
    """Sent by client when authenticating by session.

    Attributes
    ----------
    session : str
        Session ID as stored in database.
    name : str
        Session name as stored in database.

    """
    header = "auth.session"
    """"""

    def __init__(self, session, name):
        self.session = session
        self.name = name


class AuthSucceedMessage(AbstractMessage):
    """Sent by server when authentication succeeds.

    Parameters
    ----------
    user : uita.user.User
        User object to encode.

    Attributes
    ----------
    username : str
        Username for display.
    session_id : str
        Session authentication ID.
    session_name : str
        Session authentication name.

    """
    header = "auth.succeed"
    """"""

    def __init__(self, user):
        self.username = user.name
        self.session_id = user.session.id
        self.session_name = user.session.name


VALID_MESSAGES = {
    AuthCodeMessage.header: (AuthCodeMessage, ["code"]),
    AuthFailMessage.header: (AuthFailMessage, []),
    AuthSessionMessage.header: (AuthSessionMessage, ["session", "name"]),
    AuthSucceedMessage.header: (AuthSucceedMessage, ["username", "session_id", "session_name"])
}
