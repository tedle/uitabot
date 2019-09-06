import pytest
from unittest.mock import Mock

import discord
from pathlib import Path

import uita.utils


@pytest.mark.asyncio
async def test_dir_size(tmp_path):
    for i in range(5):
        with (tmp_path / str(i)).open("wb") as f:
            f.seek(9)
            f.write(b"\0")
    (tmp_path / "subdir").mkdir()
    for i in range(5):
        with (tmp_path / "subdir" / str(i)).open("wb") as f:
            f.seek(9)
            f.write(b"\0")

    assert await uita.utils.dir_size(tmp_path) == 100


@pytest.mark.asyncio
async def test_cache():
    cache_dir = Path(uita.utils.cache_dir())

    assert cache_dir.exists()
    assert cache_dir.stat().st_mode == 0o40700

    prune_file = cache_dir / "a"
    safe1_file = cache_dir / "b"
    safe2_file = cache_dir / "c"
    prune_file.touch()
    safe1_file.touch()
    safe2_file.touch()

    with uita.utils.prune_cache_guard(str(safe1_file)):
        await uita.utils.prune_cache_dir([str(safe2_file)])

    assert not prune_file.exists()
    assert safe1_file.exists()
    assert safe2_file.exists()


def test_url_builders(config):
    assert uita.utils.build_client_url(config) == "http://localhost:23231"
    assert uita.utils.build_websocket_url(config) == "ws://localhost:23230"


def test_verify_channel_visibility():
    permissions = discord.Permissions(0)
    voice_channel_mock = Mock(spec=discord.abc.GuildChannel, **{
        "type": discord.ChannelType.voice,
        "permissions_for.return_value": permissions
    })
    text_channel_mock = Mock(spec=discord.abc.GuildChannel, **{
        "type": discord.ChannelType.text,
        "permissions_for.return_value": permissions
    })
    user_mock = Mock(spec=discord.Member)

    permissions.connect, permissions.read_messages = True, False
    assert not uita.utils.verify_channel_visibility(voice_channel_mock, user_mock)

    permissions.connect, permissions.read_messages = False, True
    assert not uita.utils.verify_channel_visibility(voice_channel_mock, user_mock)

    permissions.connect, permissions.read_messages = True, True
    assert uita.utils.verify_channel_visibility(voice_channel_mock, user_mock)

    permissions.read_messages = False
    assert not uita.utils.verify_channel_visibility(text_channel_mock, user_mock)

    permissions.read_messages = True
    assert uita.utils.verify_channel_visibility(text_channel_mock, user_mock)


def test_verify_user_permissions():
    role = "123"
    role_mock = Mock(spec=discord.Role, id=int(role))
    user_mock = Mock(spec=discord.Member, **{
        "guild_permissions.administrator": False,
        "roles": []
    })

    assert uita.utils.verify_user_permissions(user_mock, None)
    assert not uita.utils.verify_user_permissions(user_mock, role)

    user_mock.guild_permissions.administrator = True
    assert uita.utils.verify_user_permissions(user_mock, role)
    user_mock.guild_permissions.administrator = False

    user_mock.roles = [role_mock]
    assert uita.utils.verify_user_permissions(user_mock, role)


def test_ffmpeg_version():
    # Test relies on external environment, but good for raising alarms about ffmpeg configurations
    # that fail to be parsed or are not found.
    version = uita.utils.ffmpeg_version()
    assert version is not None
