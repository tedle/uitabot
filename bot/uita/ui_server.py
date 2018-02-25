"""Manages connections from UI frontend."""

import asyncio
import ssl
import websockets
from collections import namedtuple

import uita.auth
import uita.exceptions
import uita.message
import uita

import logging
log = logging.getLogger(__name__)


Connection = namedtuple("Connection", ["user", "socket"])
"""Container for Server connections.

Parameters
----------
user : uita.types.DiscordUser
    User connected to server.
socket : websockets.WebSocketCommonProtocol
    Websocket connected to user.

Attributes
----------
user : uita.types.DiscordUser
    User connected to server.
socket : websockets.WebSocketCommonProtocol
    Websocket connected to user.

"""


Event = namedtuple("Event", ["message", "user", "socket", "active_server"])
"""Container for Server event callbacks.

Parameters
----------
message : uita.message.AbstractMessage
    Message that triggered event.
user : uita.types.DiscordUser
    User that triggered event.
socket : websockets.WebSocketProtocol
    Connection that triggered event.
active_server : uita.types.DiscordServer
    Server that user is active in. None if not yet selected.

Attributes
----------
message : uita.message.AbstractMessage
    Message that triggered event.
user : uita.types.DiscordUser
    User that triggered event.
socket : websockets.WebSocketProtocol
    Connection that triggered event.
active_server : uita.types.DiscordServer
    Server that user is active in. None if not yet selected.

"""


