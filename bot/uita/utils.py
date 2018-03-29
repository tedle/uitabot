"""Utility functions."""
import asyncio
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
