import ssl
import websockets


class Server():
    async def on_connect(self, websocket, path):
        print("Connected")

    def serve(self, host, port, loop=None, origins=None, ssl_cert_file=None, ssl_key_file=None):
        ssl_context = None
        # Don't need to check ssl_key_file
        # If it is None load_cert_chain will attempt to find it in the cert file
        if ssl_cert_file is not None:
            ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(ssl_cert_file, ssl_key_file)
        return websockets.serve(
            self.on_connect, host=host, port=port,
            loop=loop, origins=origins, ssl=ssl_context
        )
