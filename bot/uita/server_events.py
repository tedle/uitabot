"""Event triggers for web client to."""
import asyncio
import os
import uuid

import uita
import uita.message
import uita.types
import uita.utils
from uita.ui_server import Event


@uita.server.on_message(uita.message.ChannelActiveGetMessage)
async def channel_active_get(event: Event[uita.message.ChannelActiveGetMessage]) -> None:
    """Get the actively connected voice channel for a current server."""
    # mypy doesn't (can't?) recognize that event.active_server is always safe to access when
    # @on_message(require_active_server=True)
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await event.socket.send(str(uita.message.ChannelActiveSendMessage(voice.active_channel)))


@uita.server.on_message(uita.message.ChannelJoinMessage)
async def channel_join(event: Event[uita.message.ChannelJoinMessage]) -> None:
    """Connect the bot to a given channel of the active server."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.connect(event.message.channel_id)


@uita.server.on_message(uita.message.ChannelLeaveMessage)
async def channel_leave(event: Event[uita.message.ChannelLeaveMessage]) -> None:
    """Disconnect the bot from the voice channel of the active server."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.disconnect()


@uita.server.on_message(uita.message.ChannelListGetMessage)
async def channel_list_get(event: Event[uita.message.ChannelListGetMessage]) -> None:
    """Provide a list of available voice channels to client."""
    assert event.active_server is not None
    discord_channels = [
        channel for channel in event.active_server.channels.values()
    ]
    await event.socket.send(str(uita.message.ChannelListSendMessage(discord_channels)))


@uita.server.on_message(uita.message.FileUploadStartMessage, block=True)
async def file_upload_start(event: Event[uita.message.FileUploadStartMessage]) -> None:
    """Uploads a file to be queued."""
    assert event.active_server is not None
    # Check for queue space
    voice = uita.state.voice_connections[event.active_server.id]
    if voice.queue_full():
        raise uita.exceptions.ClientError(uita.message.ErrorQueueFullMessage())
    # Sanitization
    file_size = event.message.size
    file_path = os.path.join(uita.utils.cache_dir(), uuid.uuid4().hex)
    if file_size > event.config.file.upload_max_size:
        raise uita.exceptions.ClientError(
            uita.message.ErrorFileInvalidMessage("Uploaded file exceeds maximum size")
        )
    dir_size = await uita.utils.dir_size(uita.utils.cache_dir(), loop=event.loop)
    if dir_size + file_size > event.config.file.cache_max_size:
        raise uita.exceptions.ClientError(
            uita.message.ErrorFileInvalidMessage("Playback cache has exceeded capacity")
        )
    # Loop socket reads until file is complete
    with uita.utils.prune_cache_guard(file_path):
        with open(file_path, "wb") as f:
            # Pre-allocate full filesize so other upload tasks get valid dir_size results
            f.seek(file_size-1)
            f.write(b"\0")
            f.flush()
            os.fsync(f.fileno())
            f.seek(0)
            # Data receiving loop
            bytes_read = 0
            while bytes_read < file_size:
                # Return the original message to signal next file slice
                await event.socket.send(str(event.message))
                data = await asyncio.wait_for(event.socket.recv(), 30, loop=event.loop)
                if isinstance(data, str):
                    raise uita.exceptions.MalformedFile("Non-binary data transferred unexpectedly")
                f.write(data)
                bytes_read += len(data)
        # Double check client isn't trying to pull a fast one on us
        if bytes_read > event.config.file.upload_max_size:
            os.remove(file_path)
            raise uita.exceptions.MalformedFile("Uploaded file exceeds maximum size")
        # Enqueue uploaded file
        try:
            await voice.enqueue_file(file_path, event.user)
        except Exception:
            os.remove(file_path)
            raise
        # Signal the successful file upload
        await event.socket.send(str(uita.message.FileUploadCompleteMessage()))


@uita.server.on_message(uita.message.ServerJoinMessage, require_active_server=False)
async def server_join(event: Event[uita.message.ServerJoinMessage]) -> None:
    """Connect a user to the web client interface for a given Discord server."""
    # Check that user has access to this server
    if (
        event.message.server_id in uita.state.servers and
        event.user.id in uita.state.servers[event.message.server_id].users
    ):
        event.user.active_server_id = event.message.server_id
    else:
        event.user.active_server_id = None
        await event.socket.send(str(uita.message.ServerKickMessage()))


@uita.server.on_message(uita.message.ServerListGetMessage, require_active_server=False)
async def server_list_get(event: Event[uita.message.ServerListGetMessage]) -> None:
    """Provide a list of all servers that the user and uitabot share membership in."""
    discord_servers = [
        uita.types.DiscordServer(
            discord_server.id, discord_server.name, {}, {}, discord_server.icon
        )
        for key, discord_server in uita.state.servers.items()
        if event.user.id in discord_server.users
    ]
    await event.socket.send(str(uita.message.ServerListSendMessage(discord_servers)))


@uita.server.on_message(uita.message.PlayQueueGetMessage)
async def play_queue_get(event: Event[uita.message.PlayQueueGetMessage]) -> None:
    """Requests the queued playlist for the active server."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await event.socket.send(str(uita.message.PlayQueueSendMessage(voice.queue())))


@uita.server.on_message(uita.message.PlayQueueMoveMessage)
async def play_queue_move(event: Event[uita.message.PlayQueueMoveMessage]) -> None:
    """Moves the supplied track to a new position in the play queue."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.move(event.message.id, event.message.position)


@uita.server.on_message(uita.message.PlayQueueRemoveMessage)
async def play_queue_remove(event: Event[uita.message.PlayQueueRemoveMessage]) -> None:
    """Removes the supplied track from the play queue."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.remove(event.message.id)


@uita.server.on_message(uita.message.PlayStatusGetMessage)
async def play_status_get(event: Event[uita.message.PlayStatusGetMessage]) -> None:
    """Requests the current playback status from the active server."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await event.socket.send(str(uita.message.PlayStatusSendMessage(voice.status())))


@uita.server.on_message(uita.message.PlayURLMessage)
async def play_url(event: Event[uita.message.PlayURLMessage]) -> None:
    """Queues the audio from a given URL."""
    assert event.active_server is not None
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.enqueue_url(event.message.url, event.user)
