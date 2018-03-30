"""Utility functions."""
import asyncio
import contextlib
import os
import sys


async def dir_size(path, loop=None):
    """Gets the total size of a directory.

    Runs in a separate thread and uses a blocking mutex to ensure only one instance of this
    function is working at a time. This is to prevent race conditions in querying methods that are
    awaiting a result. The performance impact should be minimal since this cuts down on
    asynchronous random disk reads.

    Parameters
    ----------
    path : os.PathLike
        Path to directory to be sized up.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach listen server to, defaults to ``asyncio.get_event_loop()``.

    Returns
    -------
    int
        Directory size in bytes.

    """
    loop = loop or asyncio.get_event_loop()

    def walk(path):
        size = 0
        for directory, _, files in os.walk(path):
            for f in files:
                size += os.path.getsize(os.path.join(directory, f))
        return size
    with await dir_size.lock:
        return await loop.run_in_executor(None, lambda: walk(path))
dir_size.lock = asyncio.Lock()


def install_dir():
    """Gets the absolute path to the script being run.

    Returns
    -------
    os.PathLike
        Path to running script.

    """
    return os.path.abspath(os.path.dirname(sys.argv[0]))


def cache_dir():
    """Gets the absolute path to the file cache directory.

    Returns
    -------
    os.PathLike
        Path to cache directory.

    """
    cache = os.path.join(install_dir(), "cache")
    if os.path.exists(cache) and not os.path.isdir(cache):
        os.remove(cache)
    if not os.path.exists(cache):
        os.mkdir(cache, mode=0o600)
    return cache


async def prune_cache_dir(whitelist=None, loop=None):
    """Prunes the cache directory of unused files.

    Parameters
    ----------
    whitelist : list(os.PathLike), optional
        List of absolute paths to exempt from pruning.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach listen server to, defaults to ``asyncio.get_event_loop()``.

    """
    whitelist = (whitelist or list()) + list(prune_cache_dir.whitelist)
    loop = loop or asyncio.get_event_loop()

    def prune(exemptions):
        for directory, _, files in os.walk(cache_dir()):
            for f in files:
                path = os.path.join(directory, f)
                if path in exemptions:
                    continue
                os.remove(path)
    await loop.run_in_executor(None, lambda: prune(whitelist))
prune_cache_dir.whitelist = set()  # noqa: E305


@contextlib.contextmanager
def prune_cache_guard(path):
    """Scoped `with` context function for protecting a path from `uita.utils.prune_cache_dir`

    Parameters
    ----------
    path : os.PathLike
        Absolute path to be exempted from pruning.

    """
    prune_cache_dir.whitelist.add(path)
    yield
    prune_cache_dir.whitelist.discard(path)
