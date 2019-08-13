import pytest
from unittest.mock import Mock

import asyncio
from pathlib import Path
import math
import shutil

import uita.audio
import uita.types
import uita.utils


@pytest.fixture
def init_queue(data_dir, user):
    async def _init(*queued_filenames):
        source_filename = "test.flac"
        async def queue_change_stub(*args, **kwargs): ...
        mock_queue_change = Mock(side_effect=queue_change_stub)
        mock_status_change = Mock()

        queue = uita.audio.Queue(
            on_queue_change=mock_queue_change,
            on_status_change=mock_status_change
        )

        cache_dir = Path(uita.utils.cache_dir())
        for filename in queued_filenames:
            shutil.copyfile(data_dir / source_filename, cache_dir / filename)
            await queue.enqueue_file(str(cache_dir / filename), user)

        return queue, mock_queue_change, mock_status_change
    return _init


def test_track_unique_ids():
    a = uita.audio.Track(None, None, None, 0.0, None, None)
    b = uita.audio.Track(None, None, None, 0.0, None, None)
    assert a.id != b.id


@pytest.mark.asyncio
async def test_enqueue_file(init_queue):
    queue, mock_queue_change, mock_status_change = await init_queue("1")

    assert mock_queue_change.call_count == 1
    assert mock_status_change.call_count == 0
    assert len(queue.queue()) == 1

    track = queue.queue()[0]
    assert track.title == "uitabot - song title"
    assert math.isclose(track.duration, 5.0)
    assert not track.live
    assert track.local


@pytest.mark.asyncio
async def test_play(init_queue):
    queue, _, mock_status_change = await init_queue("1", "2")
    flag = asyncio.Event(loop=queue.loop)

    def on_status_change(_): flag.set()
    mock_status_change.side_effect = on_status_change
    await queue.play(Mock(**{
        "is_connected.return_value": True,
        "encoder.FRAME_SIZE": 4096
    }))
    await flag.wait()

    assert mock_status_change.call_count == 1
    assert len(queue.queue()) == 2

    await queue.stop()


@pytest.mark.asyncio
async def test_move(init_queue):
    queue, _, _ = await init_queue("1", "2")

    assert len(queue.queue()) == 2

    old_queue = queue.queue()

    await queue.move(old_queue[1].id, 1)
    assert queue.queue() == old_queue

    await queue.move(old_queue[1].id, 0)
    assert queue.queue() == old_queue[::-1]


@pytest.mark.asyncio
async def test_remove(init_queue):
    queue, _, _ = await init_queue("1")

    assert len(queue.queue()) == 1
    await queue.remove(queue.queue()[0].id)
    assert len(queue.queue()) == 0
