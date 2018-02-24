import discord

from uita import server, state
import uita.message
import uita.types

import logging
log = logging.getLogger(__name__)


@server.on_message("channel.list.get")
async def channel_list_get(event):
    log.debug("channel list get")
    discord_channels = [
        uita.types.DiscordChannel(
            discord_channel.id,
            discord_channel.name,
            discord_channel.type,
            discord_channel.position
        )
        for key, discord_channel in event.active_server.channels.items()
        if discord_channel.type is discord.ChannelType.voice
    ]
    await event.socket.send(str(uita.message.ChannelListSendMessage(discord_channels)))


@server.on_message("server.join", require_active_server=False)
async def server_join(event):
    log.debug("server join {}".format(event.message.server_id))
    log.warn("SERVER.JOIN USING UNSANITIZED, UNCHECKED USER INPUT")
    event.user.active_server_id = event.message.server_id


@server.on_message("server.list.get", require_active_server=False)
async def server_list_get(event):
    log.debug("server list get")
    discord_servers = [
        uita.types.DiscordServer(
            discord_server.id, discord_server.name, [], []
        )
        for key, discord_server in state.servers.items()
    ]
    discord_servers.append(uita.types.DiscordServer(
        "incredibly_fake", "FAKE SERVER - REMINDER TO CROSS REFERENCE USER SERVERS", [], []
    ))
    await event.socket.send(str(uita.message.ServerListSendMessage(discord_servers)))


@server.on_message("play.url")
async def play_url(event):
    log.debug("play.url event:{}".format(event))
    try:
        import asyncio
        log.debug("sleep start")
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        log.debug("sleep cancelled")
    finally:
        log.debug("sleep end")
