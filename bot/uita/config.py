"""Loads JSON configuration files."""

import json
from typing import cast, Any, Dict, List, Optional, NamedTuple, Type, Union
from typing_extensions import Final

import uita.exceptions


# Can't use nested class defs until https://github.com/python/mypy/issues/5362 is fixed
class ConfigDiscordClient(NamedTuple):
    id: str
    secret: str


class ConfigDiscord(NamedTuple):
    client: ConfigDiscordClient
    token: str


class ConfigYoutube(NamedTuple):
    api_key: str


class ConfigBotTrialMode(NamedTuple):
    enabled: bool
    server_whitelist: List[str]


class ConfigBot(NamedTuple):
    domain: str
    port: int
    database: str
    verbose_logging: bool
    trial_mode: ConfigBotTrialMode


class ConfigClient(NamedTuple):
    domain: str
    port: int


class ConfigSSL(NamedTuple):
    cert_file: Optional[str]
    key_file: Optional[str]


class ConfigFile(NamedTuple):
    upload_max_size: int
    cache_max_size: int


class Config(NamedTuple):
    """Named tuple carrying configuration options. See :doc:`config` for documentation."""
    discord: ConfigDiscord
    youtube: ConfigYoutube
    bot: ConfigBot
    client: ConfigClient
    ssl: ConfigSSL
    file: ConfigFile


_ConfigType = Union[
    Config,
    ConfigDiscord,
    ConfigDiscordClient,
    ConfigYoutube,
    ConfigBot,
    ConfigBotTrialMode,
    ConfigClient,
    ConfigSSL,
    ConfigFile
]
_CONFIGNAMES: Final[Dict[str, Type[_ConfigType]]] = {
    "config": Config,
    "config.discord": ConfigDiscord,
    "config.discord.client": ConfigDiscordClient,
    "config.youtube": ConfigYoutube,
    "config.bot": ConfigBot,
    "config.bot.trial_mode": ConfigBotTrialMode,
    "config.client": ConfigClient,
    "config.ssl": ConfigSSL,
    "config.file": ConfigFile
}


def load(filename: str) -> Config:
    """Loads a JSON formatted config file.

    Converts empty strings to ``None``.

    Args:
        filename: Filename of config file to load.

    Returns:
        Object containing config file values as attributes.

    Raises:
        uita.exceptions.MalformedConfig: If config file does not match expected structure.
    """
    with open(filename, "r") as f:
        def convert_types(namespace: List[str], obj: Any) -> _ConfigType:
            try:
                for k, v in obj.items():
                    if not k.isidentifier():
                        raise ValueError
                    if isinstance(v, dict):
                        obj[k] = convert_types(namespace + [k], v)
                    # Convert empty strings to none
                    if isinstance(v, str) and len(v) == 0:
                        obj[k] = None
                return _CONFIGNAMES[".".join(namespace)](**obj)
            except (KeyError, TypeError, ValueError):
                raise uita.exceptions.MalformedConfig
        return cast(Config, convert_types(["config"], json.load(f)))