class Server():
    """Manages connections from UI frontend.

    Requires asynchronous programming, loop management expected from user.

    Attributes
    ----------
    database : uita.database.Database
        Database containing user authentication data.
    loop : asyncio.AbstractEventLoop
        Event loop that listen server will attach to.

    """
    def __init__(self):
        self._server = None
        self._event_callbacks = {}
        self._active_events = set()
        self.connections = {}

    async def start(self, database, config, origins=None, loop=None):
        """Creates a new listen server.

        Accepts connections from UI frontend.

        Parameters
        ----------
        database : uita.database.Database
            Contains user authentication data.
        config : uita.config.Config
            Configuration options containing API keys.
        origins : str, optional
            Refuses connections from clients with origin HTTP headers that do not match given
            value.
        loop : asyncio.AbstractEventLoop, optional
            Event loop to attach listen server to, defaults to ``asyncio.get_event_loop()``.

        Raises
        ------
        uita.exceptions.ServerError
            If called while the server is already running.

        """
        if self._server is not None:
            raise uita.exceptions.ServerError("Server.start() called while already running")
        self.database = database
        self.config = config
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        ssl_context = None
        # Don't need to check ssl_key_file
        # If it is None load_cert_chain will attempt to find it in the cert file
        if config.ssl.cert_file is not None:
            ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(config.ssl.cert_file, config.ssl.key_file)
        self._server = await websockets.serve(
            self._on_connect, host=config.bot.domain, port=config.bot.port,
            loop=self.loop, origins=origins, ssl=ssl_context
        )
        log.info("Server listening on ws{}://{}:{}".format(
            "s" if ssl_context is not None else "",
            config.bot.domain, config.bot.port
        ))

    async def stop(self):
        """Closes all active connections and destroys listen server.

        Raises
        ------
        uita.exceptions.ServerError
            If called while the server is not running.

        """
        if self._server is None:
            raise uita.exceptions.ServerError("Server.stop() called while not running")
        await self._cancel_active_events()
        self._server.close()
        await self._server.wait_closed()
        self._server = None
        self.database = None
        self.loop = None
        self.connections.clear()
        log.info("Server closed successfully")

    def on_message(self, header, require_active_server=True):
        """Decorator to bind event callbacks.

        Callback function should accept a `uita.ui_server.Event` as its only parameter

        Parameters
        ----------
        header : str
            `uita.message.AbstractMessage` header to wait for.
        require_active_server : bool, optional
            Verify that `event.active_server` is valid, default `True`

        Raises
        ------
        uita.exceptions.NoActiveServer
            If `require_active_server` was set to `True` and callback is
            sent an `event.active_server` of `None`.

        """
        def decorator(function):
            async def wrapper(event):
                if require_active_server is True and event.active_server is None:
                    raise uita.exceptions.NoActiveServer
                return await function(event)
            self._event_callbacks[header] = wrapper
            return wrapper
        return decorator

    async def send_all(self, message, server_id):
        """Sends a `uita.message.AbstractMessage` to all `uita.types.DiscordUser` in a server.

        Parameters
        ----------
        user : uita.types.DiscordUser
            Connected user to send message to.
        message : uita.message.AbstractMessage
            Message to send to user.
        server_id : str
            Discord server ID to broadcast to.

        """
        await asyncio.wait([
            socket.send(str(message))
            for socket, conn in self.connections.items()
            if conn.user.active_server_id == server_id
        ], loop=self.loop)

    async def _authenticate(self, websocket):
        try:
            data = await asyncio.wait_for(websocket.recv(), timeout=5, loop=self.loop)
        except asyncio.TimeoutError:
            raise uita.exceptions.AuthenticationError("Authentication timed out")
        message = uita.message.parse(data)
        if isinstance(message, uita.message.AuthSessionMessage):
            return await uita.auth.verify_session(
                uita.auth.Session(handle=message.handle, secret=message.secret),
                self.database,
                self.config,
                self.loop
            )
        elif isinstance(message, uita.message.AuthCodeMessage):
            session = await uita.auth.verify_code(
                message.code, self.database, self.config, self.loop
            )
            return await uita.auth.verify_session(
                session, self.database, self.config, self.loop
            )
        else:
            raise uita.exceptions.AuthenticationError("Expected auth.session message")

    async def _cancel_active_events(self):
        tasks = asyncio.gather(*self._active_events, loop=self.loop)
        tasks.cancel()
        await tasks

    def _dispatch_event(self, event):
        if event.message.header in self._event_callbacks:
            async def wrapper():
                try:
                    await self._event_callbacks[event.message.header](event)
                except asyncio.CancelledError:
                    pass
                except Exception:
                    log.warning("Uncaught exception in event", exc_info=True)
                    await event.socket.close(
                        code=1001,
                        reason="Event callback caused exception"
                    )
            task = self.loop.create_task(wrapper())
            task.add_done_callback(lambda f: self._active_events.remove(f))
            self._active_events.add(task)

    async def _on_connect(self, websocket, path):
        log.debug("Websocket connected {} {}".format(websocket.remote_address[0], path))
        try:
            user = None  # If authentication throws we would get an UnboundLocalError otherwise
            user = await self._authenticate(websocket)
            conn = Connection(user, websocket)
            self.connections[websocket] = conn
            await websocket.send(str(uita.message.AuthSucceedMessage(user)))
            log.info("{}({}) connected".format(user.name, websocket.remote_address[0]))
            while True:
                data = await asyncio.wait_for(websocket.recv(), 90, loop=self.loop)
                message = uita.message.parse(data)
                active_server = uita.state.servers.get(user.active_server_id)
                self._dispatch_event(Event(message, user, websocket, active_server))
        except websockets.exceptions.ConnectionClosed as error:
            log.debug("Websocket disconnected: code {},reason {}".format(error.code, error.reason))
        except asyncio.CancelledError:
            log.debug("Websocket cancelled")
        except asyncio.TimeoutError:
            log.debug("Websocket missed heartbeat")
        except uita.exceptions.AuthenticationError as error:
            log.debug("Websocket failed to authenticate: {}".format(error))
            try:
                await asyncio.wait_for(
                    websocket.send(str(uita.message.AuthFailMessage())),
                    timeout=5,
                    loop=self.loop
                )
            except (
                asyncio.TimeoutError,
                asyncio.CancelledError,
                websockets.exceptions.ConnectionClosed
            ):
                pass
        except uita.exceptions.MalformedMessage as error:
            log.debug("Websocket sent malformed message: {}".format(error))
        except Exception:
            log.warning("Uncaught exception", exc_info=True)
        finally:
            if user is not None:
                del self.connections[websocket]
                log.info("{} disconnected".format(user.name))
            await websocket.close()
            log.debug("Websocket closed")
