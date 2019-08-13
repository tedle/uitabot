import pytest
from unittest.mock import Mock, patch

import discord
import websockets

import uita.message
import uita.server_events
import uita.ui_server
import uita.types


async def async_stub(*args, **kwargs): ...


@pytest.fixture
def event(request, config, event_loop):
    with patch("uita.server"):
        mock_event = Mock()
        mock_event.socket.send.side_effect = async_stub
        mock_event.config = config
        mock_event.loop = event_loop
        mock_event.user = uita.types.DiscordUser(
            "2b2b2b2b2b", "User Name", "http://example.com/image.png", None
        )
        mock_event.active_server = uita.types.DiscordServer(
            "1234567890",
            "Server Name",
            {"1a1a1a1a1a":
                uita.types.DiscordChannel(
                    "1a1a1a1a1a",
                    "Channel Name",
                    discord.ChannelType.voice,
                    "1c1c1c1c1c",
                    0
                )},
            {mock_event.user.id: mock_event.user.name},
            None
        )
        state = uita.types.DiscordState()
        state.server_add(mock_event.active_server, Mock(loop=event_loop))
        with patch("uita.state", new=state):
            yield mock_event


@pytest.mark.asyncio
async def test_channel_active_get(event):
    await uita.server_events.channel_active_get(event)
    message = uita.message.parse(event.socket.send.call_args[0][0])
    assert isinstance(message, uita.message.ChannelActiveSendMessage)
    assert message.channel is None


@pytest.mark.asyncio
async def test_channel_join(event):
    channel = next(iter(event.active_server.channels.values()))
    event.message = uita.message.ChannelJoinMessage
    event.message.channel_id = channel.id
    with patch("uita.types.DiscordVoiceClient.connect") as mock_connect:
        mock_connect.side_effect = async_stub
        await uita.server_events.channel_join(event)
        assert mock_connect.call_args[0][0] == channel.id


@pytest.mark.asyncio
async def test_channel_leave(event):
    with patch("uita.types.DiscordVoiceClient.disconnect") as mock_disconnect:
        mock_disconnect.side_effect = async_stub
        await uita.server_events.channel_leave(event)
        assert mock_disconnect.call_count == 1


@pytest.mark.asyncio
async def test_channel_list_get(event):
    channels = list(event.active_server.channels.values())
    await uita.server_events.channel_list_get(event)
    assert str(uita.message.ChannelListSendMessage(channels)) == event.socket.send.call_args[0][0]


@pytest.mark.asyncio
async def test_file_upload_start(event, data_dir):
    with open(data_dir / "test.flac", "rb") as f:
        file_data = f.read()

    # Runs the client logic of a file upload
    async def send_file(socket, _):
        start_message = uita.message.parse(await socket.recv())
        # These assertions can't actually propogate because websockets suppresses them
        assert isinstance(start_message, uita.message.FileUploadStartMessage)
        assert start_message.size == len(file_data)

        await socket.send(file_data)

        end_message = uita.message.parse(await socket.recv())
        assert isinstance(end_message, uita.message.FileUploadCompleteMessage)
    server = await websockets.serve(
        send_file, event.config.bot.domain, event.config.bot.port, loop=event.loop
    )

    # Receive the file
    mock_enqueue = Mock()
    mock_enqueue.side_effect = async_stub
    uita.state.voice_connections[event.active_server.id].enqueue_file = mock_enqueue
    async with websockets.connect(uita.utils.build_websocket_url(event.config)) as client_socket:
        event.message = uita.message.FileUploadStartMessage(len(file_data))
        event.socket = client_socket
        await uita.server_events.file_upload_start(event)

    # Check the uploaded file matches the source file
    uploaded_file = mock_enqueue.call_args[0][0]
    with open(uploaded_file, "rb") as f:
        uploaded_file_data = f.read()
    assert file_data == uploaded_file_data

    # Clean up
    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_server_join(event):
    event.message = uita.message.ServerJoinMessage(event.active_server.id)
    assert event.user.active_server_id is None

    # Check that join works
    await uita.server_events.server_join(event)
    assert event.user.active_server_id == event.active_server.id

    # Check that join kicks users without access
    uita.state.server_remove_user(event.active_server.id, event.user.id)
    await uita.server_events.server_join(event)
    assert isinstance(
        uita.message.parse(event.socket.send.call_args[0][0]),
        uita.message.ServerKickMessage
    )


@pytest.mark.asyncio
async def test_server_list_get(event):
    servers = [event.active_server]
    await uita.server_events.server_list_get(event)
    assert str(uita.message.ServerListSendMessage(servers)) == event.socket.send.call_args[0][0]


@pytest.mark.asyncio
async def test_play_queue_get(event):
    await uita.server_events.play_queue_get(event)
    message = uita.message.parse(event.socket.send.call_args[0][0])
    assert isinstance(message, uita.message.PlayQueueSendMessage)
    assert message.queue == []

    tracks = [uita.audio.Track("path", event.user, "title", 5, False, False)]
    queue_mock = Mock(return_value=tracks)
    uita.state.voice_connections[event.active_server.id].queue = queue_mock
    await uita.server_events.play_queue_get(event)
    assert str(uita.message.PlayQueueSendMessage(tracks)) == event.socket.send.call_args[0][0]


@pytest.mark.asyncio
async def test_play_queue_move(event):
    id, position = "1234567890", 0
    event.message = uita.message.PlayQueueMoveMessage(id, position)
    move_mock = Mock(side_effect=async_stub)
    uita.state.voice_connections[event.active_server.id].move = move_mock
    await uita.server_events.play_queue_move(event)
    assert id, position == move_mock.call_args[0]


@pytest.mark.asyncio
async def test_play_queue_remove(event):
    id = "1234567890"
    event.message = uita.message.PlayQueueRemoveMessage(id)
    remove_mock = Mock(side_effect=async_stub)
    uita.state.voice_connections[event.active_server.id].remove = remove_mock
    await uita.server_events.play_queue_remove(event)
    assert id == remove_mock.call_args[0][0]


@pytest.mark.asyncio
async def test_play_status_get(event):
    status = uita.audio.Status.PLAYING
    status_mock = Mock(return_value=status)
    uita.state.voice_connections[event.active_server.id].status = status_mock
    await uita.server_events.play_status_get(event)
    message = uita.message.PlayStatusSendMessage(status)
    assert str(message) == event.socket.send.call_args[0][0]


@pytest.mark.asyncio
async def test_play_url(event):
    url = "http://example.com/"
    event.message = uita.message.PlayURLMessage(url)
    enqueue_url_mock = Mock(side_effect=async_stub)
    uita.state.voice_connections[event.active_server.id].enqueue_url = enqueue_url_mock
    await uita.server_events.play_url(event)
    assert url, event.user == enqueue_url_mock.call_args[0]
