"""Bot commands issued by Discord chat."""
import asyncio
import discord
from typing import Any, Awaitable, Callable, Dict
from typing_extensions import Final

import uita.bot_events
import uita.types
import uita.utils
import uita.youtube_api
import uita

import logging
log = logging.getLogger(__name__)


# With how generator routing works some kind of global soup was inevitable
_COMMAND_PREFIX = "."
_COMMANDS = {}
_COMMAND_HELP = []
_EMBED_COLOUR: Final = 14721770
_EMOJI: Final[Dict[str, Any]] = {
    "ok": "\u2B55",
    "error": "\u274C",
    "loading": "\U0001F504",
    "wait": "\u2753",
    "sound": "\U0001F3B5",
    "numbers": {
        1: b"1\xe2\x83\xa3".decode("utf-8"),
        2: b"2\xe2\x83\xa3".decode("utf-8"),
        3: b"3\xe2\x83\xa3".decode("utf-8"),
        4: b"4\xe2\x83\xa3".decode("utf-8"),
        5: b"5\xe2\x83\xa3".decode("utf-8")
    }
}


CommandCallbackType = Callable[[discord.Message, str], Awaitable[None]]


def command(
    *args: str,
    help: str = "No description",
    require_administrator: bool = False
) -> Callable[[CommandCallbackType], CommandCallbackType]:
    """Decorator to bind bot commands to a given function.

    Callback function should accept a ``discord.Message`` and ``str`` as its parameters.

    Args:
        *args: Commands to be bound to this function.
        help: Descriptive message provided when help command is called.
        require_administrator: Require administrator privileges to use command.

    """
    def decorator(function: CommandCallbackType) -> CommandCallbackType:
        async def wrapper(message: discord.Message, params: str) -> None:
            # Check if command requires admin privileges
            if (
                require_administrator and
                not message.author.guild_permissions.administrator
            ):
                await message.channel.send(
                    f"{_EMOJI['error']} This command requires administrator privileges"
                )
                return
            # Check if command is role restricted
            role = uita.state.server_get_role(str(message.author.guild.id))
            if not uita.utils.verify_user_permissions(message.author, role):
                await message.channel.send(
                    f"{_EMOJI['error']} Insufficient privileges for bot commands"
                )
                return
            # Run command
            return await function(message, params)

        for arg in args:
            _COMMANDS[arg] = wrapper
        _COMMAND_HELP.append((args, help))
        return wrapper
    return decorator


async def parse(message: discord.Message) -> None:
    """Parses a message for commands and dispatches to a matching callback.

    Sends an error message to the corresponding Discord channel if command does not exist.

    Args:
        message: Message to be run.

    """
    # Check that message is using command syntax
    if (
        not message.content.startswith(_COMMAND_PREFIX)
        or len(message.content) <= len(_COMMAND_PREFIX)
    ):
        return
    # Separate message command and parameters by the first space and strip the prefix
    command, _, params = message.content[len(_COMMAND_PREFIX):].partition(" ")
    try:
        if command in _COMMANDS:
            log.debug(f"[{message.author.name}:{message.author.id}] "
                      f"{message.content} -> {message.guild.name}")
            await _COMMANDS[command](message, params)
    except discord.errors.Forbidden as e:
        log.warn(f"Failure using Discord API in "
                 f"{message.guild.name}({message.guild.id}): {e.text}")


async def set_prefix(prefix: str) -> None:
    """Sets the prefix used to trigger bot commands. Updates client presence to show help command.

    Args:
        prefix: Command prefix.

    """
    global _COMMAND_PREFIX
    _COMMAND_PREFIX = prefix
    await uita.bot.change_presence(
        activity=discord.Activity(
            name=f"{_COMMAND_PREFIX}help",
            type=discord.ActivityType.listening
        )
    )


@command("help", "?", help="Shows this potentially useful message")
async def help(message: discord.Message, params: str) -> None:
    help_message = discord.Embed(
        title="Help info",
        description=(
            "**{}** can be controlled using the web client at {}\n\n" +
            "**Commands**"
        ).format(uita.bot.user.name, uita.utils.build_client_url(uita.server.config)),
        color=_EMBED_COLOUR
    )
    for cmd in _COMMAND_HELP:
        name = ", ".join([f"`{_COMMAND_PREFIX}{c}`" for c in cmd[0]])
        help_message.add_field(
            name=name,
            value=cmd[1],
            inline=False
        )
    await message.channel.send("", embed=help_message)


