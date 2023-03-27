from typing import Any, Dict, Optional

from yt_dlp import utils as utils  # noqa: F401


class YoutubeDL:
    def __init__(self, opts: Dict[str, Any] = ...) -> None: ...

    def extract_info(
        self,
        url: str,
        download: bool = ...,
        ie_key: Optional[str] = ...
    ) -> Dict[str, Any]: ...
