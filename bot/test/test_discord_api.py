import pytest
from unittest.mock import Mock, patch

import json

import uita.discord_api


@pytest.mark.asyncio
async def test_auth(data_dir, config, event_loop):
    code = "oauth2code"
    response_json = json.load(data_dir / "discord-api-auth.json")
    with patch("uita.discord_api.requests.post") as mock_post:
        with pytest.raises(uita.exceptions.AuthenticationError):
            await uita.discord_api.auth("bad.code", config, event_loop)

        with pytest.raises(uita.exceptions.AuthenticationError):
            mock_post.return_value.status_code = 403
            await uita.discord_api.auth(code, config, event_loop)

        def data_check(url, data, headers):
            assert data["code"] == code
            response = Mock()
            response.status_code = 200
            response.json.return_value = response_json
            return response
        mock_post.side_effect = data_check

        auth_response = await uita.discord_api.auth(code, config, event_loop)
        assert auth_response == response_json


@pytest.mark.asyncio
async def test_get(data_dir, event_loop):
    token = "goodtoken"
    end_point = "/user/@me"
    response_json = json.load(data_dir / "discord-api-user.json")
    with patch("uita.discord_api.requests.get") as mock_get:
        def data_check(url, headers):
            response = Mock()
            if headers["Authorization"] == f"Bearer {token}":
                response.status_code = 200
            else:
                response.status_code = 403
            response.json.return_value = response_json
            return response
        mock_get.side_effect = data_check

        with pytest.raises(uita.exceptions.AuthenticationError):
            await uita.discord_api.get(end_point, "badtoken", event_loop)

        get_response = await uita.discord_api.get(end_point, token, event_loop)
        assert get_response == response_json


@pytest.mark.asyncio
async def test_avatar_url(data_dir):
    user = json.load(data_dir / "discord-api-user.json")

    avatar = uita.discord_api.avatar_url(user)
    assert avatar == f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png"

    user["avatar"] = None
    avatar = uita.discord_api.avatar_url(user)
    assert avatar == f"https://cdn.discordapp.com/embed/avatars/{int(user['discriminator'])%5}.png"

    with pytest.raises(KeyError):
        del user["avatar"]
        uita.discord_api.avatar_url(user)
