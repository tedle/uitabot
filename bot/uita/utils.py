"""Utility functions."""
import asyncio
import contextlib
import discord
import os
import sys
from typing import Iterator, List, Optional

import uita.config


async def dir_size(
    path: str,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> int:
    """Gets the total size of a directory.

    Runs in a separate thread and uses a blocking mutex to ensure only one instance of this
    function is working at a time. This is to prevent race conditions in querying methods that are
    awaiting a result. The performance impact should be minimal since this cuts down on
    asynchronous random disk reads.

    Args:
        path: Path to directory to be sized up.
        loop: Event loop to attach listen server to, defaults to ``asyncio.get_event_loop()``.

    Returns:
        Directory size in bytes.

    """
    loop = loop or asyncio.get_event_loop()

    def walk(path: str) -> int:
        size = 0
        for directory, _, files in os.walk(path):
            for f in files:
                size += os.path.getsize(os.path.join(directory, f))
        return size
    with await dir_size.lock:  # type: ignore
        return await loop.run_in_executor(None, lambda: walk(path))
dir_size.lock = asyncio.Lock()  # type: ignore


def install_dir() -> str:
    """Gets the absolute path to the script being run.

    Returns:
        Path to running script.

    """
    return os.path.abspath(os.path.dirname(sys.argv[0]))


def cache_dir() -> str:
    """Gets the absolute path to the file cache directory.

    Returns:
        Path to cache directory.

    """
    cache = os.path.join(install_dir(), "cache")
    if os.path.exists(cache) and not os.path.isdir(cache):
        os.remove(cache)
    if not os.path.exists(cache):
        os.mkdir(cache, mode=0o700)
    return cache


def config_file() -> str:
    """Gets the absolute path to the config file.

    Returns:
        Path to config file.

    """
    config = os.path.join(install_dir(), os.path.pardir, "config.json")
    return config


async def prune_cache_dir(
    whitelist: Optional[List[str]] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> None:
    """Prunes the cache directory of unused files.

    Args:
        whitelist: List of absolute paths to exempt from pruning.
        loop: Event loop to attach listen server to, defaults to ``asyncio.get_event_loop()``.

    """
    safe_whitelist: List[str] = (whitelist or list())
    safe_whitelist += list(prune_cache_dir.whitelist)  # type: ignore
    loop = loop or asyncio.get_event_loop()

    def prune() -> None:
        for directory, _, files in os.walk(cache_dir()):
            for f in files:
                path = os.path.join(directory, f)
                if path in safe_whitelist:
                    continue
                os.remove(path)
    await loop.run_in_executor(None, prune)
prune_cache_dir.whitelist = set()  # type: ignore


@contextlib.contextmanager
def prune_cache_guard(path: str) -> Iterator[None]:
    """Scoped `with` context function for protecting a path from `uita.utils.prune_cache_dir`

    Args:
        path: Absolute path to be exempted from pruning.

    """
    try:
        prune_cache_dir.whitelist.add(path)  # type: ignore
        yield
    finally:
        prune_cache_dir.whitelist.discard(path)  # type: ignore


def build_client_url(config: uita.config.Config) -> str:
    """Generates the web client URL from the config file settings.

    Args:
        config: Configuration settings.

    Returns:
        Web client URL.

    """
    return "http{}://{}{}".format(
        "s" if config.ssl.cert_file is not None else "",
        config.client.domain,
        (":" + str(config.client.port)) if config.client.port not in (80, 443) else ""
    )


def build_websocket_url(config: uita.config.Config) -> str:
    """Generates the websocket URL from the config file settings.

    Args:
        config: Configuration settings.

    Returns:
        Websocket URL that client is expected to connect to.

    """
    return "ws{}://{}{}".format(
        "s" if config.ssl.cert_file is not None else "",
        config.bot.domain,
        (":" + str(config.bot.port)) if config.bot.port not in (80, 443) else ""
    )


def verify_channel_visibility(channel: discord.abc.GuildChannel, user: discord.Member) -> bool:
    """Checks whether a user can see a channel.

    The Discord API provides a full list of channels including ones normally invisible to the
    client. This helps hide channels that a bot or user shouldn't see.

    Args:
        channel: discord.py channel.
        user: discord.py server member.

    Returns:
        `True` if the user can view and use the given channel.

    """
    permissions = channel.permissions_for(user)
    if channel.type is discord.ChannelType.voice:
        # read_messages is actually view_channel in the official API
        # discord.py mislabeled this, maybe not realizing voice channels use it too
        return (permissions.connect and permissions.read_messages)
    return permissions.read_messages


def verify_user_permissions(user: discord.Member, role: Optional[str]) -> bool:
    """Checks whether a user has sufficient role permissions.

    Args:
        user: discord.py server member.
        role: ID of role to verify against. `None` to allow any role.

    Returns:
        `True` if the user has the specified role, if the specified role is `None` or if the user
        is a server administrator.

    """
    return (
        role is None or
        user.guild_permissions.administrator or
        discord.utils.get(user.roles, id=int(role)) is not None
    )
