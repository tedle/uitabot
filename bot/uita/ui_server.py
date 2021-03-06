"""Manages connections from UI frontend."""

import asyncio
import ssl
import websockets
from typing import (
    Any, Awaitable, Callable, Coroutine, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar
)

import uita.auth
import uita.config
import uita.database
import uita.exceptions
import uita.message
import uita.utils
import uita

import logging
log = logging.getLogger(__name__)


class Connection():
    """Container for Server connections.

    Args:
        user: User connected to server. Can be ``None`` while connection is unauthenticated.
        socket: Websocket connected to user.

    Attributes:
        user (Optional[uita.types.DiscordUser]): User connected to server. Can be ``None`` while
            connection is unauthenticated.
        socket (websockets.WebSocketServerProtocol): Websocket connected to user.

    """
    def __init__(
        self,
        user: Optional[uita.types.DiscordUser],
        socket: websockets.WebSocketServerProtocol
    ) -> None:
        self.user = user
        self.socket = socket


_AbstractMessageType = TypeVar("_AbstractMessageType", bound=uita.message.AbstractMessage)


class Event(Generic[_AbstractMessageType]):
    """Container for Server event callbacks.

    Can be set to block the main connection loop from running until this event is processed. Is
    unblocking by default.

    Args:
        message (uita.message.AbstractMessage): Message that triggered event.
        user: User that triggered event.
        socket: Connection that triggered event.
        config: Configuration options.
        loop: Event loop that task is running in.
        active_server: Server that user is active in. ``None`` if not yet selected.

    Attributes:
        message (uita.message.AbstractMessage): Message that triggered event.
        user (uita.types.DiscordUser): User that triggered event.
        socket (websockets.WebSocketProtocol): Connection that triggered event.
        config (uita.config.Config): Configuration options.
        loop (asyncio.AbstractEventLoop): Event loop that task is running in.
        active_server (Optional[uita.types.DiscordServer]): Server that user is active in. ``None``
            if not yet selected.

    """
    CallbackType = Callable[["Event[Any]"], Awaitable[None]]

    def __init__(
        self,
        message: _AbstractMessageType,
        user: uita.types.DiscordUser,
        socket: websockets.WebSocketServerProtocol,
        config: uita.config.Config,
        loop: asyncio.AbstractEventLoop,
        active_server: Optional[uita.types.DiscordServer]
    ) -> None:
        self.message = message
        self.user = user
        self.socket = socket
        self.config = config
        self.loop = loop
        self.active_server = active_server
        self._block_flag = asyncio.Event()

    def block(self) -> None:
        """Blocks the main connection loop from further socket reads."""
        self._block_flag.clear()

    def finish(self) -> None:
        """Unblocks the main connection loop, allowing for further socket reads."""
        self._block_flag.set()

    async def wait(self) -> None:
        """Waits until the event is not blocked."""
        await self._block_flag.wait()


