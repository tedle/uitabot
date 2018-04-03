"""Bot commands issued by Discord chat."""
import discord

import uita.types
import uita.youtube
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
        await uita.bot.send_message(
            message.channel, (
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
        game=discord.Game(name="{}help".format(_COMMAND_PREFIX), type=2)
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
    await uita.bot.send_message(message.channel, content="", embed=help_message)


@command("play", "p", help="Enqueues a provided `<URL>`")
async def play(message, params):
    voice = uita.state.voice_connections[message.server.id]
    user = uita.types.DiscordUser(message.author.id, message.author.name, None, message.server.id)
    response = await uita.bot.send_message(
        message.channel,
        content="{} Processing...".format(_EMOJI["loading"])
    )
    try:
        await voice.enqueue_url(params, user)
        await uita.bot.edit_message(
            response,
            new_content="{} Got it!".format(_EMOJI["ok"])
        )
    except uita.exceptions.ClientError as error:
        if error.message.header == uita.message.ErrorQueueFullMessage.header:
            await uita.bot.edit_message(
                response,
                new_content="{} Queue is full, sorry!".format(_EMOJI["error"])
            )
        elif error.message.header == uita.message.ErrorUrlInvalidMessage.header:
            await uita.bot.edit_message(
                response,
                new_content="{} That URL was no good, sorry!".format(_EMOJI["error"])
            )
        else:
            await uita.bot.edit_message(
                response,
                new_content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
            )
            log.warn("Uncaught exception in play {}".format(error.message.header))
    except Exception:
        await uita.bot.edit_message(
            response,
            new_content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
        )
        raise


@command("search", "s", help="Searches YouTube for a provided `<QUERY>`")
async def search(message, params):
    response = await uita.bot.send_message(
        message.channel,
        content="{} Searching...".format(_EMOJI["loading"])
    )
    try:
        # Scrape YouTube for search result
        result_max = 5
        results = await uita.youtube.search(params, results=result_max, loop=uita.bot.loop)
        # Build a choice picking menu from the results
        description = ""
        for i in range(result_max):
            result = results[i]
            emoji = _EMOJI["numbers"][i+1]
            description += "{}**{}** ({})\n".format(
                emoji,
                result["title"],
                "live" if result["is_live"] else (str(result["duration"]) + "s")
            )
            # The reaction is a button that lets the user choose a result
            await uita.bot.add_reaction(response, emoji)
        embed_results = discord.Embed(
            title="Search results",
            description=description,
            color=_EMBED_COLOUR
        )
        # Display the results to the user
        await uita.bot.edit_message(
            response,
            new_content="{} Choose your future song".format(_EMOJI["wait"]),
            embed=embed_results
        )
        # Wait for the user to make a choice
        reaction = await uita.bot.wait_for_reaction(
            emoji=[_EMOJI["numbers"][i+1] for i in range(result_max)],
            message=response,
            user=message.author,
            timeout=10
        )
        # If we timed out just delete the message
        if reaction is None:
            await uita.bot.delete_message(response)
            return
        # Translate the raw emoji code back into a choice index
        choice = reaction.reaction.emoji
        choice_index = None
        for index, value in _EMOJI["numbers"].items():
            if choice == value:
                choice_index = index - 1
        if choice_index is None or choice_index < 0 or choice_index > result_max:
            await uita.bot.edit_message(
                response,
                new_content="{} There were unicode problems, sorry!".format(_EMOJI["error"])
            )
            return
        # We finally have a song to queue!
        song = results[choice_index]
        # Load it up...
        voice = uita.state.voice_connections[message.server.id]
        user = uita.types.DiscordUser(
            message.author.id, message.author.name, None, message.server.id
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
            value="Live" if song["is_live"] else "{:0>2}:{:0>2}:{:0>2}".format(
                int(song["duration"] / (60 * 60)),
                int((song["duration"] / 60) % 60),
                int(song["duration"] % 60)
            ),
            inline=True
        )
        # Finally display the enqueued song to the user
        await uita.bot.edit_message(
            response,
            new_content="{} Enqueued".format(_EMOJI["ok"]),
            embed=song_info
        )
    except uita.exceptions.ClientError as error:
        if error.message.header == uita.message.ErrorQueueFullMessage.header:
            await uita.bot.edit_message(
                response,
                new_content="{} Queue is full, sorry!".format(_EMOJI["error"])
            )
        elif error.message.header == uita.message.ErrorUrlInvalidMessage.header:
            await uita.bot.edit_message(
                response,
                new_content="{} That URL was no good, sorry!".format(_EMOJI["error"])
            )
        else:
            await uita.bot.edit_message(
                response,
                new_content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
            )
            log.warn("Uncaught exception in play {}".format(error.message.header))
    except Exception:
        await uita.bot.edit_message(
            response,
            new_content="{} Not feeling up to it, sorry!".format(_EMOJI["error"])
        )
        raise


@command("join", "j", help="Joins your voice channel")
async def join(message, params):
    channel = message.author.voice.voice_channel
    if channel is not None:
        voice = uita.state.voice_connections[message.server.id]
        await voice.connect(channel.id)
    else:
        await uita.bot.send_message(
            message.channel,
            content="{} You aren't in a voice channel (that I can see)".format(_EMOJI["error"])
        )


@command("leave", "l", help="Leaves the voice channel")
async def leave(message, params):
    voice = uita.state.voice_connections[message.server.id]
    await voice.disconnect()
