"""Bot commands issued by Discord chat."""
import asyncio
import discord

import uita.types
import uita.youtube_api
import uita

import logging
log = logging.getLogger(__name__)


# With how generator routing works some kind of global soup was inevitable
_COMMAND_PREFIX = "."
_COMMANDS = {}
_COMMAND_HELP = []
_EMBED_COLOUR = 14721770
_EMOJI = {
    "ok": "\u2B55",
    "error": "\u274C",
    "loading": "\U0001F504",
    "wait": "\u2753",
    "numbers": {
        1: b"1\xe2\x83\xa3".decode("utf-8"),
        2: b"2\xe2\x83\xa3".decode("utf-8"),
        3: b"3\xe2\x83\xa3".decode("utf-8"),
        4: b"4\xe2\x83\xa3".decode("utf-8"),
        5: b"5\xe2\x83\xa3".decode("utf-8")
    }
}


def command(*args, **kwargs):
    """Decorator to bind bot commands to a given function.

    Callback function should accept a `discord.Message` and `str` as its parameters.

    Parameters
    ----------
    *args : str
        List of commands to be bound to this function.
    help : str, optional
        Descriptive message provided when help command is called.

    """
    def decorator(function):
        async def wrapper(message, params):
            return await function(message, params)
        for arg in args:
            _COMMANDS[arg] = wrapper
        _COMMAND_HELP.append((args, kwargs.get("help", "No description")))
        return wrapper
    return decorator


async def parse(message):
    """Parses a message for commands and dispatches to a matching callback.

    Sends an error message to the corresponding Discord channel if command does not exist.

    Parameters
    ----------
    message : discord.Message
        Message to be run.

    """
    # Check that message is using command syntax
    if (
        not message.content.startswith(_COMMAND_PREFIX)
        or len(message.content) <= len(_COMMAND_PREFIX)
    ):
        return
    # Separate message command and parameters by the first space and strip the prefix
    command, _, params = message.content[len(_COMMAND_PREFIX):].partition(" ")
    if command in _COMMANDS:
        await _COMMANDS[command](message, params)
    else:
        await message.channel.send((
            "{} Unknown command. Try `{}help` for a list of commands."
            ).format(_EMOJI["error"], _COMMAND_PREFIX)
        )


async def set_prefix(prefix):
    """Sets the prefix used to trigger bot commands. Updates client presence to show help command.

    Parameters
    ----------
    prefix : str
        Command prefix.

    """
    global _COMMAND_PREFIX
    _COMMAND_PREFIX = prefix
    await uita.bot.change_presence(
        activity=discord.Activity(
            name="{}help".format(_COMMAND_PREFIX),
            type=discord.ActivityType.listening
        )
    )


@command("help", "?", help="Shows this potentially useful message")
async def help(message, params):
    help_message = discord.Embed(
        title="Help info",
        description=(
            "**{}** can be controlled using the web client at {}\n\n" +
            "**Commands**"
        ).format(uita.bot.user.name, uita.utils.build_client_url(uita.server.config)),
        color=_EMBED_COLOUR
    )
    for cmd in _COMMAND_HELP:
        name = ", ".join(["`{}{}`".format(_COMMAND_PREFIX, c) for c in cmd[0]])
        help_message.add_field(
            name=name,
            value=cmd[1],
            inline=False
        )
    await message.channel.send("", embed=help_message)


@command("play", "p", help="Enqueues a provided `<URL>`")
async def play(message, params):
    voice = uita.state.voice_connections[str(message.guild.id)]
    user = uita.types.DiscordUser(
        message.author.id,
        message.author.name,
        str(message.author.avatar_url),
        None,
        message.guild.id
    )
    response = await message.channel.send("{} Processing...".format(_EMOJI["loading"]))
    try:
        await voice.enqueue_url(params, user)
        await response.edit(
            content="{} Got it!".format(_EMOJI["ok"])
        )
    except uita.exceptions.ClientError as error:
        if error.message.header == uita.message.ErrorQueueFullMessage.header:
            await response.edit(
                content="{} Queue is full, sorry!".format(_EMOJI["error"])
            )
        elif error.message.header == uita.message.ErrorUrlInvalidMessage.header:
            await response.edit(
                content="{} That URL was no good, sorry!".format(_EMOJI["error"])
            )
        else:
            await response.edit(
                content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
            )
            log.warn("Uncaught exception in play {}".format(error.message.header))
    except Exception:
        await response.edit(
            content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
        )
        raise


