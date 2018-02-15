"""Loads JSON configuration files"""

import json
from collections import namedtuple


def load(filename):
    """Loads a JSON formatted config file.

    Converts empty strings to `None`.

    Parameters
    ----------
    filename : str
        Filename of config file to load.

    Returns
    -------
    namedtuple
        Object containing config file values as attributes.
    """
    with open(filename, "r") as f:
        def hook(obj):
            def convert_empty_strings(value):
                if isinstance(value, str) and len(value) == 0:
                    return None
                return value
            obj = {k: convert_empty_strings(v) for k, v in obj.items()}
            return namedtuple("Config", obj.keys())(*obj.values())

        return json.load(f, object_hook=hook)
