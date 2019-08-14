"""Audio queue management."""
import asyncio
import atexit
import collections
import copy
import discord
import enum
import json
import os
import queue
import subprocess
import threading
import time
import uuid
from typing import cast, Any, Awaitable, Callable, Deque, List, Optional

import uita.exceptions
import uita.youtube_api

import logging
log = logging.getLogger(__name__)


class Track():
    """Container for audio resource metadata.

    Args:
        path: Path to audio resource for ffmpeg to load.
        user: User that requested track.
        title: Title of track.
        duration: Track duration in seconds.
        live: Determines if the track is a remote livestream.
        local: Determines if the track is a local file or not.
        url: The public URL of the track if it exists, ``None`` otherwise.

    Attributes:
        id (str): Unique 32 character long ID.
        path (str): Path to audio resource for ffmpeg to load.
        user (uita.types.DiscordUser): User that requested track.
        title (str): Title of track.
        duration (int): Track duration in seconds.
        live (bool): Determines if the track is a remote livestream.
        local (bool): Determines if the track is a local file or not.
        url (typing.Optional[str]): The public URL of the track if it exists, ``None`` otherwise.
        offset (float): Offset in seconds to start track from.

    """
    def __init__(
        self,
        path: str,
        user: "uita.types.DiscordUser",
        title: str,
        duration: float,
        live: bool,
        local: bool,
        url: Optional[str] = None
    ):
        self.id = uuid.uuid4().hex
        self.path = path
        self.user = user
        self.title = title
        self.duration = float(duration)
        self.live = live
        self.local = local
        self.url = url
        self.offset: float = 0.0


# NOTE: These values must be synced with the enum used in utils/Message.js:PlayStatusSendMessage
class Status(enum.IntEnum):
    """Play status for audio."""
    PLAYING = 1
    PAUSED = 2


