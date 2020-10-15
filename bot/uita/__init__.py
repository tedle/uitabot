"""Music bot for Discord that can be controlled via websockets"""

__version__ = "1.1.1"
__author__ = "Dominic Bowden"
__copyright__ = "2018, Dominic Bowden"
__license__ = "ISC"
__url__ = "https://github.com/tedle/uitabot"

from discord import Client, Intents
from uita.ui_server import Server
from uita.types import DiscordState
import asyncio

# Use a bunch of globals because of decorator class methods
loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
bot: Client = Client(
    loop=loop,
    intents=Intents(
        guilds=True,          # List which guilds bot is in
        members=True,         # Web UI verification of user permissions
        voice_states=True,    # Auto-pause when voice channel is empty
        guild_messages=True,  # Chat commands
        guild_reactions=True  # Chat command UI
    )
)
server: Server = Server()
state: DiscordState = DiscordState()

# Initialize bot and server decorators
import uita.bot_events, uita.server_events  # noqa: E401,E402,F401
