import asyncio
import collections
import youtube_dl

import uita.exceptions

import logging
log = logging.getLogger(__name__)


class Track():
    """Container for audio resource metadata.

    Parameters
    ----------
    url : str
        URL to audio resource for ffmpeg to load.
    title : str
        Title of track.
    duration : int
        Track duration in seconds.

    Attributes
    ----------
    url : str
        URL to audio resource for ffmpeg to load.
    title : str
        Title of track.
    duration : int
        Track duration in seconds.

    """
    def __init__(self, url, title, duration):
        self.url = url
        self.title = title
        self.duration = duration


class Queue():
    """Queues audio resources to be played by a looping task.

    Parameters
    ----------
    loop : asyncio.AbstractEventLoop, optional
        Event loop for audio tasks to run in.

    Attributes
    ----------
    loop : asyncio.AbstractEventLoop
        Event loop for audio tasks to run in.

    """
    def __init__(self, loop=None):
        # Start queue loop here?
        self.loop = loop or asyncio.get_event_loop()
        self.now_playing = None
        self.queue = collections.deque()
        self._queue_update_flag = asyncio.Event(loop=self.loop)
        self._play_task = None

    async def play(self, voice):
        """Starts a new playlist task that awaits and plays new queue inputs.

        First stops current playlist task if it exists.

        Parameters
        ----------
        voice : discord.VoiceClient
            Voice connection to spawn audio players for.

        """
        # Cancels currently running play task
        await self.stop()
        self._play_task = self.loop.create_task(self._play_loop(voice))

    async def stop(self):
        """Stops and currently playing audio and cancels the running play task."""
        if self._play_task is not None:
            self._play_task.cancel()
            await self._play_task

    async def enqueue(self, url):
        """Queues a URL to be played by the running playlist task.

        Parameters
        ----------
        url : str
            URL for audio resource to be played.

        Raises
        ------
        uita.exceptions.MalformedMessage
            If called with an unusable audio URL.

        """
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
        info = None
        extractor_used = None
        valid_extractors = ["Youtube", "YoutubePlaylist"]
        for extractor in valid_extractors:
            try:
                info = await self.loop.run_in_executor(
                    None,
                    lambda: scraper.extract_info(url, download=False, ie_key=extractor)
                )
                extractor_used = extractor
                # Break on first valid extraction
                break
            # Triggers when URL doesnt match extractor used
            except youtube_dl.utils.DownloadError:
                pass
        if extractor_used == "Youtube":
            log.debug("Enqueue [YouTube]{}({}) {}@{}abr, {}s".format(
                info["title"],
                info["id"],
                info["acodec"],
                info["abr"],
                info["duration"]
            ))
            # is_live is either True or None?? Thanks ytdl
            if info["is_live"] is True:
                raise uita.exceptions.MalformedMessage("Live YouTube URLs are unsupported")
            self.queue.append(Track(info["url"], info["title"], info["duration"]))
            self._queue_update_flag.set()
        elif extractor_used == "YoutubePlaylist":
            log.debug("YoutubePlaylists still unimplemented!")
            raise uita.exceptions.MalformedMessage("YoutubePlaylists unimplemented (but will be)")
        elif extractor_used is None:
            raise uita.exceptions.MalformedMessage("Malformed URLs should send an error message")
        else:
            raise uita.exceptions.MalformedMessage("Unhandled extractor used")

    def _after_song(self):
        self.now_playing = None
        self._queue_update_flag.set()

    async def _play_loop(self, voice):
        try:
            while True:
                self._queue_update_flag.clear()
                if self.now_playing is None and len(self.queue) > 0:
                    self.now_playing = self.queue.popleft()
                    log.debug("Now playing {}".format(self.now_playing.title))
                    # Launch ffmpeg process
                    player = voice.create_ffmpeg_player(
                        self.now_playing.url,
                        # before_options="-ss 60 -reconnect 1"
                        # -reconnect_streamed 1 -reconnect_delay_max 3
                        before_options="-reconnect 1",
                        # options="-b:a 128k -bufsize 128k"
                        # options="-f s16le -ac 2 -ar 48000 -acodec pcm_s16le -vn"
                        options="-acodec pcm_s16le -vn",
                        after=lambda: self.loop.call_soon_threadsafe(self._after_song)
                    )
                    # Gives ffmpeg a second to load and buffer audio before playing
                    await asyncio.sleep(1, loop=self.loop)
                    # About the same as a max volume YouTube video, I think
                    player.volume = 0.5
                    player.start()
                await self._queue_update_flag.wait()
        except asyncio.CancelledError:
            pass
