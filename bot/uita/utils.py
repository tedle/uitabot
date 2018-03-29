"""Utility functions."""
import os
import sys


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