class Server():
    """Manages connections from UI frontend.

    Requires asynchronous programming, loop management expected from user.

    Attributes:
        database (Optional[uita.database.Database]): Database containing user authentication data.
            ``None`` if the server has not yet started.
        loop (Optional[asyncio.AbstractEventLoop]): Event loop that listen server will attach to.
            ``None`` if the server has not yet started.

    """
    def __init__(self) -> None:
        self._server: Optional[websockets.server.WebSocketServer] = None
        self._event_callbacks: Dict[str, Event.CallbackType] = {}
        self._active_events: Set[asyncio.Task[None]] = set()
        self.connections: Dict[websockets.WebSocketServerProtocol, Connection] = {}

    async def start(
        self,
        database_uri: str,
        config: uita.config.Config,
        origins: Optional[List[websockets.Origin]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        """Creates a new listen server.

        Accepts connections from UI frontend.

        Args:
            database_uri: URI to database containing user authentication data.
            config: Configuration options containing API keys.
            origins: Refuses connections from clients with origin HTTP headers that do not match
                given value.
            loop: Event loop to attach listen server to, defaults to ``asyncio.get_event_loop()``.

        Raises:
            uita.exceptions.ServerError: If called while the server is already running.

        """
        if self._server is not None:
            raise uita.exceptions.ServerError("Server.start() called while already running")
        self.database = uita.database.Database(database_uri)
        self.config = config
        self.loop = loop or asyncio.get_event_loop()

        # Setup an endless database maintenance task to run every 10 minutes
        async def database_maintenance() -> None:
            while True:
                self.database.maintenance()
                await asyncio.sleep(600, loop=self.loop)
        self._create_task(database_maintenance())

        # Setup an endless cache pruning task to run every minute
        async def cache_prune() -> None:
            while True:
                whitelist = []
                for _, v in uita.state.voice_connections.items():
                    for track in v.queue():
                        if track.local:
                            whitelist.append(track.path)
                await uita.utils.prune_cache_dir(whitelist=whitelist)
                await asyncio.sleep(60, loop=self.loop)
        self._create_task(cache_prune())

        ssl_context = None
        # Don't need to check ssl_key_file
        # If it is None load_cert_chain will attempt to find it in the cert file
        if config.ssl.cert_file is not None:
            ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(config.ssl.cert_file, config.ssl.key_file)
        self._server = await websockets.serve(
            self._on_connect, port=config.bot.port,
            loop=self.loop, origins=origins, ssl=ssl_context
        )
        log.info(f"Server listening on {uita.utils.build_websocket_url(self.config)}")

    async def stop(self) -> None:
        """Closes all active connections and destroys listen server."""
        if self._server is None:
            return
        # Cancel active events first so they can access server internals before they are reset
        await self._cancel_active_events()
        self._server.close()
        await self._server.wait_closed()
        # Close all active connections
        for conn in self.connections:
            await conn.close()
        self._server = None
        self.connections.clear()
        log.info("Server closed")

    def on_message(
        self,
        message_type: Type[_AbstractMessageType],
        require_active_server: bool = True,
        block: bool = False
    ) -> Callable[[Event.CallbackType], Event.CallbackType]:
        """Decorator to bind event callbacks.

        Callback function should accept a :class:`~uita.ui_server.Event` as its only parameter

        Args:
            message_type: Message type to wait for.
            require_active_server: Verify that :attr:`~uita.ui_server.Event.active_server` is
                valid, default ``True``.
            block: Block connection await loop until event callback is completed, default
                ``False``.

        Raises:
            uita.exceptions.NoActiveServer: If ``require_active_server`` was set to ``True`` and
                callback is sent an :attr:`~uita.ui_server.Event.active_server` of ``None``.

        """
        def decorator(function: Event.CallbackType) -> Event.CallbackType:
            async def wrapper(event: Event[Any]) -> None:
                if require_active_server is True and event.active_server is None:
                    raise uita.exceptions.NoActiveServer
                if block is False:
                    event.finish()
                await function(event)
            self._event_callbacks[message_type.header] = wrapper
            return wrapper
        return decorator

    def send_all(self, message: uita.message.AbstractMessage, server_id: str) -> None:
        """Sends a :class:`~uita.message.AbstractMessage` to all :class:`~uita.types.DiscordUser`
        in a server.

        Args:
            message: Message to send to user.
            server_id: Discord server ID to broadcast to.

        """
        for socket, conn in self.connections.items():
            if conn.user is not None and conn.user.active_server_id == server_id:
                async def try_send(s: websockets.WebSocketServerProtocol, m: str) -> None:
                    try:
                        await s.send(m)
                    except websockets.exceptions.ConnectionClosed:
                        pass
                    except asyncio.CancelledError:
                        pass
                self._create_task(try_send(socket, str(message)))

    async def verify_active_servers(self) -> None:
        """Checks if any user is connected to an active server that is no longer accessible.

        If so, will force them back to the server select screen.

        """
        # Might help to have an individual user check, but since connections aren't stored in a
        # hash table (and the server lookups they need are), it probably wouldn't be much faster
        # without reworking how data is stored. Also I don't expect many simultaneous active
        # connections. So optimize this if it ever gets to be slow, but I don't think it will.
        for socket, conn in self.connections.items():
            if conn.user is None:
                continue
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

    async def _authenticate(
        self,
        websocket: websockets.WebSocketServerProtocol
    ) -> Tuple[uita.types.DiscordUser, uita.auth.Session]:
        """Hardcoded authentication handshake with web client."""
        # Start by waiting for a data with either session info or an auth code for the Discord API
        try:
            data = await asyncio.wait_for(websocket.recv(), timeout=5, loop=self.loop)
            if isinstance(data, bytes):
                raise uita.exceptions.MalformedMessage("Websocket sent bytes unexpectedly")
        # If it takes more than 5 seconds, kick them out
        except asyncio.TimeoutError:
            raise uita.exceptions.AuthenticationError("Authentication timed out")
        message = uita.message.parse(data)
        # Authenticating by session data
        if isinstance(message, uita.message.AuthSessionMessage):
            session = uita.auth.Session(handle=message.handle, secret=message.secret)
            return await uita.auth.verify_session(
                session,
                self.database,
                self.config,
                self.loop
            ), session
        # Authenticating by authorization code
        elif isinstance(message, uita.message.AuthCodeMessage):
            session = await uita.auth.verify_code(
                message.code, self.database, self.config, self.loop
            )
            return await uita.auth.verify_session(
                session, self.database, self.config, self.loop
            ), session
        # Unexpected data (port scanners, etc)
        else:
            raise uita.exceptions.AuthenticationError("Expected authentication message")

    async def _cancel_active_events(self) -> None:
        """Cancels all events spawned by the UI server."""
        tasks = asyncio.gather(*self._active_events, loop=self.loop, return_exceptions=True)
        try:
            tasks.cancel()
            await tasks
        except asyncio.CancelledError:
            pass

    def _create_task(self, coroutine: Coroutine[Any, Any, None]) -> None:
        """Creates a managed task that will be tracked and cancelled on server shutdown."""
        task = self.loop.create_task(coroutine)
        task.add_done_callback(lambda f: self._active_events.remove(f))
        self._active_events.add(task)

    def _dispatch_event(self, event: Event[Any]) -> None:
        """Finds and calls aproppriate callback for given event message.

        If an event raises an exception it is logged and the connection is closed.

        """
        # Log all events except heartbeats since they happen so often and aren't very useful
        if event.message.header != "heartbeat":
            log.debug("[{}:{}] {} {} -> {}".format(
                event.user.name,
                event.user.id,
                event.message.header,
                event.message.__dict__,
                "No server" if not event.active_server else event.active_server.name
            ))
        # Process the event
        if event.message.header in self._event_callbacks:
            async def wrapper() -> None:
                try:
                    await self._event_callbacks[event.message.header](event)
                except (asyncio.CancelledError, websockets.exceptions.ConnectionClosed):
                    pass
                except uita.exceptions.ClientError as e:
                    log.debug(f"ClientError {e}")
                    await event.socket.send(str(e))
                except uita.exceptions.NoActiveServer:
                    await event.socket.send(str(uita.message.ServerKickMessage()))
                except Exception:
                    log.warning("Uncaught exception in event", exc_info=True)
                    await event.socket.close(
                        code=1001,
                        reason="Event callback caused exception"
                    )
                finally:
                    event.finish()
            self._create_task(wrapper())
        else:
            event.finish()

    async def _on_connect(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        """Main loop for each connected client."""
        log.debug(f"Websocket connected {websocket.remote_address[0]} {path}")
        try:
            # Connection stub in case server stops during authentication
            conn = Connection(None, websocket)
            self.connections[websocket] = conn
            # Initialize user and connection data
            user, session = await self._authenticate(websocket)
            conn.user = user
            # Notify client that they authenticated successfully
            await websocket.send(str(uita.message.AuthSucceedMessage(user, session)))
            log.info(f"[{user.name}:{user.id}] connected ({websocket.remote_address[0]})")
            # Main loop, runs for the life of each connection
            while True:
                # 90 second timeout to cull zombie connections, expects client heartbeats
                data = await asyncio.wait_for(websocket.recv(), 90, loop=self.loop)
                if isinstance(data, bytes):
                    raise uita.exceptions.MalformedMessage("Websocket sent bytes unexpectedly")
                # Parse data into message and dispatch to aproppriate event callback
                message = uita.message.parse(data)
                # mypy gets confused passing None to .get(), so here's a redundant ternary check
                active_server = (
                    uita.state.servers.get(user.active_server_id)
                    if user.active_server_id is not None else None
                )
                event = Event(message, user, websocket, self.config, self.loop, active_server)
                self._dispatch_event(event)
                await event.wait()
        except websockets.exceptions.ConnectionClosed as error:
            log.debug(f"Websocket disconnected: code {error.code},reason {error.reason}")
        except asyncio.CancelledError:
            log.debug("Websocket cancelled")
        except asyncio.TimeoutError:
            log.debug("Websocket missed heartbeat")
        except uita.exceptions.AuthenticationError as error:
            log.debug(f"Websocket failed to authenticate: {error}")
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
            log.debug(f"Websocket sent malformed message: {error}")
        except Exception:
            log.error("Uncaught exception", exc_info=True)
        finally:
            # Close and cleanup connection
            if conn.user is not None:
                log.info(f"[{conn.user.name}:{conn.user.id}] disconnected")
            del self.connections[websocket]
            await websocket.close()
            log.debug("Websocket closed")
