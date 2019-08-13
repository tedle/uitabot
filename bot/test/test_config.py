import json

import uita.config


def test_load(data_dir):
    filename = data_dir / "config.test.json"
    uita_config = uita.config.load(filename)
    json_config = json.load(filename)

    def check(uita_obj, json_obj):
        for key, json_value in json_obj.items():
            uita_value = getattr(uita_obj, key, None)
            if isinstance(json_value, dict):
                # Messy (but recommended?) is-namedtuple check
                # https://bugs.python.org/issue7796
                assert hasattr(uita_value, "_fields")
                check(uita_value, json_value)
            elif isinstance(json_value, str):
                # Empty strings should be None
                assert isinstance(uita_value, type(json_value)) if uita_value is not None else True
            else:
                assert isinstance(uita_value, type(json_value))
    check(uita_config, json_config)
