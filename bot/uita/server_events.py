"""Event triggers for web client to."""
import asyncio
import discord
import os
import uuid

import uita
import uita.message
import uita.types
import uita.utils

import logging
log = logging.getLogger(__name__)


@uita.server.on_message("channel.join")
async def channel_join(event):
    """Connect the bot to a given channel of the active server."""
    log.debug("channel join {}".format(event.message.channel_id))
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.connect(uita.bot, event.message.channel_id)


@uita.server.on_message("channel.leave")
async def channel_leave(event):
    """Disconnect the bot from the voice channel of the active server."""
    log.debug("channel leave")
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.disconnect()


@uita.server.on_message("channel.list.get")
async def channel_list_get(event):
    """Provide a list of available voice channels to client."""
    log.debug("channel list get")
    discord_channels = [
        uita.types.DiscordChannel(
            discord_channel.id,
            discord_channel.name,
            discord_channel.type,
            discord_channel.position
        )
        for key, discord_channel in event.active_server.channels.items()
        if discord_channel.type is discord.ChannelType.voice
    ]
    await event.socket.send(str(uita.message.ChannelListSendMessage(discord_channels)))


@uita.server.on_message("file.upload.start", block=True)
async def file_upload_start(event):
    """Uploads a file to be queued."""
    log.debug("file upload start {}B".format(event.message.size))
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
    # Return the original message to signal binary data stream
    await event.socket.send(str(event.message))
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
                data = await asyncio.wait_for(event.socket.recv(), 5, loop=uita.loop)
                f.write(data)
                bytes_read += len(data)
        # Double check client isn't trying to pull a fast one on us
        if bytes_read > event.config.file.upload_max_size:
            os.remove(file_path)
            raise uita.exceptions.MalformedFile("Uploaded file exceeds maximum size")
        # Enqueue uploaded file
        try:
            voice = uita.state.voice_connections[event.active_server.id]
            await voice.enqueue(file_path)
            # Signal the successful file upload
            await event.socket.send(str(uita.message.FileUploadCompleteMessage()))
        except Exception:
            os.remove(file_path)
            raise


@uita.server.on_message("server.join", require_active_server=False)
async def server_join(event):
    """Connect a user to the web client interface for a given Discord server."""
    log.debug("server join {}".format(event.message.server_id))
    # Check that user has access to this server
    if event.user.id in uita.state.servers[event.message.server_id].users:
        event.user.active_server_id = event.message.server_id
    else:
        await event.socket.send(str(uita.message.ServerKickMessage()))


@uita.server.on_message("server.list.get", require_active_server=False)
async def server_list_get(event):
    """Provide a list of all servers that the user and uitabot share membership in."""
    log.debug("server list get")
    discord_servers = [
        uita.types.DiscordServer(
            discord_server.id, discord_server.name, [], []
        )
        for key, discord_server in uita.state.servers.items()
        if event.user.id in discord_server.users
    ]
    await event.socket.send(str(uita.message.ServerListSendMessage(discord_servers)))


@uita.server.on_message("play.queue.get")
async def play_queue_get(event):
    """Requests the queued playlist for the active server."""
    log.debug("play.queue.get")
    voice = uita.state.voice_connections[event.active_server.id]
    await event.socket.send(str(uita.message.PlayQueueSendMessage(voice.queue())))


@uita.server.on_message("play.queue.move")
async def play_queue_move(event):
    """Moves the supplied track to a new position in the play queue."""
    log.debug("play.queue.move {}->{}".format(event.message.id, event.message.position))
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.move(event.message.id, event.message.position)


@uita.server.on_message("play.queue.remove")
async def play_queue_remove(event):
    """Removes the supplied track from the play queue."""
    log.debug("play.queue.remove {}".format(event.message.id))
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.remove(event.message.id)


@uita.server.on_message("play.url")
async def play_url(event):
    """Queues the audio from a given URL."""
    log.debug("play.url {}".format(event.message.url))
    voice = uita.state.voice_connections[event.active_server.id]
    await voice.enqueue(event.message.url)
