import asyncio
import atexit
import collections
import queue
import subprocess
import threading
import time
import uuid
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
    live : bool
        Determines if the track is a remote livestream.

    Attributes
    ----------
    id : str
        Unique 32 character long ID.
    url : str
        URL to audio resource for ffmpeg to load.
    title : str
        Title of track.
    duration : int
        Track duration in seconds.
    live : bool
        Determines if the track is a remote livestream.
    offset : float
        Offset in seconds to start track from.

    """
    def __init__(self, url, title, duration, live):
        self.id = uuid.uuid4().hex
        self.url = url
        self.title = title
        self.duration = duration
        self.live = live
        self.offset = 0.0


class Queue():
    """Queues audio resources to be played by a looping task.

    Parameters
    ----------
    on_queue_change : callback(list), optional
        Callback that is triggered everytime the state of the playback queue changes. Function
        accepts a list of `uita.audio.Track`s as its only argument.
    loop : asyncio.AbstractEventLoop, optional
        Event loop for audio tasks to run in.

    Attributes
    ----------
    loop : asyncio.AbstractEventLoop
        Event loop for audio tasks to run in.

    """
    def __init__(self, on_queue_change=None, loop=None):
        # async lambdas don't exist
        async def dummy_queue_change(q): pass
        self._on_queue_change = on_queue_change or dummy_queue_change

        self.loop = loop or asyncio.get_event_loop()
        self._now_playing = None
        self._queue = collections.deque()
        self._queue_update_flag = asyncio.Event(loop=self.loop)
        self._play_task = None
        self._play_start_time = None
        self._stream = None

    def queue(self):
        """Retrieves a list of currently queued audio resources.

        Returns
        -------
        list
            Ordered list of audio resources queued for playback.

        """
        return ([self._now_playing] if self._now_playing is not None else []) + list(self._queue)

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
            # If we stop during a song, add it to the front of the queue to be resumed later
            if self._now_playing is not None:
                if self._play_start_time is not None:
                    # Add the time spent playing this track to the starting offset, so it resumes
                    # where it left off
                    self._now_playing.offset += max(
                        time.perf_counter() - self._play_start_time,
                        0.0
                    )
                    self._play_start_time = None
                self._queue.appendleft(self._now_playing)
                self._now_playing = None
            self._play_task.cancel()
            await self._play_task
        if self._stream is not None:
            self._stream.stop()
            self._stream = None

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
            self._queue.append(Track(
                info["url"],
                info["title"],
                info["duration"],
                info["is_live"] or False  # is_live is either True or None?? Thanks ytdl
            ))
            self._queue_update_flag.set()
            self._on_queue_change(self.queue())
        elif extractor_used == "YoutubePlaylist":
            log.debug("YoutubePlaylists still unimplemented!")
            raise uita.exceptions.MalformedMessage("YoutubePlaylists unimplemented (but will be)")
        elif extractor_used is None:
            raise uita.exceptions.MalformedMessage("Malformed URLs should send an error message")
        else:
            raise uita.exceptions.MalformedMessage("Unhandled extractor used")

    def _after_song(self):
        self._now_playing = None
        self._queue_update_flag.set()
        self._on_queue_change(self.queue())
        if self._stream is not None:
            self._stream.stop()
            self._stream = None

    async def _play_loop(self, voice):
        try:
            while voice.is_connected():
                self._queue_update_flag.clear()
                if self._now_playing is None and len(self._queue) > 0:
                    self._now_playing = self._queue.popleft()
                    log.debug("Now playing {}".format(self._now_playing.title))
                    # Set encoder options that are injected into ffmpeg
                    voice.encoder_options(
                        sample_rate=FfmpegStream.SAMPLE_RATE,
                        channels=FfmpegStream.CHANNELS
                    )
                    # Launch ffmpeg process
                    self._stream = FfmpegStream(
                        self._now_playing.url,
                        voice.encoder.frame_size,
                        offset=self._now_playing.offset if not self._now_playing.live else 0.0
                    )
                    player = voice.create_stream_player(
                        self._stream,
                        after=lambda: self.loop.call_soon_threadsafe(self._after_song)
                    )
                    # Waits until ffmpeg has buffered audio before playing
                    await self._stream.wait_ready(loop=self.loop)
                    # Wait an extra second for livestreams to ensure player clock runs behind input
                    if self._now_playing.live is True:
                        await asyncio.sleep(1, loop=self.loop)
                    # About the same as a max volume YouTube video, I think
                    player.volume = 0.5
                    # Sync play start time to player start
                    self._play_start_time = time.perf_counter()
                    player.start()
                await self._queue_update_flag.wait()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("Unhandled exception: {}", e)


class FfmpegStream():
    """Provides a data stream interface from an ffmpeg process for a `discord.StreamPlayer`

    Compared to the ffmpeg stream player provided by `discord.VoiceClient.create_ffmpeg_player()`,
    this implementation will attempt to pre-fetch and cache (buffer) a sizable amount of audio
    data in a concurrently running thread to minimize any hiccups while fetching audio data for
    the consumer thread. This noticably cuts down on stuttering during playback, especially for
    live streams.

    Parameters
    ----------
    url : str
        URL for audio resource to be played.
    frame_size : int
        Amount of bytes to be returned by `FfmpegStream.read()`. **Note that `FfmpegStream.read()`
        actually ignores its byte input parameter as the buffered audio data chunks are of
        uniform size.** This is because Python lacks a good ring buffer implementation, so this is
        a hacky work around to avoid creating a new one. Judging by discord.py's implementation
        it will always call `FfmpegStream.read()` with a size of
        `discord.VoiceClient.encoder.frame_size`, so just pass that into the constructor and
        things should be okay. Sorry.
    offset : float, optional
        Time offset in fractional seconds to start playback of audio resource from.

    """
    SAMPLE_RATE = 48000
    CHANNELS = 2

    def __init__(self, url, frame_size, offset=0.0):
        self._process = subprocess.Popen([
            "ffmpeg",
            "-reconnect", "1",
            "-ss", str(offset),
            "-i", url,
            "-f", "s16le",
            "-ac", str(FfmpegStream.CHANNELS),
            "-ar", str(FfmpegStream.SAMPLE_RATE),
            "-acodec", "pcm_s16le",
            "-vn",
            "-loglevel", "quiet",
            "pipe:1"
        ], stdout=subprocess.PIPE)
        # Ensure ffmpeg processes are cleaned up at exit, since Python handles this horribly
        atexit.register(self.stop)
        self._frame_size = frame_size

        # Expecting a frame size of 3840 currently, queue should max out at 3.5MB~ of memory
        self._buffer = queue.Queue(maxsize=1000)
        # Run audio production and consumption in separate threads, buffering as much as possible
        # This cuts down on audio dropping out during playback (especially for livestreams)
        self._buffer_thread = threading.Thread(target=self._buffer_audio_packets)
        # Causes thread to force exit on shutdown without cleaning up resources
        # Python is really pretty bad for concurrency, maybe they intend for you to use events to
        # trigger resource cleanup except this totally defeats the purpose of being able to use
        # blocking calls in threads which is exactly how most of these threadable data structures
        # are meant to be used!! It's very poorly designed!!!
        self._buffer_thread.daemon = True
        self._buffer_thread.start()
        # Set once queue has buffered audio data available
        self._is_ready = threading.Event()

    def read(self, size):
        """Returns a `bytes` array of raw audio data.

        Parameters
        ----------
        size : int
            Ignored. See the `frame_size` parameter of `FfmpegStream()` for the terrifying details.

        Returns
        -------
        bytes
            Array of raw audio data. Size of array is equal to (or less than if EOF has been
            reached) the `frame_size` parameter passed into the object constructor.

        """
        if size != self._frame_size:
            log.error("Audio process queue has mismatched frame_size and read size.")
            return b""
        try:
            return self._buffer.get(timeout=5)
        except queue.Empty:
            log.warn("Audio process queue is not being produced")
            self.stop()
            # Empty read indicates completion
            return b""

    def stop(self):
        """Stops any currently running processes."""
        try:
            # We don't need to kill the thread here since it auto terminates after 10 seconds
            # without buffer consumption
            self._process.kill()
        except Exception:
            # subprocess.kill() can throw if the process has already ended...
            # But I forget what type of exception it is and it's seemingly undocumented
            pass
        finally:
            atexit.unregister(self.stop)

    async def wait_ready(self, loop=None):
        """Waits until the first packet of buffered audio data is available to be read.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop, optional
            Event loop to launch threaded blocking wait task from.

        """
        async_loop = loop or asyncio.get_event_loop()
        await async_loop.run_in_executor(None, lambda: self._is_ready.wait())

    def _buffer_audio_packets(self):
        need_set_ready = True
        # Read from process stdout until an empty byte string is returned
        for data in iter(lambda: self._process.stdout.read(self._frame_size), b""):
            try:
                # If the buffer fills and times out it means the queue is no longer being
                # consumed, this likely means we're running in a zombie thread and should
                # terminate. Ideally Python would let you send cancellation exceptions
                # to child threads, much like how asyncio works, but hey who cares about
                # consistency? Just let the timeout clean up our old resources instead...
                # However! Since we use daemon threads, this method would just leave dangling
                # ffmpeg processes on exit, and so we must register every spawned process to be
                # cleaned up on exit. Python is really pretty terrible for concurrency. Chears.
                self._buffer.put(data, timeout=5)
                if need_set_ready is True:
                    self._is_ready.set()
                    need_set_ready = False
            except queue.Full:
                self.stop()
                return
        try:
            # self.read returning an empty byte string indicates EOF
            self._buffer.put(b"", timeout=5)
        except queue.Full:
            pass
        finally:
            self.stop()