@command("search", "s", help="Searches YouTube for a provided `<QUERY>`")
async def search(message, params):
    response = await message.channel.send("{} Searching...".format(_EMOJI["loading"]))
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
            content="{} Choose your future song".format(_EMOJI["wait"]),
            embed=embed_results
        )

        # Build a responsive UI out of emoji reactions
        async def add_reactions():
            for i in range(results_found):
                emoji = _EMOJI["numbers"][i+1]
                await response.add_reaction(emoji)
        # Run the task separately so if a reaction is clicked while the loop is running we will
        # still respond to it
        uita.bot.loop.create_task(add_reactions())
        # Wait for the user to make a choice
        def reaction_predicate(reaction, user):
            valid_emoji = [_EMOJI["numbers"][i+1] for i in range(results_found)]
            return (
                reaction.message.id == response.id
                and user.id == message.author.id
                and reaction.emoji in valid_emoji
            )
        try:
            reaction, _ = await uita.bot.wait_for(
                "reaction_add",
                timeout=30,
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
            await response.edit(
                content="{} There were unicode problems, sorry!".format(_EMOJI["error"])
            )
            return
        # We finally have a song to queue!
        song = results[choice_index]
        # Load it up...
        voice = uita.state.voice_connections[str(message.guild.id)]
        user = uita.types.DiscordUser(
            message.author.id,
            message.author.name,
            str(message.author.avatar_url),
            None,
            message.guild.id
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
            content="{} Enqueued".format(_EMOJI["ok"]),
            embed=song_info
        )
    except uita.exceptions.ClientError as error:
        if error.message.header == uita.message.ErrorQueueFullMessage.header:
            await response.edit(
                content="{} Queue is full, sorry!".format(_EMOJI["error"])
            )
        elif error.message.header == uita.message.ErrorUrlInvalidMessage.header:
            await response.edit(
                content="{} That URL was no good, sorry!".format(_EMOJI["error"])
            )
        else:
            await response.edit(
                content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
            )
            log.warn("Uncaught exception in play {}".format(error.message.header))
    except Exception:
        await response.edit(
            content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
        )
        raise


@command("skip", help="Skips the currently playing song")
async def skip(message, params):
    voice = uita.state.voice_connections[str(message.guild.id)]
    queue = voice.queue()
    if len(queue) > 0:
        await voice.remove(queue[0].id)
        await message.channel.send("{} Skipped `{}`".format(_EMOJI["ok"], queue[0].title))
    else:
        await message.channel.send("{} The queue is already empty".format(_EMOJI["error"]))


@command("clear", help="Empties the playback queue")
async def clear(message, params):
    voice = uita.state.voice_connections[str(message.guild.id)]
    # Start from the back so we don't have to await currently playing songs
    for track in reversed(voice.queue()):
        await voice.remove(track.id)
    await message.channel.send("{} The queue has been emptied".format(_EMOJI["ok"]))


@command("join", "j", help="Joins your voice channel")
async def join(message, params):
    channel = message.author.voice.voice_channel
    if channel is not None:
        voice = uita.state.voice_connections[str(message.guild.id)]
        await voice.connect(channel.id)
    else:
        await message.channel.send("{} You aren't in a voice channel (that I can see)".format(_EMOJI["error"]))


@command("leave", "l", help="Leaves the voice channel")
async def leave(message, params):
    voice = uita.state.voice_connections[str(message.guild.id)]
    await voice.disconnect()
