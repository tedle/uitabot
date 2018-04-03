"""Audio queue management."""
import asyncio
import youtube_dl

import uita.exceptions

import logging
log = logging.getLogger(__name__)


async def scrape(url, loop=None):
    """Queries YouTube for URL metadata.

    Parameters
    ----------
    url : str
        URL for audio resource to be played.

    Returns
    -------
    dict
        YoutubeDL dict soup response.

    Raises
    ------
    uita.exceptions.ClientError
        If called with an unusable audio path.

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
