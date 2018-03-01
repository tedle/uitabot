"""Event triggers for web client to."""
import discord

import uita
import uita.message
import uita.types

import logging
log = logging.getLogger(__name__)


@uita.server.on_message("channel.join")
async def channel_join(event):
    """Connect the bot to a given channel of the active server."""
    log.debug("channel join {}".format(event.message.channel_id))
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.connect(uita.bot, event.message.channel_id)


@uita.server.on_message("channel.leave")
async def channel_leave(event):
    """Disconnect the bot from the voice channel of the active server."""
    log.debug("channel leave")
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.disconnect()


@uita.server.on_message("channel.list.get")
async def channel_list_get(event):
    """Provide a list of available voice channels to client."""
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


@uita.server.on_message("server.join", require_active_server=False)
async def server_join(event):
    """Connect a user to the web client interface for a given Discord server."""
    log.debug("server join {}".format(event.message.server_id))
    # Check that user has access to this server
    if event.user.id in uita.state.servers[event.message.server_id].users:
        event.user.active_server_id = event.message.server_id
    else:
        await event.socket.send(str(uita.message.ServerKickMessage()))


@uita.server.on_message("server.list.get", require_active_server=False)
async def server_list_get(event):
    """Provide a list of all servers that the user and uitabot share membership in."""
    log.debug("server list get")
    discord_servers = [
        uita.types.DiscordServer(
            discord_server.id, discord_server.name, [], []
        )
        for key, discord_server in uita.state.servers.items()
        if event.user.id in discord_server.users
    ]
    await event.socket.send(str(uita.message.ServerListSendMessage(discord_servers)))


@uita.server.on_message("play.url")
async def play_url(event):
    """Still just a test function."""
    log.debug("play.url {}".format(event.message.url))
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.enqueue(event.message.url)
