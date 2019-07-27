from discord import Embed, File, Guild, Member, Message, Permissions, ChannelType
from typing import List, Optional


class Messageable:
    async def send(
        self,
        content: Optional[str],
        *,
        tts: bool = ...,
        embed: Optional[Embed] = ...,
        file: Optional[File] = ...,
        files: Optional[List[File]] = ...,
        delete_after: Optional[float] = ...,
        nonce: Optional[int] = ...
    ) -> Message: ...


class GuildChannel(Messageable):
    def permissions_for(self, member: Member) -> Permissions: ...
    category_id: int
    guild: Guild
    id: int
    name: str
    position: int
    type: ChannelType


class PrivateChannel(Messageable):
    ...
