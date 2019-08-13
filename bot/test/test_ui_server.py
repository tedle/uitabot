import pytest
from unittest.mock import Mock, patch

import json
import websockets

import uita.message
import uita.ui_server


async def authenticate(socket, user=None, session=None):
    if user is None:
        user = uita.types.DiscordUser(
            "1234567890",
            "User name",
            "http://example.com/image.png",
            None
        )
    if session is None:
        session = uita.auth.Session(handle="123", secret="abc")
    with patch("uita.auth.verify_session") as mock_verify:
        async def return_user(*args, **kwargs):
            return user
        mock_verify.side_effect = return_user
        message = uita.message.AuthSessionMessage(session.handle, session.secret)
        await socket.send(str(message))
        message = json.loads(await socket.recv())

        return user, session, message


@pytest.fixture
@pytest.mark.asyncio
async def connection(config, event_loop):
    server = uita.ui_server.Server()
    url = uita.utils.build_websocket_url(config)
    await server.start(config.bot.database, config, loop=event_loop)

    async with websockets.connect(url, loop=event_loop) as socket:
        user, _, _ = await authenticate(socket)
        yield socket, user, server

    await server.stop()


@pytest.mark.asyncio
async def test_start_stop(config, event_loop):
    server = uita.ui_server.Server()
    url = uita.utils.build_websocket_url(config)
    await server.start(config.bot.database, config, loop=event_loop)

    async with websockets.connect(url, loop=event_loop) as socket:
        assert socket.open is True
        await server.stop()
        assert socket.closed is True


@pytest.mark.asyncio
async def test_auth(config, event_loop):
    server = uita.ui_server.Server()
    url = uita.utils.build_websocket_url(config)
    user = uita.types.DiscordUser("1234567890", "User name", "http://example.com/image.png", None)
    session = uita.auth.Session(handle="123", secret="abc")
    await server.start(config.bot.database, config, loop=event_loop)

    async with websockets.connect(url, loop=event_loop) as socket:
        _, _, message = await authenticate(socket, user=user, session=session)

    assert message["header"] == uita.message.AuthSucceedMessage.header
    assert message["user"]["id"] == user.id
    assert message["session"]["secret"] == session.secret

    await server.stop()


@pytest.mark.asyncio
async def test_on_message(connection, event_loop):
    socket, user, server = connection

    @server.on_message(uita.message.ServerListGetMessage, require_active_server=False)
    async def test_message(event):
        await event.socket.send("good")

    await socket.send(str(uita.message.ServerListGetMessage()))
    assert await socket.recv() == "good"


@pytest.mark.asyncio
async def test_send_all(connection):
    socket, user, server = connection

    user.active_server_id = "123"

    server.send_all(uita.message.ServerKickMessage(), "ABC")
    server.send_all(uita.message.HeartbeatMessage(), "123")
    message = uita.message.parse(await socket.recv())

    assert isinstance(message, uita.message.HeartbeatMessage)


@pytest.mark.asyncio
async def test_verify_active_servers(connection, event_loop):
    socket, user, server = connection

    with patch("uita.server", new=server):
        discord_server = uita.types.DiscordServer("1234567890", "Server Name", {}, {}, None)
    uita.state.server_add(discord_server, Mock(loop=event_loop))

    # Use a server ID that doesn't exist
    user.active_server_id = "fakeid"
    await server.verify_active_servers()
    assert user.active_server_id is None
    assert isinstance(uita.message.parse(await socket.recv()), uita.message.ServerKickMessage)

    # Use a server that exists but does not have the user as a member
    user.active_server_id = discord_server.id
    await server.verify_active_servers()
    assert user.active_server_id is None
    assert isinstance(uita.message.parse(await socket.recv()), uita.message.ServerKickMessage)

    # Use a server that has the user as a member
    user.active_server_id = discord_server.id
    uita.state.server_add_user(discord_server.id, user.id, user.name)
    await server.verify_active_servers()
    server.send_all(uita.message.HeartbeatMessage(), discord_server.id)
    assert user.active_server_id == discord_server.id
    assert isinstance(uita.message.parse(await socket.recv()), uita.message.HeartbeatMessage)
