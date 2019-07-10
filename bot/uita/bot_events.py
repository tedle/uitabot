"""Event triggers for Discord client to synchronize API state with uitabot."""
import asyncio
import discord

import uita.bot_commands
import uita.types
import uita.utils
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

    if uita.server.config.bot.trial_mode.enabled:
        tasks = [
            server.leave()
            for server in uita.bot.guilds
            if str(server.id) not in uita.server.config.bot.trial_mode.server_whitelist
        ]
        await asyncio.gather(*tasks, loop=uita.bot.loop)


def _sync_channels(guild):
    voice_channels = [
        channel for channel in uita.state.servers[str(guild.id)].channels.values()
        if channel.type is discord.ChannelType.voice
    ]
    uita.server.send_all(uita.message.ChannelListSendMessage(voice_channels), str(guild.id))


def _verify_member(member):
    role = uita.state.server_get_role(str(member.guild.id))
    return uita.utils.verify_user_permissions(member, role)


@uita.bot.event
@bot_ready
async def on_guild_channel_create(channel):
    discord_channel = uita.types.DiscordChannel(
        channel.id, channel.name, channel.type, channel.position
    )
    uita.state.channel_add(discord_channel, str(channel.guild.id))
    _sync_channels(channel.guild)


@uita.bot.event
@bot_ready
async def on_guild_channel_delete(channel):
    uita.state.channel_remove(str(channel.id), str(channel.guild.id))
    _sync_channels(channel.guild)


@uita.bot.event
@bot_ready
async def on_guild_channel_update(before, after):
    discord_channel = uita.types.DiscordChannel(
        after.id, after.name, after.type, after.position
    )
    uita.state.channel_add(discord_channel, str(after.guild.id))
    _sync_channels(after.guild)


@uita.bot.event
@bot_ready
async def on_member_join(member):
    if _verify_member(member):
        uita.state.server_add_user(str(member.guild.id), str(member.id), member.name)


@uita.bot.event
@bot_ready
async def on_member_remove(member):
    uita.state.server_remove_user(str(member.guild.id), str(member.id))
    # Kick any displaced users
    await uita.server.verify_active_servers()


@uita.bot.event
@bot_ready
async def on_member_update(before, after):
    if (
        not _verify_member(before) and
        _verify_member(after)
    ):
        await on_member_join(after)
    elif (
        _verify_member(before) and
        not _verify_member(after)
    ):
        await on_member_remove(after)


@uita.bot.event
@bot_ready
async def on_message(message):
    if (
        message.author.id == uita.bot.user.id
        or isinstance(message.channel, discord.abc.PrivateChannel)
    ):
        return
    await uita.bot_commands.parse(message)


@uita.bot.event
@bot_ready
async def on_guild_join(guild):
    channels = {
        str(channel.id): uita.types.DiscordChannel(
            channel.id, channel.name, channel.type, channel.position
        )
        for channel in guild.channels
    }
    users = {
        str(user.id): user.name
        for user in guild.members
        if _verify_member(user)
    }
    discord_server = uita.types.DiscordServer(
        guild.id,
        guild.name,
        channels,
        users,
        guild.icon
    )
    uita.state.server_add(discord_server, uita.bot)
    log.info("Joined {}".format(discord_server.name))

    if (
        uita.server.config.bot.trial_mode.enabled and
        str(guild.id) not in uita.server.config.bot.trial_mode.server_whitelist
    ):
        async def trial_leave():
            await asyncio.sleep(60 * 60, loop=uita.bot.loop)
            await uita.bot.wait_until_ready()
            trial_server = discord.utils.get(uita.bot.guilds, id=guild.id)
            if trial_server:
                await trial_server.leave()
        uita.bot.loop.create_task(trial_leave())
        if guild.system_channel:
            await guild.system_channel.send((
                "Hello! This is a trial version of **uitabot** and will leave the server shortly."
                " If you want unrestricted access, you can host your own instance for free @ {}"
                ).format(uita.__url__)
            )


@uita.bot.event
@bot_ready
async def on_guild_remove(guild):
    log.info("Leaving {}".format(guild.name))
    uita.state.server_remove(str(guild.id))
    # Kick any displaced users
    await uita.server.verify_active_servers()


@uita.bot.event
@bot_ready
async def on_guild_update(before, after):
    channels = {
        str(channel.id): uita.types.DiscordChannel(
            channel.id, channel.name, channel.type, channel.position
        )
        for channel in after.channels
    }
    users = {
        str(user.id): user.name
        for user in after.members
        if _verify_member(user)
    }
    discord_server = uita.types.DiscordServer(
        after.id,
        after.name,
        channels,
        users,
        after.icon
    )
    uita.state.server_add(discord_server, uita.bot.loop)
    # Kick any displaced users
    await uita.server.verify_active_servers()


@uita.bot.event
@bot_ready
async def on_voice_state_update(member, before, after):
    if member.id == uita.bot.user.id:
        channel = uita.types.DiscordChannel(
            after.channel.id,
            after.channel.name,
            after.channel.type,
            after.channel.position
        ) if after.channel is not None else None
        message = uita.message.ChannelActiveSendMessage(channel)
        uita.server.send_all(message, str(member.guild.id))
    else:
        # Member is leaving a channel, check if bot is in that channel and if it is now empty
        if before.channel is not None:
            bot_voice = uita.state.voice_connections[str(before.channel.guild.id)]
            if (
                bot_voice.active_channel is not None and
                str(before.channel.id) == bot_voice.active_channel.id and
                len(before.channel.members) <= 1
            ):
                await bot_voice.disconnect()
