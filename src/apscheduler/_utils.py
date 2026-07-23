
from __future__ import annotations

import asyncio
from datetime import datetime, tzinfo
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar
from zoneinfo import ZoneInfo

from ._exceptions import DeserializationError
from .abc import Trigger

try:
    import sniffio
except ImportError:
    sniffio = None

if TYPE_CHECKING:
    from ._structures import MetadataType

T = TypeVar("T")


class UnsetValue:

    __slots__ = ()

    def __new__(cls) -> UnsetValue:
        try:
            return unset
        except NameError:
            return super().__new__(cls)

    def __getstate__(self) -> NoReturn:
        raise RuntimeError("Internal error: attempted to serialize an unset value")

    def __repr__(self) -> str:
        return "<unset>"


unset = UnsetValue()


def timezone_repr(timezone: tzinfo) -> str:
    pass


def absolute_datetime_diff(dateval1: datetime, dateval2: datetime) -> float:
    pass


def qualified_name(cls: type) -> str:
    pass


def require_state_version(
    trigger: Trigger, state: dict[str, Any], max_version: int
) -> None:
    pass


def merge_metadata(
    base_metadata: MetadataType, *overlays: MetadataType | UnsetValue
) -> MetadataType:
    pass


def create_repr(instance: object, *attrnames: str, **kwargs) -> str:
    pass


def time_exists(dt: datetime) -> bool:
    pass


def current_async_library() -> str:
    pass
