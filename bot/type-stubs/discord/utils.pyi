from typing import Any, Iterable, Optional, TypeVar

T = TypeVar("T")


def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]: ...
