from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone, tzinfo
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from tzlocal import get_localzone


def as_int(value: int | str) -> int:
    pass


def as_datetime(value: datetime | str) -> datetime:
    pass


def as_aware_datetime(value: datetime | str) -> datetime:
    pass


def as_date(value: date | str) -> date:
    pass


def as_timezone(value: tzinfo | str) -> tzinfo:
    pass


def as_uuid(value: UUID | str) -> UUID:
    pass


def as_timedelta(value: timedelta | int) -> timedelta:
    pass


def as_enum(enum_class: Any) -> Callable[[Any], Any]:
    def converter(value: Any) -> Any:
        if isinstance(value, str):
            return enum_class[value]

        return value

    return converter


def list_converter(converter: Callable[[Any], Any]) -> Callable[[Any], Any]:
    def convert(value: Any) -> Any:
        pass

    return convert
