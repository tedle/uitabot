"""Manages connections from UI frontend."""

import asyncio
import ssl
import websockets

import uita.auth
import uita.exceptions
import uita.message

import logging
log = logging.getLogger(__name__)


class Server():
    """Manages connections from UI frontend.

    Requires asynchronous programming, loop management expected from user.

    Parameters
    ----------
    database : uita.database.Database
        Contains user authentication data.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach listen server to, defaults to `asyncio.get_event_loop()`.

    Attributes
    ----------
    database : uita.database.Database
        Database containing user authentication data.
    loop : asyncio.AbstractEventLoop
        Event loop that listen server will attach to.

    """
    def __init__(self, database, loop=None):
        self.database = database
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self._server = None

    async def close(self):
        """Closes all active connections and destroys listen server.

        Raises
        ------
        uita.exceptions.ServerError
            If called while the server is not running.

        """
        if self._server is None:
            raise uita.exceptions.ServerError("Server.close() called while not running")
        self._server.close()
        await self._server.wait_closed()
        self._server = None
        log.info("Server closed successfully")

    async def serve(self, host, port, origins=None, ssl_cert_file=None, ssl_key_file=None):
        """Creates a new listen server.

        Accepts connections from UI frontend.

        Parameters
        ----------
        host : str
            Host to bind server to.
        port : int
            Port to bind server to.
        origins : str, optional
            Refuses connections from clients with origin HTTP headers that do not match given
            value.
        ssl_cert_file : str, optional
            Filename of SSL cert chain to load, if not provided will create unencrypted
            connections.
        ssl_key_file : str, optional
            Filename of SSL keyfile to load.

        Raises
        ------
        uita.exceptions.ServerError
            If called while the server is already running.

        """
        if self._server is not None:
            raise uita.exceptions.ServerError("Server.serve() called while already running")
        ssl_context = None
        # Don't need to check ssl_key_file
        # If it is None load_cert_chain will attempt to find it in the cert file
        if ssl_cert_file is not None:
            ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(ssl_cert_file, ssl_key_file)
        self._server = await websockets.serve(
            self._on_connect, host=host, port=port,
            loop=self.loop, origins=origins, ssl=ssl_context
        )
        log.info("Server listening on ws{}://{}:{}".format(
            "s" if ssl_context is not None else "",
            host, port
        ))

    async def _authenticate(self, websocket):
        try:
            data = await asyncio.wait_for(websocket.recv(), timeout=5)
        except asyncio.TimeoutError:
            raise uita.exceptions.AuthenticationError("Authentication timed out")
        message = uita.message.parse(data)
        if isinstance(message, uita.message.AuthSessionMessage):
            return uita.auth.verify_session(
                uita.auth.Session(message.session, message.name),
                self.database
            )
        elif isinstance(message, uita.message.AuthCodeMessage):
            session = uita.auth.verify_code(message.code, self.database)
            return uita.auth.verify_session(session, self.database)
        else:
            raise uita.exceptions.AuthenticationError("Expected auth.session message")

    async def _on_connect(self, websocket, path):
        log.debug("Websocket connected {} {}".format(websocket.remote_address[0], path))
        try:
            user = await self._authenticate(websocket)
            await websocket.send(str(uita.message.AuthSucceedMessage(user)))
            log.info("{} connected".format(user.name))
            while True:
                await websocket.recv()
        except websockets.exceptions.ConnectionClosed as err:
            log.debug("Websocket disconnected: code {},reason {}".format(err.code, err.reason))
        except asyncio.CancelledError:
            log.debug("Websocket cancelled")
        except uita.exceptions.AuthenticationError:
            log.debug("Websocket failed to authenticate")
            try:
                await asyncio.wait_for(websocket.send(
                    str(uita.message.AuthFailMessage())),
                    timeout=5
                )
            except (
                asyncio.TimeoutError,
                asyncio.CancelledError,
                websockets.exceptions.ConnectionClosed
            ):
                pass
        finally:
            await websocket.close()
            log.debug("Websocket closed")
