"""Music bot for Discord that can be controlled via websockets"""

__version__ = "0.0.1"
__author__ = "Dominic Bowden"
__copyright__ = "2018, Dominic Bowden"
__license__ = "ISC"

from uita.ui_server import Server

server = Server()

import uita.server_events  # noqa: E402,F401
