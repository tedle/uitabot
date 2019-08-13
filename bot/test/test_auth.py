import pytest
from unittest.mock import patch

import json

import uita.auth


@pytest.mark.asyncio
async def test_verify_session(config, database, data_dir):
    session = database.add_session("token", 0)
    raw_response = json.load(data_dir / "discord-api-user.json")
    with patch("uita.auth.uita.discord_api.get") as mock_get:
        async def get(*args, **kwargs): return raw_response
        mock_get.side_effect = get
        user = await uita.auth.verify_session(session, database, config)
    assert user.id == raw_response["id"]


@pytest.mark.asyncio
async def test_verify_session_expired(config, database):
    # Should fail if session does not exist
    with pytest.raises(uita.exceptions.AuthenticationError):
        await uita.auth.verify_session(uita.auth.Session("1", "2"), database, config)


@pytest.mark.asyncio
async def test_verify_code(config, database, data_dir):
    raw_response = json.load(data_dir / "discord-api-auth.json")
    with patch("uita.auth.uita.discord_api.auth") as mock_auth:
        async def auth(*args, **kwargs): return raw_response
        mock_auth.side_effect = auth
        session = await uita.auth.verify_code("code", database, config)
    assert database.get_access_token(session) == raw_response["access_token"]
