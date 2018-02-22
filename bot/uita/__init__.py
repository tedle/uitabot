"""Music bot for Discord that can be controlled via websockets"""

__version__ = "0.0.1"
__author__ = "Dominic Bowden"
__copyright__ = "2018, Dominic Bowden"
__license__ = "ISC"

from discord import Client
from uita.ui_server import Server
import asyncio

loop = asyncio.get_event_loop()
bot = Client(loop=loop)
server = Server()

import uita.bot_events, uita.server_events  # noqa: E401,E402,F401
