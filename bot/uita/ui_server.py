"""Manages connections from UI frontend."""

import asyncio
import ssl
import websockets
from collections import namedtuple

import uita.auth
import uita.database
import uita.exceptions
import uita.message
import uita

import logging
log = logging.getLogger(__name__)


class Connection():
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
    def __init__(self, user, socket):
        self.user = user
        self.socket = socket


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

    async def start(self, database_uri, config, origins=None, loop=None):
        """Creates a new listen server.

        Accepts connections from UI frontend.

        Parameters
        ----------
        database_uri : str
            URI to database containing user authentication data.
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
        self.database = uita.database.Database(database_uri)
        self.config = config
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        # Setup an endless database maintenance task to run every 10 minutes
        async def database_maintenance():
            while True:
                self.database.maintenance()
                await asyncio.sleep(600, loop=self.loop)
        self._create_task(database_maintenance())

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
        # Cancel active events first so they can access server internals before they are reset
        await self._cancel_active_events()
        self._server.close()
        await self._server.wait_closed()
        # Close all active connections
        for conn in self.connections:
            await conn.close()
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

    async def verify_active_servers(self):
        """Checks if any user is connected to an active server that is no longer accessible.

        If so, will force them back to the server select screen.

        """
        # Might help to have an individual user check, but since connections aren't stored in a
        # hash table (and the server lookups they need are), it probably wouldn't be much faster
        # without reworking how data is stored. Also I don't expect many simultaneous active
        # connections. So optimize this if it ever gets to be slow, but I don't think it will.
        for socket, conn in self.connections.items():
            if conn.user.active_server_id is None:
                continue
            if (
                conn.user.active_server_id not in uita.state.servers
                or conn.user.id not in uita.state.servers[conn.user.active_server_id].users
            ):
                conn.user.active_server_id = None
                self._create_task(
                    socket.send(str(uita.message.ServerKickMessage()))
                )

    async def _authenticate(self, websocket):
        """Hardcoded authentication handshake with web client."""
        # Start by waiting for a data with either session info or an auth code for the Discord API
        try:
            data = await asyncio.wait_for(websocket.recv(), timeout=5, loop=self.loop)
        # If it takes more than 5 seconds, kick them out
        except asyncio.TimeoutError:
            raise uita.exceptions.AuthenticationError("Authentication timed out")
        message = uita.message.parse(data)
        # Authenticating by session data
        if isinstance(message, uita.message.AuthSessionMessage):
            return await uita.auth.verify_session(
                uita.auth.Session(handle=message.handle, secret=message.secret),
                self.database,
                self.config,
                self.loop
            )
        # Authenticating by authorization code
        elif isinstance(message, uita.message.AuthCodeMessage):
            session = await uita.auth.verify_code(
                message.code, self.database, self.config, self.loop
            )
            return await uita.auth.verify_session(
                session, self.database, self.config, self.loop
            )
        # Unexpected data (port scanners, etc)
        else:
            raise uita.exceptions.AuthenticationError("Expected authentication message")

    async def _cancel_active_events(self):
        """Cancels all events spawned by the UI server."""
        tasks = asyncio.gather(*self._active_events, loop=self.loop, return_exceptions=True)
        tasks.cancel()
        await tasks

    def _create_task(self, coroutine):
        """Creates a managed task that will be tracked and cancelled on server shutdown."""
        task = self.loop.create_task(coroutine)
        task.add_done_callback(lambda f: self._active_events.remove(f))
        self._active_events.add(task)

    def _dispatch_event(self, event):
        """Finds and calls aproppriate callback for given event message.

        If an event raises an exception it is logged and the connection is closed.

        """
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
            self._create_task(wrapper())

    async def _on_connect(self, websocket, path):
        """Main loop for each connected client."""
        log.debug("Websocket connected {} {}".format(websocket.remote_address[0], path))
        try:
            # Connection stub in case server stops during authentication
            conn = Connection(None, websocket)
            self.connections[websocket] = conn
            # Initialize user and connection data
            user = await self._authenticate(websocket)
            conn.user = user
            # Notify client that they authenticated successfully
            await websocket.send(str(uita.message.AuthSucceedMessage(user)))
            log.info("{}({}) connected".format(user.name, websocket.remote_address[0]))
            # Main loop, runs for the life of each connection
            while True:
                # 90 second timeout to cull zombie connections, expects client heartbeats
                data = await asyncio.wait_for(websocket.recv(), 90, loop=self.loop)
                # Parse data into message and dispatch to aproppriate event callback
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
                # Notify client that their authentication failed before closing connection
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
            # Close and cleanup connection
            if conn.user is not None:
                del self.connections[websocket]
                log.info("{} disconnected".format(conn.user.name))
            await websocket.close()
            log.debug("Websocket closed")
