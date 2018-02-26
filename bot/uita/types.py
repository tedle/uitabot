"""Defines various container and running state types for the Discord API."""
import logging
log = logging.getLogger(__name__)


class DiscordState():
    """Container for active Discord data.

    Attributes
    ----------
    servers : list(uita.types.DiscordServer)
        List of servers bot is connected to.

    """
    def __init__(self):
        self.servers = {}

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
        log.debug("initialize_from_bot")
        for server in bot.servers:
            discord_channels = {
                channel.id: DiscordChannel(
                    channel.id, channel.name, channel.type, channel.position
                )
                for channel in server.channels
            }
            discord_users = {user.id: user.name for user in server.members}
            discord_server = DiscordServer(server.id, server.name, discord_channels, discord_users)
            self.servers[server.id] = discord_server

    def channel_add(self, channel, server_id):
        """Add a server channel to Discord state.

        Parameters
        ----------
        channel : uita.types.DiscordChannel
            Channel to be added to server.
        server_id : str
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

    def server_add(self, server):
        """Add an accessible server to Discord state.

        Parameters
        ----------
        server : uita.types.DiscordServer
            Server that bot has joined.

        """
        log.debug("server_add {}".format(server.id))
        self.servers[server.id] = server

    def server_remove(self, server_id):
        """Remove an accessible server from Discord state.

        Parameters
        ----------
        server_id : str
            ID of server that bot has left.

        """
        log.debug("server_remove {}".format(server_id))
        del self.servers[server_id]

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
    id : str
        Unique channel ID.
    name : str
        Channel name.
    type : discord.ChannelType
        Channel type.
    position : int
        Ordered position in channel list.

    Attributes
    ----------
    id : str
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
    id : str
        Unique server ID.
    name : str
        Server name.
    channels : dict(channel_id: uita.types.DiscordChannel)
        Dictionary of channels in server.
    users : dict(user_id: user_name)
        Dictionary of users in server.

    Attributes
    ----------
    id : str
        Unique server ID.
    name : str
        Server name.
    channels : dict(channel_id: uita.types.DiscordChannel)
        Dictionary of channels in server.
    users : dict(user_id: user_name)
        Dictionary of users in server.

    """
    def __init__(self, id, name, channels, users):
        self.id = id
        self.name = name
        self.channels = channels
        self.users = users


class DiscordUser():
    """Container for Discord user data.

    Parameters
    ----------
    id : str
        Unique user ID.
    name : str
        User name.
    session : uita.auth.Session
        Session authentication data.
    active_server_id : str
        Discord server that user has joined. None if user has not joined a server yet.

    Attributes
    ----------
    id : str
        Unique user ID.
    name : str
        User name.
    session : uita.auth.Session
        Session authentication data.
    active_server_id : str
        Discord server that user has joined. None if user has not joined a server yet.

    """
    def __init__(self, id, name, session, active_server_id):
        self.id = id
        self.name = name
        self.session = session
        self.active_server_id = active_server_id
