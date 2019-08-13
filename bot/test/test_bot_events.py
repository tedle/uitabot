import pytest
from unittest.mock import Mock, patch

import discord
import uuid

import uita
import uita.bot_events
import uita.database


async def async_stub(*args, **kwargs): ...


@pytest.fixture
def bot(config, event_loop, user):
    with patch("uita.bot") as mock_bot, \
         patch("uita.server") as mock_server:
        mock_bot.wait_until_ready.side_effect = async_stub
        mock_bot.guilds = []
        mock_bot.loop = event_loop
        mock_bot.user = user()
        mock_server.config = config
        mock_server.database = uita.database.Database(config.bot.database)
        mock_server.verify_active_servers.side_effect = async_stub
        uita.state.initialize_from_bot(mock_bot)
        yield mock_bot


@pytest.fixture
def channel():
    def make_channel(guild):
        mock_channel = Mock()
        mock_channel.id = uuid.uuid4().int
        mock_channel.guild = guild
        return mock_channel
    return make_channel


@pytest.fixture
def guild(bot, member):
    def make_guild(name="Server name"):
        mock_guild = Mock()
        mock_guild.id = uuid.uuid4().int
        mock_guild.name = name
        mock_guild.channels = []
        mock_guild.me = member(mock_guild, bot.user)
        mock_guild.members = [mock_guild.me]
        return mock_guild
    return make_guild


@pytest.fixture
def member(user):
    def make_member(guild, base_user=None):
        mock_member = base_user if base_user is not None else user()
        mock_member.guild = guild
        mock_member.roles = []
        mock_member.guild_permissions.administrator = False
        return mock_member
    return make_member


@pytest.fixture
def user():
    def make_user():
        mock_user = Mock()
        mock_user.id = uuid.uuid4().int
        return mock_user
    return make_user


@pytest.fixture
def role():
    def make_role(guild):
        mock_role = Mock()
        mock_role.id = uuid.uuid4().int
        mock_role.guild = guild
        return mock_role
    return make_role


@pytest.mark.asyncio
async def test_on_guild_channel(bot, guild, channel):
    mock_guild = guild()
    mock_channel = channel(mock_guild)
    server = uita.types.DiscordServer(str(mock_guild.id), mock_guild.name, {}, {}, None)
    uita.state.server_add(server, bot)

    with patch("uita.bot_events._sync_channels") as mock_sync:
        await uita.bot_events.on_guild_channel_create(mock_channel)
        assert str(mock_channel.id) in uita.state.servers[str(mock_guild.id)].channels
        assert mock_sync.call_count == 1

        await uita.bot_events.on_guild_channel_delete(mock_channel)
        assert str(mock_channel.id) not in uita.state.servers[str(mock_guild.id)].channels
        assert mock_sync.call_count == 2


@pytest.mark.asyncio
async def test_on_guild_role(bot, guild, channel, role):
    mock_guild = guild()
    mock_channel = channel(mock_guild)
    mock_guild.channels = [mock_channel]
    mock_role = role(mock_guild)

    with patch("uita.bot_events.uita.utils.verify_channel_visibility") as mock_visibility:
        # on create
        mock_visibility.return_value = True
        await uita.bot_events.on_guild_role_create(mock_role)
        assert len(uita.state.servers[str(mock_guild.id)].channels) == 1
        mock_visibility.return_value = False
        await uita.bot_events.on_guild_role_create(mock_role)
        assert len(uita.state.servers[str(mock_guild.id)].channels) == 0

        # on delete
        mock_visibility.return_value = True
        uita.state.server_set_role(str(mock_guild.id), str(mock_role.id))
        assert uita.state.server_get_role(str(mock_guild.id)) == str(mock_role.id)
        await uita.bot_events.on_guild_role_delete(mock_role)
        assert uita.state.server_get_role(str(mock_guild.id)) is None