class Queue():
    """Queues audio resources to be played by a looping task.

    Args:
        maxlen: Maximum queue size. Default is ``None``, which is unlimited.
        on_queue_change: Callback that is triggered everytime the state of the playback queue
            changes. Function accepts a list of :class:`~uita.audio.Track` as its only argument.
        on_status_change: Callback that is triggered everytime the playback status changes.
            Function accepts a :class:`~uita.audio.Status` as its only argument.
        loop: Event loop for audio tasks to run in.

    Attributes:
        loop (asyncio.AbstractEventLoop): Event loop for audio tasks to run in.
        status (uita.audio.Status): Current playback status (playing, paused, etc).

    """
    QueueCallbackType = Callable[
        [List[Track], Optional["uita.types.DiscordUser"]], Awaitable[None]
    ]
    StatusCallbackType = Callable[[Status], None]

    def __init__(
        self,
        maxlen: Optional[int] = None,
        on_queue_change: Optional[QueueCallbackType] = None,
        on_status_change: Optional[StatusCallbackType] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        # async lambdas don't exist
        async def dummy_queue_change(q: Any, u: Any) -> None: pass
        self._on_queue_change = on_queue_change or dummy_queue_change

        async def dummy_status_change(s: Any) -> None: pass
        self._on_status_change = on_status_change or dummy_status_change

        self.loop = loop or asyncio.get_event_loop()
        self.status = Status.PAUSED
        self._now_playing: Optional[Track] = None
        self._queue: Deque[Track] = collections.deque()
        self._queue_lock = asyncio.Lock(loop=self.loop)
        self._queue_update_flag = asyncio.Event(loop=self.loop)
        self._queue_maxlen = maxlen
        self._play_task: Optional[asyncio.Task[Any]] = None
        self._play_start_time: Optional[float] = None
        self._stream: Optional[FfmpegStream] = None
        self._voice: Optional[discord.VoiceClient] = None

    def queue(self) -> List[Track]:
        """Retrieves a list of currently queued audio resources.

        Returns:
            Ordered list of audio resources queued for playback.

        """
        if self._now_playing is not None:
            # To maintain timer precision we want to avoid modifying the current tracks offset
            # outside of pause/resumes
            now_playing = copy.copy(self._now_playing)
            if self._play_start_time is not None:
                now_playing.offset += max(
                    time.perf_counter() - self._play_start_time,
                    0.0
                )
            return [now_playing] + list(self._queue)
        return list(self._queue)

    def queue_full(self) -> bool:
        """Tests if the queue is at capacity.

        Returns:
            True if the queue is full.

        """
        return self._queue_maxlen is not None and len(self.queue()) >= self._queue_maxlen

    async def play(self, voice: discord.VoiceClient) -> None:
        """Starts a new playlist task that awaits and plays new queue inputs.

        First stops current playlist task if it exists.

        Args:
            voice: Voice connection to spawn audio players for.

        """
        # Cancels currently running play task
        await self.stop()
        self._play_task = self.loop.create_task(self._play_loop(voice))

    async def stop(self) -> None:
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
        self._end_stream()

    async def enqueue_file(self, path: str, user: "uita.types.DiscordUser") -> None:
        """Queues a file to be played by the running playlist task.

        Args:
            path: Path for audio resource to be played.
            user: User that requested track.

        Raises:
            uita.exceptions.ClientError: If called with an unusable audio path.

        """
        # Some quick sanitization to make sure bad input won't escape the cache directory
        # However user input should never reach this function
        filename = os.path.join(uita.utils.cache_dir(), os.path.basename(path))
        if not os.path.isfile(filename):
            raise uita.exceptions.ClientError(
                uita.message.ErrorFileInvalidMessage("Invalid audio format")
            )
        completed_probe_process = await self.loop.run_in_executor(
            None,
            lambda: subprocess.run([
                "ffprobe",
                filename,
                "-of", "json",
                "-show_format",
                "-show_error",
                "-loglevel", "quiet"
            ], stdout=subprocess.PIPE)
        )
        probe = json.loads(completed_probe_process.stdout.decode("utf-8"))
        if "format" not in probe:
            raise uita.exceptions.ClientError(
                uita.message.ErrorFileInvalidMessage("Invalid audio format")
            )
        title = "untagged file upload"
        if "tags" in probe["format"]:
            # ffprobe sometimes keys tags in all caps or not
            tags = {k.lower(): v for k, v in probe["format"]["tags"].items()}
            title = "{} - {}".format(
                tags.get("artist", "Unknown artist"),
                tags.get("title", "Unknown title")
            )
        log.info(f"[{user.name}:{user.id}] Enqueue [Local]{title}, {probe['format']['duration']}s")
        # This check cannot have any awaits between it and the following queue.append()s
        if self.queue_full():
            raise uita.exceptions.ClientError(uita.message.ErrorQueueFullMessage())
        self._queue.append(Track(
            filename,
            user,
            title,
            float(probe["format"]["duration"]),
            live=False,
            local=True
        ))
        await self._notify_queue_change(user)

    async def enqueue_url(self, url: str, user: "uita.types.DiscordUser") -> None:
        """Queues a URL to be played by the running playlist task.

        Args:
            url: URL for audio resource to be played.
            user: User that requested track.

        Raises:
            uita.exceptions.ClientError: If called with an unusable audio path.

        """
        info = await uita.youtube_api.scrape(url, loop=self.loop)
        # This check cannot have any awaits between it and the following queue.append()s
        if self.queue_full():
            raise uita.exceptions.ClientError(uita.message.ErrorQueueFullMessage())
        if info["extractor"] == "Youtube":
            log.info(f"[{user.name}:{user.id}] Enqueue [YouTube]{info['title']}({info['id']}) "
                     f"{info['acodec']}@{info['abr']}abr, {info['duration']}s")
            self._queue.append(Track(
                info["url"],
                user,
                info["title"],
                float(info["duration"]),
                info["is_live"] or False,  # is_live is either True or None?? Thanks ytdl
                local=False,
                url=f"https://youtube.com/watch?v={info['id']}"
            ))
            await self._notify_queue_change(user)
        elif info["extractor"] == "YoutubePlaylist":
            if info["_type"] != "playlist":
                raise uita.exceptions.ServerError("Unknown playlist type")
            for entry in info["entries"]:
                await self.enqueue_url(f"https://youtube.com/watch?v={entry['id']}", user)
        else:
            raise uita.exceptions.ClientError(uita.message.ErrorUrlInvalidMessage())

    async def move(self, track_id: str, position: int) -> None:
        """Moves a track to a new position in the playback queue.

        Args:
            track_id: Track ID of audio resource to be moved.
            position: Index position for the track to be moved to.

        """
        with await self._queue_lock:
            if position >= len(self.queue()) or position < 0:
                log.debug("Requested queue index out of bounds")
                return
            # Check if re-ordering the queue will change the currently playing song
            if self._now_playing is not None and self._voice is not None:
                # No need to swap with self while playing, would restart the track
                if self._now_playing.id == track_id and position == 0:
                    return
                if self._now_playing.id == track_id or position == 0:
                    self._now_playing.offset = 0
                    self._queue.appendleft(self._now_playing)
                    self._now_playing = None
                    self._voice.stop()
                # Since now_playing will not be added to the queue, offset the index to compensate
                else:
                    position -= 1
            for index, track in enumerate(self._queue):
                if track.id == track_id:
                    del self._queue[index]
                    self._queue.insert(position, track)
                    await self._notify_queue_change()
                    return

    async def remove(self, track_id: str) -> None:
        """Removes a track from the playback queue.

        Args:
            track_id: Track ID of audio resource to be removed.

        """
        with await self._queue_lock:
            if self._now_playing is not None and self._now_playing.id == track_id:
                if self._voice is not None:
                    self._voice.stop()
                return
            for track in self._queue:
                if track.id == track_id:
                    self._queue.remove(track)
                    await self._notify_queue_change()
                    return

    async def track_from_url(self, url: str) -> Track:
        """Probes the audio resource at a given URL for audio metadata.

        Args:
            url: URL to audio resource.

        Returns:
            Container for track metadata.

        """
    async def _after_song(self) -> None:
        with await self._queue_lock:
            self._now_playing = None
            self._change_status(Status.PAUSED)
            await self._notify_queue_change()
            self._end_stream()

    def _change_status(self, status: Status) -> None:
        self.status = status
        self._on_status_change(self.status)

    async def _play_loop(self, voice: discord.VoiceClient) -> None:
        try:
            while voice.is_connected():
                self._queue_update_flag.clear()
                with await self._queue_lock:
                    if self._voice is None and len(self._queue) > 0:
                        self._now_playing = self._queue.popleft()
                        log.info(f"[{self._now_playing.user.name}:{self._now_playing.user.id}] "
                                 f"Now playing {self._now_playing.title}")
                        # Launch ffmpeg process
                        self._stream = FfmpegStream(
                            self._now_playing,
                            voice.encoder
                        )
                        self._voice = voice
                        # Waits until ffmpeg has buffered audio before playing
                        await self._stream.wait_ready(loop=self.loop)
                        # Wait an extra second for livestreams so player clock runs behind input
                        if self._now_playing.live is True:
                            await asyncio.sleep(1, loop=self.loop)
                        # Sync play start time to player start
                        self._play_start_time = time.perf_counter()
                        self._voice.play(
                            # About the same as a max volume YouTube video, I think
                            discord.PCMVolumeTransformer(self._stream, volume=0.3),
                            after=lambda err: asyncio.run_coroutine_threadsafe(
                                self._after_song(),
                                loop=self.loop
                            )
                        )
                        self._change_status(Status.PLAYING)
                await self._queue_update_flag.wait()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"Unhandled exception: {e}")

    async def _notify_queue_change(self, user: Optional["uita.types.DiscordUser"] = None) -> None:
        self._queue_update_flag.set()
        await self._on_queue_change(self.queue(), user)

    def _end_stream(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream = None
        if self._voice is not None:
            self._voice.stop()
            self._voice = None


class FfmpegStream(discord.AudioSource):
    """Provides a data stream interface from an ffmpeg process for a ``discord.StreamPlayer``

    Compared to the ffmpeg stream player provided by ``discord.FFmpegPCMAudio``,
    this implementation will attempt to pre-fetch and cache (buffer) a sizable amount of audio
    data in a concurrently running thread to minimize any hiccups while fetching audio data for
    the consumer thread. This noticably cuts down on stuttering during playback, especially for
    live streams.

    Args:
        track: Track to be played.
        encoder: Opus encoder is needed to configure sampling rate for FFmpeg.

    """

    def __init__(self, track: Track, encoder: discord.opus.Encoder) -> None:
        self._track = track
        self._encoder = encoder
        process_options = [
            "ffmpeg"
        ]
        # The argument order is very important
        if not self._track.local:
            process_options += [
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10"
            ]
        process_options += [
            "-ss", str(track.offset if not track.live else 0.0),
            "-i", track.path,
            "-f", "s16le",
            "-ac", str(self._encoder.CHANNELS),
            "-ar", str(self._encoder.SAMPLING_RATE),
            "-acodec", "pcm_s16le",
            "-vn",
            "-loglevel", "quiet",
            "pipe:1"
        ]

        self._process = subprocess.Popen(process_options, stdout=subprocess.PIPE)
        # Ensure ffmpeg processes are cleaned up at exit, since Python handles this horribly
        atexit.register(self.stop)

        # Expecting a frame size of 3840 currently, queue should max out at 3.5MB~ of memory
        self._buffer: queue.Queue[bytes] = queue.Queue(maxsize=1000)
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

    def read(self) -> bytes:
        """Returns an array of raw audio data.

        Returns:
            Array of raw audio data. Size of array is equal to (or less than if EOF has been
            reached) the ``FRAME_SIZE`` of the opus Encoder parameter passed into the object
            constructor.

        """
        try:
            return self._buffer.get(timeout=10)
        except queue.Empty:
            log.warning("Audio process queue is not being produced")
            self.stop()
            # Empty read indicates completion
            return b""

    def is_opus(self) -> bool:
        """Produces raw PCM audio data."""
        return False

    def cleanup(self) -> None:
        """Cleanup is handled outside the discord.py API."""
        pass

    def stop(self) -> None:
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
            self._is_ready.set()
            atexit.unregister(self.stop)

    async def wait_ready(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Waits until the first packet of buffered audio data is available to be read.

        Args:
            loop: Event loop to launch threaded blocking wait task from.

        """
        async_loop = loop or asyncio.get_event_loop()
        await async_loop.run_in_executor(None, lambda: self._is_ready.wait())

    def _buffer_audio_packets(self) -> None:
        need_set_ready = True

        # Read from process stdout until an empty byte string is returned
        def read() -> bytes:
            return cast(bytes, self._process.stdout.read(self._encoder.FRAME_SIZE))
        for data in iter(read, b""):
            try:
                # If the buffer fills and times out it means the queue is no longer being
                # consumed, this likely means we're running in a zombie thread and should
                # terminate. Ideally Python would let you send cancellation exceptions
                # to child threads, much like how asyncio works, but hey who cares about
                # consistency? Just let the timeout clean up our old resources instead...
                # However! Since we use daemon threads, this method would just leave dangling
                # ffmpeg processes on exit, and so we must register every spawned process to be
                # cleaned up on exit. Python is really pretty terrible for concurrency. Chears.
                if len(data) != self._encoder.FRAME_SIZE:
                    break
                self._buffer.put(data, timeout=10)
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
