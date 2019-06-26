"""Defines various container and running state types for the Discord API."""
import asyncio

import uita.audio

import logging
log = logging.getLogger(__name__)


class DiscordState():
    """Container for active Discord data.

    Attributes
    ----------
    servers : dict(uita.types.DiscordServer)
        Dict of servers bot is connected to indexed by server ID.
    voice_connections : dict(uita.types.DiscordVoiceClient)
        Dict of voice channels bot is connected to indexed by server ID.

    """
    def __init__(self):
        self.servers = {}
        self.voice_connections = {}

    def __str__(self):
        dump_str = "DiscordState() {}:\n".format(hash(self))
        for key, server in self.servers.items():
            dump_str += "server {}: {}\n".format(server.id, server.name)
            for key, channel in server.channels.items():
                dump_str += "\tchannel {}: {}\n".format(channel.id, channel.name)
            for user_id, user_name in server.users.items():
                dump_str += "\tuser {}: {}\n".format(user_id, user_name)
        return dump_str

    def initialize_from_bot(self, bot):
        """Initialize Discord state from a `discord.Client`

        Parameters
        ----------
        bot : discord.Client
            Bot containing initial Discord state to copy.

        """
        log.info("Bot state synced to Discord")
        for server in bot.servers:
            discord_channels = {
                channel.id: DiscordChannel(
                    channel.id, channel.name, channel.type, channel.position
                )
                for channel in server.channels
            }
            discord_users = {user.id: user.name for user in server.members}
            self.servers[server.id] = DiscordServer(
                server.id, server.name, discord_channels, discord_users, server.icon
            )
            self.voice_connections[server.id] = DiscordVoiceClient(server.id, bot.loop)

    def channel_add(self, channel, server_id):
        """Add a server channel to Discord state.

        Parameters
        ----------
        channel : uita.types.DiscordChannel
            Channel to be added to server.
        server_id : int
            ID of server that channel belongs to.

        """
        log.debug("channel_add {}".format(channel.id))
        self.servers[server_id].channels[channel.id] = channel

    def channel_remove(self, channel_id, server_id):
        """Remove a server channel from Discord state.

        Parameters
        ----------
        channel_id : str
            ID of channel to be removed from server.
        server_id : str
            ID of server that channel belongs to.

        """
        log.debug("channel_remove {}".format(channel_id))
        del self.servers[server_id].channels[channel_id]

    def server_add(self, server, bot):
        """Add an accessible server to Discord state.

        Parameters
        ----------
        server : uita.types.DiscordServer
            Server that bot has joined.
        bot : discord.Client
            Bot that handles voice client connections.

        """
        log.debug("server_add {}".format(server.id))
        self.servers[server.id] = server
        # Non-POD type with persistent connections, doesn't need to be updated
        if server.id not in self.voice_connections:
            self.voice_connections[server.id] = DiscordVoiceClient(server.id, bot.loop)

    def server_remove(self, server_id):
        """Remove an accessible server from Discord state.

        Parameters
        ----------
        server_id : str
            ID of server that bot has left.

        """
        log.debug("server_remove {}".format(server_id))
        del self.servers[server_id]
        del self.voice_connections[server_id]

    def user_add_server(self, user_id, user_name, server_id):
        """Add an accessible server for a user.

        Parameters
        ----------
        user_id : str
            User to update.
        user_name : str
            New username.
        server_id : str
            Server that can be accessed.

        """
        self.servers[server_id].users[user_id] = user_name

    def user_remove_server(self, user_id, server_id):
        """Remove an inaccessible server for a user.

        Parameters
        ----------
        user_id : str
            User to update.
        server_id : str
            Server that can no longer be accessed.

        """
        del self.servers[server_id].users[user_id]


# TODO: Add category support if discord.py rewrite ever goes live
class DiscordChannel():
    """Container for Discord channel data.

    Parameters
    ----------
    id : int
        Unique channel ID.
    name : str
        Channel name.
    type : discord.ChannelType
        Channel type.
    position : int
        Ordered position in channel list.

    Attributes
    ----------
    id : int
        Unique channel ID.
    name : str
        Channel name.
    type : discord.ChannelType
        Channel type.
    position : int
        Ordered position in channel list.

    """
    def __init__(self, id, name, type, position):
        self.id = id
        self.name = name
        self.type = type
        self.position = position


class DiscordServer():
    """Container for Discord server data.

    Parameters
    ----------
    id : int
        Unique server ID.
    name : str
        Server name.
    channels : dict(channel_id: uita.types.DiscordChannel)
        Dictionary of channels in server.
    users : dict(user_id: user_name)
        Dictionary of users in server.
    icon : str
        Server icon hash.

    Attributes
    ----------
    id : int
        Unique server ID.
    name : str
        Server name.
    channels : dict(channel_id: uita.types.DiscordChannel)
        Dictionary of channels in server.
    users : dict(user_id: user_name)
        Dictionary of users in server.
    icon : str
        Server icon hash.

    """
    def __init__(self, id, name, channels, users, icon):
        self.id = id
        self.name = name
        self.channels = channels
        self.users = users
        self.icon = icon


