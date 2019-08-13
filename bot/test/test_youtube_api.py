import pytest
from unittest.mock import Mock, patch

import json
import re

import uita.youtube_api


@pytest.mark.asyncio
async def test_search(data_dir, event_loop):
    with patch("requests.get") as mock_get:
        def find_json(*args, **kwargs):
            # Press X
            url = args[0]
            path = None
            if re.match(r".*\/search\/.*", url):
                path = data_dir / "youtube-api-search.json"
            elif re.match(r".*\/videos\/.*", url):
                path = data_dir / "youtube-api-search-details.json"
            assert path is not None
            with open(path, "rb") as f:
                content = f.read()
            mock_response = Mock(status_code=200, content=content)
            mock_response.json.return_value = json.loads(content)
            return mock_response
        mock_get.side_effect = find_json

        results = await uita.youtube_api.search("chocobanana", api_key="real-key", loop=event_loop)
        assert len(results) == 5
        assert results[0]["title"] == "Video 1"
        assert results[0]["duration"] == 5
        assert results[1]["thumbnail"] == "http://example.com/vid2/default.jpg"
        assert results[2]["id"] == "vid3"
        assert results[3]["live"] is False
        assert results[4]["uploader"] == "Uploader 5"


def test_parse_time():
    assert uita.youtube_api.parse_time("PT5S") == 5
    assert uita.youtube_api.parse_time("PT1M0S") == 60
    assert uita.youtube_api.parse_time("PT10M30S") == 630
    assert uita.youtube_api.parse_time("PT1H0M0S") == 3600
    assert uita.youtube_api.parse_time("PT10H10M10S") == 36610


def test_build_url():
    assert uita.youtube_api.build_url("vid1") == "https://youtube.com/watch?v=vid1"
