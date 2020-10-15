"""Async HTTP requests to the Discord API"""
import asyncio
import re
import requests
from typing import cast, Any, Dict, Optional
from typing_extensions import Final

import uita
import uita.exceptions
import uita.utils


# API config definitions
BASE_HEADERS: Final = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": f"uitabot ({uita.__url__}, {uita.__version__})"
}
BASE_URL: Final = "https://discord.com/api"
AUTH_URL: Final = BASE_URL + "/oauth2/token"
API_URL: Final = BASE_URL + "/v8"
CDN_URL: Final = "https://cdn.discordapp.com"
VALID_CODE_REGEX: Final = re.compile("^([a-zA-Z0-9]+)$")


async def auth(
    code: str,
    config: uita.config.Config,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> Dict[str, Any]:
    """Retrieves an access token from the Discord API with an authourization code.

    Args:
        code: Access code presented by redirect URI. Must be alphanumeric.
        config: Configuration options containing API keys.
        loop: Event loop to attach blocking request threads to.

    Returns:
        JSON decoded token data of authenticated user.

    Raises:
        uita.exceptions.AuthenticationError: If code is invalid.

    """
    loop = loop or asyncio.get_event_loop()
    # Since these are passed by the client, sanitize to expected format
    if VALID_CODE_REGEX.match(code) is None:
        raise uita.exceptions.AuthenticationError("Passed an invalidly formatted auth code")
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": config.discord.client.id,
        "client_secret": config.discord.client.secret,
        "redirect_uri": uita.utils.build_client_url(config)
    }
    # requests is not asynchronous, so run in another thread and await it
    response = await loop.run_in_executor(
        None,
        lambda: requests.post(
            AUTH_URL,
            data=data,
            headers=BASE_HEADERS
        )
    )
    if response.status_code != 200:
        raise uita.exceptions.AuthenticationError("Passed an incorrect auth code")
    return cast(Dict[str, Any], response.json())


async def get(
    end_point: str,
    token: str,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> Dict[str, Any]:
    """Retrieves an object from the Discord API with an authorization token.

    Args:
        end_point: Discord API end point to access.
        token: User authorization token for the Discord API.
        loop: Event loop to attach blocking request threads to.

    Returns:
        JSON decoded data of the requested object.

    Raises:
        uita.exceptions.AuthenticationError: If request is invalid.

    """
    loop = loop or asyncio.get_event_loop()
    headers = BASE_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    # requests is not asynchronous, so run in another thread and await it
    response = await loop.run_in_executor(
        None,
        lambda: requests.get(
            BASE_URL + end_point,
            headers=headers
        )
    )
    if response.status_code != 200:
        raise uita.exceptions.AuthenticationError("Made an invalid Discord API request")
    return cast(Dict[str, Any], response.json())


def avatar_url(user: Dict[str, Any]) -> str:
    """Generates an avatar CDN URL from a supplied API User GET response.

    Args:
        user: JSON decoded data of a Discord API User object.

    Returns:
        URL to user avatar.

    Raises:
        KeyError: If supplied object is missing expected values.

    """
    if user["avatar"]:
        return CDN_URL + f"/avatars/{user['id']}/{user['avatar']}.png"
    else:
        return CDN_URL + f"/embed/avatars/{int(user['discriminator']) % 5}.png"