@command("play", "p", help="Enqueues a provided `<URL>`")
async def play(message: discord.Message, params: str) -> None:
    voice = uita.state.voice_connections[str(message.guild.id)]
    user = uita.types.DiscordUser(
        str(message.author.id),
        message.author.name,
        str(message.author.display_avatar.url),
        str(message.guild.id)
    )
    response = await message.channel.send(f"{_EMOJI['loading']} Processing...")
    try:
        await voice.enqueue_url(params, user)
        await response.edit(content=f"{_EMOJI['ok']} Got it!")
    except uita.exceptions.ClientError as error:
        if error.message.header == uita.message.ErrorQueueFullMessage.header:
            await response.edit(content=f"{_EMOJI['error']} Queue is full, sorry!")
        elif error.message.header == uita.message.ErrorUrlInvalidMessage.header:
            await response.edit(content=f"{_EMOJI['error']} That URL was no good, sorry!")
        else:
            await response.edit(content=f"{_EMOJI['error']} Not feeling up to it, sorry!")
            log.error(f"Uncaught exception in play {error.message.header}")
    except Exception:
        await response.edit(content=f"{_EMOJI['error']} Not feeling up to it, sorry!")
        raise


@command("search", "s", help="Searches YouTube for a provided `<QUERY>`")
async def search(message: discord.Message, params: str) -> None:
    response = await message.channel.send(f"{_EMOJI['loading']} Searching...")
    try:
        # Scrape YouTube for search result
        result_max = 5
        results = await uita.youtube_api.search(
            params,
            api_key=uita.server.config.youtube.api_key,
            referrer=uita.utils.build_client_url(uita.server.config),
            results=result_max,
            loop=uita.bot.loop
        )
        results_found = min(result_max, len(results))
        if results_found == 0:
            raise uita.exceptions.ClientError(uita.message.ErrorUrlInvalidMessage())

        # Build a choice picking menu from the results
        description = ""
        for i in range(results_found):
            result = results[i]
            emoji = _EMOJI["numbers"][i+1]
            description += "{}**{}** ({})\n".format(
                emoji,
                result["title"],
                "Live" if result["live"] else "{:0>2}:{:0>2}:{:0>2}".format(
                    int(result["duration"] / (60 * 60)),
                    int((result["duration"] / 60) % 60),
                    int(result["duration"] % 60)
                )
            )
        embed_results = discord.Embed(
            title="Search results",
            description=description,
            color=_EMBED_COLOUR
        )
        # Display the results to the user
        await response.edit(
            content=f"{_EMOJI['wait']} Choose your future song",
            embed=embed_results
        )

        # Build a responsive UI out of emoji reactions
        async def add_reactions() -> None:
            for i in range(results_found):
                emoji = _EMOJI["numbers"][i+1]
                await response.add_reaction(emoji)
        # Run the task separately so if a reaction is clicked while the loop is running we will
        # still respond to it
        uita.bot.loop.create_task(add_reactions())

        # Wait for the user to make a choice
        def reaction_predicate(reaction: discord.Reaction, user: discord.Member) -> bool:
            valid_emoji = [_EMOJI["numbers"][i+1] for i in range(results_found)]
            return (
                reaction.message.id == response.id
                and user.id == message.author.id
                and reaction.emoji in valid_emoji
            )
        try:
            reaction, _ = await uita.bot.wait_for(
                "reaction_add",
                timeout=30.0,
                check=reaction_predicate
            )
        except asyncio.TimeoutError:
            await response.delete()
            return
        # Translate the raw emoji code back into a choice index
        choice = reaction.emoji
        choice_index = None
        for index, value in _EMOJI["numbers"].items():
            if choice == value:
                choice_index = index - 1
        if choice_index is None or choice_index < 0 or choice_index > results_found:
            await response.edit(content=f"{_EMOJI['error']} There were unicode problems, sorry!")
            return
        # We finally have a song to queue!
        song = results[choice_index]
        # Load it up...
        voice = uita.state.voice_connections[str(message.guild.id)]
        user = uita.types.DiscordUser(
            str(message.author.id),
            message.author.name,
            str(message.author.display_avatar.url),
            str(message.guild.id)
        )
        await voice.enqueue_url(song["url"], user)
        # Build an embedded (nice looking) message that describes the song
        song_info = discord.Embed(
            color=_EMBED_COLOUR
        )
        song_info.set_author(
                name=song["title"],
                url=song["url"]
        )
        song_info.set_thumbnail(url=song["thumbnail"])
        song_info.add_field(
            name="Uploader",
            value=song["uploader"],
            inline=True
        )
        song_info.add_field(
            name="Duration",
            value="Live" if song["live"] else "{:0>2}:{:0>2}:{:0>2}".format(
                int(song["duration"] / (60 * 60)),
                int((song["duration"] / 60) % 60),
                int(song["duration"] % 60)
            ),
            inline=True
        )
        # Finally display the enqueued song to the user
        await response.edit(
            content=f"{_EMOJI['ok']} Enqueued",
            embed=song_info
        )
    except uita.exceptions.ClientError as error:
        if error.message.header == uita.message.ErrorQueueFullMessage.header:
            await response.edit(content=f"{_EMOJI['error']} Queue is full, sorry!")
        elif error.message.header == uita.message.ErrorUrlInvalidMessage.header:
            await response.edit(content=f"{_EMOJI['error']} That URL was no good, sorry!")
        else:
            await response.edit(content=f"{_EMOJI['error']} Not feeling up to it, sorry!")
            log.error(f"Uncaught exception in play {error.message.header}")
    except Exception:
        await response.edit(content=f"{_EMOJI['error']} Not feeling up to it, sorry!")
        raise


