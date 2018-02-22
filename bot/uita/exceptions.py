"""Specialized exceptions."""


class AuthenticationError(Exception):
    """Occurs when a `uita.types.DiscordUser` resource is accessed without proper credentials."""
    pass


class MalformedMessage(Exception):
    """Occurs when a parsed websocket message is malformed."""
    pass


class ServerError(Exception):
    """Occurs when a `uita.ui_server.Server` is configured or used incorrectly."""
    pass
