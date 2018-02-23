import discord

from uita import bot, server
import uita.message
import uita.types

import logging
log = logging.getLogger(__name__)


@server.on_message("channel.list.get")
async def channel_list_get(event):
    log.debug("channel list get")
    server = bot.get_server(event.connection.user.active_server)
    if server is None:
        raise uita.exceptions.NoActiveServer
    discord_channels = [
        uita.types.DiscordChannel(
            discord_channel.id, discord_channel.name
        )
        for discord_channel in server.channels
        if discord_channel.type is discord.ChannelType.voice
    ]
    await event.connection.socket.send(str(uita.message.ChannelListSendMessage(discord_channels)))


@server.on_message("server.join")
async def server_join(event):
    log.debug("server join {}".format(event.message.server_id))
    log.warn("SERVER.JOIN USING UNSANITIZED, UNCHECKED USER INPUT")
    event.connection.user.active_server = event.message.server_id


@server.on_message("server.list.get")
async def server_list_get(event):
    log.debug("server list get")
    discord_servers = [
        uita.types.DiscordServer(
            discord_server.id, discord_server.name
        )
        for discord_server in bot.servers
    ]
    discord_servers.append(uita.types.DiscordServer(
        "incredibly_fake", "FAKE SERVER - REMINDER TO CROSS REFERENCE USER SERVERS"
    ))
    await event.connection.socket.send(str(uita.message.ServerListSendMessage(discord_servers)))


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