class DiscordUser():
    """Container for Discord user data.

    Parameters
    ----------
    id : int
        Unique user ID.
    name : str
        User name.
    avatar : str
        URL to user avatar.
    session : uita.auth.Session
        Session authentication data.
    active_server_id : str
        Discord server that user has joined. None if user has not joined a server yet.

    Attributes
    ----------
    id : int
        Unique user ID.
    name : str
        User name.
    avatar : str
        URL to user avatar.
    session : uita.auth.Session
        Session authentication data.
    active_server_id : str
        Discord server that user has joined. None if user has not joined a server yet.

    """
    def __init__(self, id, name, avatar, session, active_server_id):
        self.id = id
        self.name = name
        # Hack for discord.py forcing WebP extensions even though it has terrible browser support
        # This also replaces animated GIFs with static PNGs, but thats for the best
        self.avatar = avatar.rpartition(".")[0] + ".png"
        self.session = session
        self.active_server_id = active_server_id


class DiscordVoiceClient():
    """Container for Discord voice connections.

    Parameters
    ----------
    server_id : str
        Server ID to connect to.
    loop : asyncio.AbstractEventLoop, optional
        Event loop for audio tasks to run in.

    Attributes
    ----------
    server_id : str
        Server ID to connect to.
    loop : asyncio.AbstractEventLoop
        Event loop for audio tasks to run in.

    """
    def __init__(self, server_id, loop=None):
        self.server_id = server_id
        self.loop = loop or asyncio.get_event_loop()

        async def on_queue_change(queue, user=None):
            # If the queue is changed and the bot is not connected to a voice channel, find the
            # voice channel of the user who most recently changed the queue and join it.
            # User is None for queue change callbacks that should not cause the bot to join a
            # channel, such as queue re-ordering and removal
            if self._voice is None and user is not None and len(queue) > 0:
                discord_user = uita.bot.get_server(self.server_id).get_member(user.id)
                if discord_user is not None:
                    channel = discord_user.voice.voice_channel
                    if channel is not None:
                        await self.connect(channel.id)
            elif len(queue) == 0:
                await self.disconnect()
            message = uita.message.PlayQueueSendMessage(queue)
            uita.server.send_all(message, self.server_id)

        async def on_status_change(status):
            message = uita.message.PlayStatusSendMessage(status)
            uita.server.send_all(message, self.server_id)

        self._playlist = uita.audio.Queue(
            maxlen=100,
            on_queue_change=on_queue_change,
            on_status_change=on_status_change,
            loop=self.loop
        )

        self._voice = None
        self._voice_lock = asyncio.Lock(loop=self.loop)

    @property
    def active_channel(self):
        if self._voice is not None and self._voice.is_connected():
            channel = self._voice.channel
            return DiscordChannel(channel.id, channel.name, channel.type, channel.position)
        return None

    async def connect(self, channel_id):
        """Connect bot to a voice a voice channel in this server.

        Parameters
        ----------
        channel_id : str
            ID of channel to connect to.

        """
        channel = uita.bot.get_server(self.server_id).get_channel(channel_id)
        with await self._voice_lock:
            if self._voice is None:
                self._voice = await uita.bot.join_voice_channel(channel)
                await self._playlist.play(self._voice)
            else:
                await self._voice.move_to(channel)

    async def disconnect(self):
        """Disconnect bot from the voice channels in this server."""
        with await self._voice_lock:
            if self._voice is not None:
                await self._playlist.stop()
                await self._voice.disconnect()
                self._voice = None

    async def enqueue_file(self, path, user):
        """Queues a file to be played by the running playlist task.

        Parameters
        ----------
        path : os.PathLike
            Path to audio resource to be played.
        user : uita.types.DiscordUser
            User that requested track.

        Raises
        ------
        uita.exceptions.ClientError
            If called with an unusable audio URL.

        """
        await self._playlist.enqueue_file(path, user)

    async def enqueue_url(self, url, user):
        """Queues a URL to be played by the running playlist task.

        Parameters
        ----------
        url : str
            URL for audio resource to be played.
        user : uita.types.DiscordUser
            User that requested track.

        Raises
        ------
        uita.exceptions.ClientError
            If called with an unusable audio URL.

        """
        await self._playlist.enqueue_url(url, user)

    def queue(self):
        """Retrieves a list of currently queued audio resources for this connection.

        Returns
        -------
        list
            Ordered list of audio resources queued for playback.

        """
        return self._playlist.queue()

    def queue_full(self):
        """Tests if the queue is at capacity.

        Returns
        -------
        bool
            True if the queue is full.

        """
        return self._playlist.queue_full()

    def status(self):
        """Returns the current playback status.

        Returns
        -------
        uita.audio.Status
            Enum of current playback status (playing, paused, etc).

        """
        return self._playlist.status

    async def move(self, track_id, position):
        """Moves a track to a new position in the playback queue.

        Parameters
        ----------
        track_id : str
            Track ID of audio resource to be moved.
        position : int
            Index position for the track to be moved to.

        """
        await self._playlist.move(track_id, position)

    async def remove(self, track_id):
        """Removes a track from the playback queue.

        Parameters
        ----------
        track_id : str
            Track ID of audio resource to be removed.

        """
        await self._playlist.remove(track_id)
