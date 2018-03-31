"""Async HTTP requests to the Discord API"""
import re
import requests

import uita
import uita.exceptions


# API config definitions
BASE_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "uitabot (https://github.com/tedle, {})".format(uita.__version__)
}
BASE_URL = "https://discordapp.com/api"
AUTH_URL = BASE_URL + "/oauth2/token"
API_URL = BASE_URL + "/v6"
VALID_CODE_REGEX = re.compile("^([a-zA-Z0-9]+)$")


async def auth(code, config, loop):
    """Retrieves an access token from the Discord API with an authourization code.

    Parameters
    ----------
    code : str
        Access code presented by redirect URI. Must be alphanumeric.
    config : uita.config.Config
        Configuration options containing API keys.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach blocking request threads to.

    Returns
    -------
    dict
        JSON decoded token data of authenticated user.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If code is invalid.

    """
    # Since these are passed by the client, sanitize to expected format
    if VALID_CODE_REGEX.match(code) is None:
        raise uita.exceptions.AuthenticationError("Passed an invalidly formatted auth code")
    # Generate a redirect URL since it is required, even though we aren't being redirected anywhere
    redirect = "http{}://{}{}".format(
        "s" if config.ssl.cert_file is not None else "",
        config.client.domain,
        (":{}".format(config.client.port)) if config.client.port is not 80 else ""
    )
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": config.discord.client.id,
        "client_secret": config.discord.client.secret,
        "redirect_uri": redirect
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
    return response.json()


async def get(end_point, token, loop):
    """Retrieves an object from the Discord API with an authorization token.

    Parameters
    ----------
    end_point : str
        Discord API end point to access.
    token : str
        User authorization token for the Discord API.
    loop : asyncio.AbstractEventLoop, optional
        Event loop to attach blocking request threads to.

    Returns
    -------
    dict
        JSON decoded data of the requested object.

    Raises
    ------
    uita.exceptions.AuthenticationError
        If request is invalid.

    """
    headers = BASE_HEADERS.copy()
    headers["Authorization"] = "Bearer {}".format(token)
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
    return response.json()
