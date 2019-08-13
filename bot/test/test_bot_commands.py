import pytest
from unittest.mock import Mock, patch

import discord

import uita.bot_commands


@pytest.fixture
def mock_message():
    message = Mock(spec=discord.Message)
    async def stub(*args, **kwargs): ...
    message.channel.send.side_effect = stub
    return message


@pytest.fixture
def patch_state():
    with patch("uita.bot_commands.uita.state") as mock_state:
        mock_state.server_get_role.return_value = None
        yield


@pytest.mark.asyncio
async def test_set_prefix(mock_message, patch_state, event_loop, request):
    @uita.bot_commands.command("test")
    async def command_test(message, params):
        await message.channel.send("success")

    async def stub(*args, **kwargs): ...

    # Record and restore global state (sorry)
    original_prefix = uita.bot_commands._COMMAND_PREFIX

    def restore():
        with patch("uita.bot_commands.uita.bot") as mock_bot:
            mock_bot.change_presence.side_effect = stub
            event_loop.run_until_complete(uita.bot_commands.set_prefix(original_prefix))
    request.addfinalizer(restore)

    # Run the actual test
    with patch("uita.bot_commands.uita.bot") as mock_bot:
        mock_bot.change_presence.side_effect = stub
        await uita.bot_commands.set_prefix("!")
        mock_message.content = "!test"
        await uita.bot_commands.parse(mock_message)
        mock_message.channel.send.assert_called_once_with("success")


@pytest.mark.asyncio
async def test_help(mock_message, patch_state, config):
    with patch("uita.bot") as mock_bot, \
         patch("uita.server") as mock_server:
        mock_bot.user.name = "uitabot"
        mock_server.config = config
        mock_message.content = ".help"
        await uita.bot_commands.parse(mock_message)
    embed = mock_message.channel.send.call_args[1]["embed"]
    assert embed.title == "Help info"
