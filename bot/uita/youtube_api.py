"""Async HTTP requests to the Youtube API"""
import asyncio
import re
import requests
import urllib.parse
import youtube_dl
from typing import Any, Dict, List, Optional
from typing_extensions import Final

import uita.exceptions

import logging
log = logging.getLogger(__name__)


# API config definitions
BASE_HEADERS: Final = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "uitabot ({}, {})".format(uita.__url__, uita.__version__)
}
API_URL: Final = "https://www.googleapis.com/youtube/v3"


async def scrape(url: str, loop: Optional[asyncio.AbstractEventLoop] = None) -> Dict[str, Any]:
    """Queries YouTube for URL metadata.

    Args:
        url: URL for audio resource to be played.
        loop: Event loop to attach to launch worker threads from.

    Returns:
        YoutubeDL dict soup response.

    Raises:
        uita.exceptions.ClientError: If called with an unusable audio path.

    """
    loop = loop or asyncio.get_event_loop()
    null_log = logging.Logger("dummy")
    null_log.addHandler(logging.NullHandler())

    opts = {
        # bestaudio prefers videoless streams, which often have a lower bitrate
        # ironically not the best audio
        # also highly values lower bitrate vorbis streams over higher bitrate opus?? why.
        "format": "best[acodec=opus]/bestaudio[acodec=opus]/bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "logger": null_log,
        "skip_download": True
    }
    scraper = youtube_dl.YoutubeDL(opts)
    valid_extractors = ["Youtube", "YoutubePlaylist"]
    for extractor in valid_extractors:
        try:
            info = await loop.run_in_executor(
                None,
                lambda: scraper.extract_info(url, download=False, ie_key=extractor)
            )
            info["extractor"] = extractor
            return info
        # Triggers when URL doesnt match extractor used
        except youtube_dl.utils.DownloadError:
            pass
    raise uita.exceptions.ClientError(uita.message.ErrorUrlInvalidMessage())


async def search(
    query: str,
    api_key: Optional[str] = None,
    referrer: Optional[str] = None,
    results: int = 5,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> List[Dict[str, Any]]:
    """Queries YouTube for search results.

    Args:
        query: Search query for audio resource to be found.
        api_key: API key for Youtube searches. Defaults to `None` which performs a much slower
            search using youtube-dl.
        referrer: Referrer for HTTP requests, in case API restrictions are in place.
        results: Number of results to retrieve, default ``5``.
        loop: Event loop to attach to launch worker threads from.

    Returns:
        List of search results.

    Raises:
        uita.exceptions.ClientError: If called with an unusable search query.

    """
    loop = loop or asyncio.get_event_loop()
    # Without an API key we take the much slower path using youtube-dl
    if api_key is None:
        return await _search_slow(query, results, loop)
    # Build and request the initial search results
    url = (
        "{}/search/?"
        + "q={}"
        + "&maxResults={}"
        + "&part=snippet"
        + "&type=video"
        + "&key={}"
    ).format(API_URL, urllib.parse.quote_plus(query), results, api_key)
    headers = BASE_HEADERS
    if referrer is not None:
        headers["referer"] = referrer
    response = await loop.run_in_executor(
        None,
        lambda: requests.get(url, headers=headers)
    )
    if response.status_code != 200:
        raise uita.exceptions.ClientError(uita.message.ErrorUrlInvalidMessage())
    search_results = response.json()["items"]
    # Request detailed results for each video (to get the duration)
    video_ids = [r["id"]["videoId"] for r in search_results]
    details_url = (
        "{}/videos/?"
        + "id={}"
        + "&part=contentDetails"
        + "&key={}"
    ).format(API_URL, ",".join(video_ids), api_key)
    details_response = await loop.run_in_executor(
        None,
        lambda: requests.get(details_url, headers=headers)
    )
    if details_response.status_code != 200:
        raise uita.exceptions.ClientError(uita.message.ErrorUrlInvalidMessage())
    details_results = details_response.json()["items"]
    # Build and return the final query results
    durations = {r["id"]: parse_time(r["contentDetails"]["duration"]) for r in details_results}
    return [{
        "id": r["id"]["videoId"],
        "live": True if r["snippet"]["liveBroadcastContent"] == "live" else False,
        "thumbnail": r["snippet"]["thumbnails"]["default"]["url"],
        "title": r["snippet"]["title"],
        "uploader": r["snippet"]["channelTitle"],
        "duration": durations[r["id"]["videoId"]],
        "url": build_url(r["id"]["videoId"])
    } for r in search_results]


def parse_time(time: str) -> int:
    """Converts a YouTube timestamp into seconds.

    Args:
        time: Timestamp from YouTube API.

    Returns:
        Time in seconds.

    """
    duration = 0
    for match in re.finditer("(\\d+)(H|M|S)", time):
        number, interval = match.group(1, 2)
        if interval == "H":
            duration += int(number) * 60 * 60
        elif interval == "M":
            duration += int(number) * 60
        elif interval == "S":
            duration += int(number)
        else:
            raise TypeError("Incorrect YouTube timestamp format")
    return duration


def build_url(video_id: str) -> str:
    """Converts a YouTube video ID into a valid URL.

    Args:
        video_id: YouTube video ID.

    Returns:
        YouTube video URL.

    """
    return "https://youtube.com/watch?v={}".format(video_id)


async def _search_slow(
    query: str,
    results: int,
    loop: asyncio.AbstractEventLoop
) -> List[Dict[str, Any]]:
    null_log = logging.Logger("dummy")
    null_log.addHandler(logging.NullHandler())

    opts = {
        "quiet": True,
        "no_warnings": True,
        "logger": null_log,
        "skip_download": True
    }
    scraper = youtube_dl.YoutubeDL(opts)
    try:
        search_results = await loop.run_in_executor(
            None,
            lambda: scraper.extract_info("ytsearch{}:{}".format(results, query), download=False)
        )
        # Filter out any entries that aren't in this whitelist
        whitelist = set([
            "id",
            "duration",
            "is_live",
            "thumbnail",
            "title",
            "uploader"
        ])
        entries = [
            dict(filter(lambda x: x[0] in whitelist, e.items()))
            for e in search_results["entries"]
        ]
        # By default is True or None for some reason
        for entry in entries:
            entry["live"] = entry["is_live"] or False
            entry["url"] = build_url(entry["id"])
        return entries
    # Triggers when query doesnt match extractor used
    except youtube_dl.utils.DownloadError:
        pass
    raise uita.exceptions.ClientError(uita.message.ErrorUrlInvalidMessage())
