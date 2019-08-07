"""Specialized exceptions."""
import uita.message


class ClientError(Exception):
    """Occurs when a server event fails and needs to notify to the client.

    Unlike other uncaught errors caused by a server event, `uita.exceptions.ClientError` will not
    cause a connection closure.

    Args:
        message: Message to be sent by the connection handler to the client.

    Attributes:
        message (uita.message.AbstractMessage): Message to be sent by the connection handler to the
            client.

    Raises:
        TypeError: If initialized with a type other than uita.message.AbstractMessage

    """
    def __init__(self, message: uita.message.AbstractMessage) -> None:
        if not isinstance(message, uita.message.AbstractMessage):
            raise TypeError(
                "uita.exceptions.ClientError must be initialized with uita.message.AbstractMessage"
            )
        super().__init__(message)
        self.message = message


class AuthenticationError(Exception):
    """Occurs when a `uita.types.DiscordUser` resource is accessed without proper credentials."""
    pass


class MalformedConfig(Exception):
    """Occurs when a config file is malformed."""
    pass


class MalformedFile(Exception):
    """Occurs when an uploaded file is malformed."""
    pass


class MalformedMessage(Exception):
    """Occurs when a parsed websocket message is malformed."""
    pass


class NoActiveServer(Exception):
    """Occurs when an authenticated active server is needed but not set."""
    pass


class ServerError(Exception):
    """Occurs when a `uita.ui_server.Server` is configured or used incorrectly."""
    pass