@command("skip", help="Skips the currently playing song")
async def skip(message: discord.Message, params: str) -> None:
    voice = uita.state.voice_connections[str(message.guild.id)]
    queue = voice.queue()
    if len(queue) > 0:
        await voice.remove(queue[0].id)
        await message.channel.send(f"{_EMOJI['ok']} Skipped `{queue[0].title}`")
    else:
        await message.channel.send(f"{_EMOJI['error']} The queue is already empty")


@command("shuffle", "sh", help="Shuffles the playback queue")
async def shuffle(message: discord.Message, params: str) -> None:
    voice = uita.state.voice_connections[str(message.guild.id)]
    queue = voice.queue()
    if len(queue) > 0:
        await voice.shuffle()
        await message.channel.send(f"{_EMOJI['ok']} Shuffled queue")
    else:
        await message.channel.send(f"{_EMOJI['error']} The queue is currently empty")


@command("clear", help="Empties the playback queue")
async def clear(message: discord.Message, params: str) -> None:
    voice = uita.state.voice_connections[str(message.guild.id)]
    # Start from the back so we don't have to await currently playing songs
    for track in reversed(voice.queue()):
        await voice.remove(track.id)
    await message.channel.send(f"{_EMOJI['ok']} The queue has been emptied")


@command("join", "j", help="Joins your voice channel")
async def join(message: discord.Message, params: str) -> None:
    message_voice = message.author.voice
    if message_voice is not None:
        bot_voice = uita.state.voice_connections[str(message.guild.id)]
        await bot_voice.connect(str(message_voice.channel.id))
    else:
        await message.channel.send(
            f"{_EMOJI['error']} You aren't in a voice channel (that I can see)"
        )


@command("leave", "l", help="Leaves the voice channel")
async def leave(message: discord.Message, params: str) -> None:
    voice = uita.state.voice_connections[str(message.guild.id)]
    await voice.disconnect()


@command("nowplaying", "np", help="Shows currently playing song")
async def nowplaying(message: discord.Message, params: str) -> None:
    voice = uita.state.voice_connections[str(message.guild.id)]
    queue = voice.queue()
    description = ""

    if voice.status() == uita.audio.Status.PLAYING and len(queue) > 0:
        track = queue[0]
        source = ""
        if track.local:
            source = "File upload"
        elif track.url is not None:
            source = f"[URL]({track.url})"
        else:
            source = "Unknown"
        description = f"{_EMOJI['sound']} Now playing **{track.title}** ({source})"
    else:
        description = f"{_EMOJI['sound']} Now playing **John Cage - 4'33**"

    track_message = discord.Embed(description=description, color=_EMBED_COLOUR)
    await message.channel.send("", embed=track_message)


@command(
    "set-role",
    help="Set a `<ROLE>` needed to use bot commands. Leave empty for free access",
    require_administrator=True
)
async def set_role(message: discord.Message, params: str) -> None:
    role = None
    if len(message.role_mentions) > 0:
        role = str(message.role_mentions[0].id)
    elif len(params) > 0:
        role_search = discord.utils.get(message.guild.roles, name=params)
        if role_search is None:
            await message.channel.send(f"{_EMOJI['error']} This role does not exist")
            return
        role = str(role_search.id)

    uita.state.server_set_role(str(message.guild.id), role)
    await uita.bot_events.on_guild_update(message.guild, message.guild)
    await message.channel.send(f"{_EMOJI['ok']} Updated role required for using bot commands")
