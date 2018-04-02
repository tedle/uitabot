"""Bot commands issued by Discord chat."""
import discord

import uita.types
import uita

import logging
log = logging.getLogger(__name__)


# With how generator routing works some kind of global soup was inevitable
_COMMAND_PREFIX = "."
_COMMANDS = {}
_COMMAND_HELP = []
_EMBED_COLOUR = 14721770


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
                "Unknown command. Try `{0}help` for a list of commands."
            ).format(_COMMAND_PREFIX)
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
    help_message = discord.Embed(title="Commands", color=_EMBED_COLOUR)
    for cmd in _COMMAND_HELP:
        name = ", ".join(["`{}{}`".format(_COMMAND_PREFIX, c) for c in cmd[0]])
        help_message.add_field(
            name=name,
            value=cmd[1],
            inline=False
        )
    await uita.bot.send_message(message.channel, content="", embed=help_message)
