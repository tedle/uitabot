"""Event triggers for Discord client to synchronize API state with uitabot."""
import discord

import uita.bot_commands
import uita.types
import uita

import logging
log = logging.getLogger(__name__)


def bot_ready(function):
    """Decorator that awaits execution of a function until Discord client is ready."""
    async def wrapper(*args, **kwargs):
        await uita.bot.wait_until_ready()
        return await function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper


@uita.bot.event
async def on_ready():
    log.info("Bot connected to Discord")
    uita.state.initialize_from_bot(uita.bot)
    await uita.bot_commands.set_prefix(".")


def _sync_channels(server):
    voice_channels = [
        channel for channel in uita.state.servers[server.id].channels.values()
        if channel.type is discord.ChannelType.voice
    ]
    uita.server.send_all(uita.message.ChannelListSendMessage(voice_channels), server.id)


@uita.bot.event
@bot_ready
async def on_channel_create(channel):
    discord_channel = uita.types.DiscordChannel(
        channel.id, channel.name, channel.type, channel.position
    )
    uita.state.channel_add(discord_channel, channel.server.id)
    _sync_channels(channel.server)


@uita.bot.event
@bot_ready
async def on_channel_delete(channel):
    uita.state.channel_remove(channel.id, channel.server.id)
    _sync_channels(channel.server)


@uita.bot.event
@bot_ready
async def on_channel_update(before, after):
    discord_channel = uita.types.DiscordChannel(
        after.id, after.name, after.type, after.position
    )
    uita.state.channel_add(discord_channel, after.server.id)
    _sync_channels(after.server)


@uita.bot.event
@bot_ready
async def on_member_join(member):
    uita.state.user_add_server(member.id, member.name, member.server.id)


@uita.bot.event
@bot_ready
async def on_member_remove(member):
    uita.state.user_remove_server(member.id, member.server.id)
    # Kick any displaced users
    await uita.server.verify_active_servers()


@uita.bot.event
@bot_ready
async def on_member_update(before, after):
    return


@uita.bot.event
@bot_ready
async def on_message(message):
    if message.author == uita.bot.user or message.channel.is_private is True:
        return
    await uita.bot_commands.parse(message)


@uita.bot.event
@bot_ready
async def on_server_join(server):
    channels = {
        channel.id: uita.types.DiscordChannel(
            channel.id, channel.name, channel.type, channel.position
        )
        for channel in server.channels
    }
    users = {user.id: user.name for user in server.members}
    discord_server = uita.types.DiscordServer(server.id, server.name, channels, users, server.icon)
    uita.state.server_add(discord_server, uita.bot)


@uita.bot.event
@bot_ready
async def on_server_remove(server):
    uita.state.server_remove(server.id)
    # Kick any displaced users
    await uita.server.verify_active_servers()


@uita.bot.event
@bot_ready
async def on_server_update(before, after):
    channels = {
        channel.id: uita.types.DiscordChannel(
            channel.id, channel.name, channel.type, channel.position
        )
        for channel in after.channels
    }
    users = {user.id: user.name for user in after.members}
    discord_server = uita.types.DiscordServer(after.id, after.name, channels, users, after.icon)
    uita.state.server_add(discord_server, uita.bot.loop)
    # Kick any displaced users
    await uita.server.verify_active_servers()


@uita.bot.event
@bot_ready
async def on_voice_state_update(before, after):
    if after != uita.bot.user:
        return
    channel = uita.types.DiscordChannel(
        after.voice.voice_channel.id,
        after.voice.voice_channel.name,
        after.voice.voice_channel.type,
        after.voice.voice_channel.position
    ) if after.voice.voice_channel is not None else None
    message = uita.message.ChannelActiveSendMessage(channel)
    uita.server.send_all(message, after.server.id)
