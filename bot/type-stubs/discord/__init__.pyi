from typing import overload, Any, Awaitable, Callable, List, Optional, Tuple, Union
from typing_extensions import Literal

import asyncio
import enum

from discord import abc as abc, errors as errors, opus as opus, utils as utils  # noqa: F401


class Activity:
    def __init__(self, *, name: str = ..., type: "ActivityType" = ...) -> None: ...


class ActivityType(enum.Enum):
    unknown: int
    playing: int
    streaming: int
    listening: int
    watching: int


class Asset:
    def __str__(self) -> str: ...


class AudioSource:
    ...


class ChannelType(enum.Enum):
    voice: int


class Client:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = ...) -> None: ...
    def event(self, coro: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]: ...
    def get_guild(self, id: int) -> "Optional[Guild]": ...

    async def change_presence(
        self,
        *,
        activity: Optional[Union["Game", "Streaming", "Activity"]] = ...,
        status: Optional["Status"] = ...,
        afk: Optional[bool] = ...
    ) -> None: ...
    async def logout(self) -> None: ...
    async def start(self, token: str, *, bot: bool = ...) -> None: ...

    @overload  # noqa: F811
    async def wait_for(
        self,
        event: Literal["reaction_add"],
        *,
        check: Optional[Callable[..., bool]] = ...,
        timeout: Optional[float] = ...
    ) -> Tuple["Reaction", Any]: ...

    @overload  # noqa: F811
    async def wait_for(
        self,
        event: str,
        *,
        check: Optional[Callable[..., bool]] = ...,
        timeout: Optional[float] = ...
    ) -> Any: ...
    async def wait_until_ready(self) -> None: ...

    guilds: List["Guild"]
    loop: asyncio.AbstractEventLoop
    user: "User"


class Colour:
    ...


class Embed:
    class Empty:
        ...

    def __init__(
        self,
        title: str = ...,
        description: str = ...,
        color: Union[Colour, int] = ...
    ) -> None: ...
    def add_field(self, *, name: str, value: str, inline: bool = ...) -> None: ...

    def set_author(
        self,
        *,
        name: str, url: Union[str, Empty] = ...,
        icon_url: Union[str, Empty] = ...
    ) -> None: ...
    def set_thumbnail(self, *, url: str) -> None: ...


class File:
    ...


class Game:
    ...


class Guild:
    def get_channel(self, id: int) -> Optional[abc.GuildChannel]: ...
    def get_member(self, id: int) -> "Optional[Member]": ...
    async def leave(self) -> None: ...

    channels: List[abc.GuildChannel]
    id: int
    me: "Member"
    members: List["Member"]
    name: str
    icon: Optional[str]
    roles: List["Role"]
    system_channel: Optional["TextChannel"]


class Member:
    avatar_url: Asset
    guild: Guild
    guild_permissions: "Permissions"
    id: int
    name: str
    roles: List["Role"]
    voice: Optional["VoiceState"]


class Message:
    async def add_reaction(str, emoji: str) -> None: ...

    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        embed: Optional[Embed] = ...,
        suppress: bool = ...,
        delete_after: Optional[float] = ...
    ) -> None: ...
    async def delete(self) -> None: ...

    author: Member
    channel: abc.GuildChannel
    content: str
    guild: Guild
    id: int
    role_mentions: List["Role"]


class PCMVolumeTransformer(AudioSource):
    def __init__(self, original: AudioSource, volume: float = ...) -> None: ...


class Permissions:
    administrator: bool
    connect: bool
    read_messages: bool


class Reaction:
    message: Message
    emoji: str


class Role:
    guild: Guild
    id: int
    name: str
    permissions: Permissions


class Status:
    ...


class Streaming:
    ...


class TextChannel(abc.GuildChannel):
    ...


class User:
    id: int
    name: str


class VoiceChannel(abc.GuildChannel):
    async def connect(self, *, timeout: float = ..., reconnect: bool = ...) -> "VoiceClient": ...

    members: List[Member]


class VoiceClient:
    def is_connected(self) -> bool: ...

    def play(
        self,
        source: AudioSource,
        *,
        after: Optional[Callable[[Exception], Any]] = ...
    ) -> None: ...
    def stop(self) -> None: ...

    async def disconnect(self, *, force: bool = ...) -> None: ...
    async def move_to(self, channel: VoiceChannel) -> None: ...

    channel: VoiceChannel
    encoder: opus.Encoder


class VoiceState:
    channel: VoiceChannel
