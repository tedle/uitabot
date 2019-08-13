import pytest
from unittest.mock import Mock, patch

import discord

import uita
import uita.types


def test_initialize_from_bot(event_loop):
    with patch("uita.server") as mock_server, \
         patch("uita.utils.verify_channel_visibility", return_value=True), \
         patch("uita.utils.verify_user_permissions", return_value=True):
        mock_server.database.get_server_role.return_value = None
        mock_bot = Mock(**{
            "guilds": [Mock(**{
                "id": 99999,
                "name": "server-name",
                "channels": [Mock(**{
                    "id": 12345,
                    "name": "channel-name",
                    "type": discord.ChannelType.voice,
                    "category_id": 54321,
                    "position": 1
                })],
                "members": [Mock(**{
                    "id": 11111,
                    "name": "user-name"
                })],
                "icon": None
            })],
            "loop": event_loop
        })

        state = uita.types.DiscordState()
        state.initialize_from_bot(mock_bot)

        assert "99999" in state.servers
        assert "12345" in state.servers["99999"].channels
        assert "11111" in state.servers["99999"].users


def test_channel(event_loop):
    with patch("uita.server") as mock_server:
        mock_server.database.get_server_role.return_value = None
        channel = uita.types.DiscordChannel("12345", "channel", discord.ChannelType.voice, "9", 1)
        server = uita.types.DiscordServer("54321", "server", {}, {}, None)

    state = uita.types.DiscordState()

    with pytest.raises(KeyError):
        state.channel_add(channel, server.id)

    state.server_add(server, Mock(loop=event_loop))
    state.channel_add(channel, server.id)
    assert channel.id in state.servers[server.id].channels
    assert state.servers[server.id].channels[channel.id].name == channel.name

    state.channel_remove(channel.id, server.id)
    assert channel.id not in state.servers[server.id].channels


def test_server(event_loop):
    with patch("uita.server") as mock_server:
        mock_server.database.get_server_role.return_value = None
        server = uita.types.DiscordServer("12345", "server", {}, {}, None)

    state = uita.types.DiscordState()

    state.server_add(server, Mock(loop=event_loop))
    assert server.id in state.servers
    assert server.id in state.voice_connections

    state.server_remove(server.id)
    assert server.id not in state.servers
    assert server.id not in state.voice_connections


def test_user(event_loop):
    with patch("uita.server") as mock_server:
        mock_server.database.get_server_role.return_value = None
        user = uita.types.DiscordUser("12345", "user", "http://example.com/image.png", None)
        server = uita.types.DiscordServer("54321", "server", {}, {}, None)

    state = uita.types.DiscordState()

    with pytest.raises(KeyError):
        state.server_add_user(server.id, user.id, user.name)

    state.server_add(server, Mock(loop=event_loop))
    state.server_add_user(server.id, user.id, user.name)
    assert user.id in state.servers[server.id].users
    assert state.servers[server.id].users[user.id] == user.name

    state.server_remove_user(server.id, user.id)
    assert user.id not in state.servers[server.id].users


def test_role(event_loop):
    with patch("uita.server") as mock_server:
        state = uita.types.DiscordState()
        server = uita.types.DiscordServer("12345", "server", {}, {}, None)
        server.role = "321"

        mock_server.database.get_server_role.return_value = "123"
        assert state.server_get_role(server.id) == "123"

        state.server_add(server, Mock(loop=event_loop))
        assert state.server_get_role(server.id) == "321"

        state.server_set_role(server.id, "999")
        assert state.server_get_role(server.id) == "999"