@pytest.mark.asyncio
async def test_on_member(bot, guild, member, role):
    mock_guild = guild()
    mock_role = role(mock_guild)
    mock_member = member(mock_guild)
    server = uita.types.DiscordServer(str(mock_guild.id), mock_guild.name, {}, {}, None)
    uita.state.server_add(server, bot)

    # on join
    await uita.bot_events.on_member_join(mock_member)
    assert str(mock_member.id) in uita.state.servers[str(mock_guild.id)].users

    # on leave
    await uita.bot_events.on_member_remove(mock_member)
    assert str(mock_member.id) not in uita.state.servers[str(mock_guild.id)].users

    # on join with insufficient permissions
    uita.state.server_set_role(str(mock_guild.id), str(mock_role.id))
    await uita.bot_events.on_member_join(mock_member)
    assert str(mock_member.id) not in uita.state.servers[str(mock_guild.id)].users


@pytest.mark.asyncio
async def test_on_message(bot, member):
    message = Mock(spec=discord.Message)
    with patch("uita.bot_commands.parse") as mock_parse:
        mock_parse.side_effect = async_stub

        # Bot can't trigger itself
        message.author.id = bot.user.id
        await uita.bot_events.on_message(message)
        assert mock_parse.call_count == 0

        # Bot can't trigger on private messages
        message.author.id = 0
        message.channel = Mock(spec=discord.abc.PrivateChannel)
        await uita.bot_events.on_message(message)
        assert mock_parse.call_count == 0

        # Bot can trigger on guild messages
        message.channel = Mock(spec=discord.abc.GuildChannel)
        await uita.bot_events.on_message(message)
        assert mock_parse.call_count == 1


@pytest.mark.asyncio
async def test_on_guild(bot, guild, channel, member):
    mock_guild = guild()
    mock_channel = channel(mock_guild)
    mock_member = member(mock_guild)
    mock_guild.channels = [mock_channel]
    mock_guild.members = [mock_member]

    await uita.bot_events.on_guild_join(mock_guild)
    assert str(mock_guild.id) in uita.state.servers
    assert str(mock_channel.id) in uita.state.servers[str(mock_guild.id)].channels
    assert str(mock_member.id) in uita.state.servers[str(mock_guild.id)].users

    with patch("uita.bot_events._sync_channels") as mock_sync:
        await uita.bot_events.on_guild_update(mock_guild, mock_guild)
        assert mock_sync.call_count == 1

    await uita.bot_events.on_guild_remove(mock_guild)
    assert str(mock_guild.id) not in uita.state.servers


@pytest.mark.asyncio
async def test_on_voice_state(bot, guild, channel, member):
    mock_guild = guild()
    mock_member = member(mock_guild)
    mock_channel = channel(mock_guild)
    mock_channel.members = [mock_guild.me, mock_member]
    mock_voice_before = Mock(spec=discord.VoiceState)
    mock_voice_after = Mock(spec=discord.VoiceState)
    mock_voice_before.channel = mock_channel
    mock_voice_after.channel = None

    await uita.bot_events.on_voice_state_update(mock_guild.me, mock_voice_before, mock_voice_after)
    assert uita.server.send_all.call_count == 1

    mock_bot_voice = Mock(spec=uita.types.DiscordVoiceClient)
    mock_bot_voice.disconnect.side_effect = async_stub
    uita.state.voice_connections[str(mock_guild.id)] = mock_bot_voice

    # Don't disconnect if not in a channel
    mock_bot_voice.active_channel.id = str(0)
    mock_channel.members = [mock_guild.me]
    await uita.bot_events.on_voice_state_update(mock_member, mock_voice_before, mock_voice_after)
    assert mock_bot_voice.disconnect.call_count == 0

    # Don't disconnect if other members are listening
    mock_bot_voice.active_channel.id = str(mock_channel.id)
    mock_channel.members = [mock_guild.me, mock_member]
    await uita.bot_events.on_voice_state_update(mock_member, mock_voice_before, mock_voice_after)
    assert mock_bot_voice.disconnect.call_count == 0

    # Disconnect if alone in channel
    mock_bot_voice.active_channel.id = str(mock_channel.id)
    mock_channel.members = [mock_guild.me]
    await uita.bot_events.on_voice_state_update(mock_member, mock_voice_before, mock_voice_after)
    assert mock_bot_voice.disconnect.call_count == 1
