"""Specialized exceptions."""


class AuthenticationError(Exception):
    """Occurs when a `uita.user.User` resource is accessed without proper credentials."""
    pass


class ServerError(Exception):
    """Occurs when a `uita.ui_server.Server` is configured or used incorrectly"""
    pass
