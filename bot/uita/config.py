import json
from collections import namedtuple


def load(filename):
    with open(filename, "r") as f:
        # Converts JSON dict into namedtuple
        def hook(obj):
            def convert_empty_strings(value):
                if isinstance(value, str) and len(value) == 0:
                    return None
                return value
            obj = {k: convert_empty_strings(v) for k, v in obj.items()}
            return namedtuple("Config", obj.keys())(*obj.values())

        return json.load(f, object_hook=hook)
