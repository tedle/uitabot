import asyncio
import ssl
import websockets


class Server():
    def __init__(self, loop=None):
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self._server = None

    async def close(self):
        if self._server is None:
            raise RuntimeError("Server.close() called while not running")
        self._server.close()
        await self._server.wait_closed()
        self._server = None

    async def serve(self, host, port, origins=None, ssl_cert_file=None, ssl_key_file=None):
        if self._server is not None:
            raise RuntimeError("Server.serve() called while already running")
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

    async def _on_connect(self, websocket, path):
        print("websocket connected")
        while True:
            try:
                await websocket.recv()
            except websockets.exceptions.ConnectionClosed as err:
                print("websocket lost: {},{}".format(err.code, err.reason))
                return
            except asyncio.CancelledError:
                print("websocket cancelled")
                return
            finally:
                await websocket.close()
                print("websocket closed")
