import uita.types
from uita import bot, state

import logging
log = logging.getLogger(__name__)


def bot_ready(function):
    async def wrapper(*args, **kwargs):
        await bot.wait_until_ready()
        return await function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper


@bot.event
async def on_ready():
    log.info("Bot connected to Discord")
    state.initialize_from_bot(bot)


@bot.event
@bot_ready
async def on_channel_create(channel):
    discord_channel = uita.types.DiscordChannel(
        channel.id, channel.name, channel.type, channel.position
    )
    state.channel_add(discord_channel, channel.server.id)


@bot.event
@bot_ready
async def on_channel_delete(channel):
    state.channel_remove(channel.id, channel.server.id)


@bot.event
@bot_ready
async def on_channel_update(before, after):
    discord_channel = uita.types.DiscordChannel(
        after.id, after.name, after.type, after.position
    )
    state.channel_add(discord_channel, after.server.id)


@bot.event
@bot_ready
async def on_member_join(member):
    state.user_add_server(member.id, member.name, member.server.id)


@bot.event
@bot_ready
async def on_member_remove(member):
    state.user_remove_server(member.id, member.server.id)


@bot.event
@bot_ready
async def on_member_update(before, after):
    return


@bot.event
@bot_ready
async def on_server_join(server):
    channels = {
        channel.id: uita.types.DiscordChannel(
            channel.id, channel.name, channel.type, channel.position
        )
        for channel in server.channels
    }
    users = {user.id: user.name for user in server.members}
    discord_server = uita.types.DiscordServer(server.id, server.name, channels, users)
    uita.state.server_add(discord_server)


@bot.event
@bot_ready
async def on_server_remove(server):
    uita.state.server_remove(server.id)


@bot.event
@bot_ready
async def on_server_update(before, after):
    channels = {
        channel.id: uita.types.DiscordChannel(
            channel.id, channel.name, channel.type, channel.position
        )
        for channel in after.channels
    }
    users = {user.id: user.name for user in after.members}
    discord_server = uita.types.DiscordServer(after.id, after.name, channels, users)
    uita.state.server_add(discord_server)
