from __future__ import annotations

from datetime import date, datetime, time, timedelta, tzinfo
from typing import Any

import attrs
from attr.validators import instance_of, optional

from .._converters import as_aware_datetime, as_date, as_timezone
from .._utils import require_state_version, timezone_repr
from ..abc import Trigger


@attrs.define(kw_only=True)
class CalendarIntervalTrigger(Trigger):

    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0
    hour: int = 0
    minute: int = 0
    second: int = 0
    start_date: date = attrs.field(
        converter=as_date, validator=instance_of(date), factory=date.today
    )
    end_date: date | None = attrs.field(
        converter=as_date, validator=optional(instance_of(date)), default=None
    )
    timezone: tzinfo = attrs.field(
        converter=as_timezone, validator=instance_of(tzinfo), default="local"
    )
    _time: time = attrs.field(init=False, eq=False)
    _last_fire_date: date | None = attrs.field(
        init=False, eq=False, converter=as_aware_datetime, default=None
    )

    def __attrs_post_init__(self) -> None:
        self._time = time(self.hour, self.minute, self.second, tzinfo=self.timezone)

        if self.years == self.months == self.weeks == self.days == 0:
            raise ValueError("interval must be at least 1 day long")

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("end_date cannot be earlier than start_date")

    def next(self) -> datetime | None:
        pass

    def __getstate__(self) -> dict[str, Any]:
        return {
            "version": 1,
            "interval": [self.years, self.months, self.weeks, self.days],
            "time": [self._time.hour, self._time.minute, self._time.second],
            "start_date": self.start_date,
            "end_date": self.end_date,
            "timezone": self.timezone,
            "last_fire_date": self._last_fire_date,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        require_state_version(self, state, 1)
        self.years, self.months, self.weeks, self.days = state["interval"]
        self.start_date = state["start_date"]
        self.end_date = state["end_date"]
        self.timezone = state["timezone"]
        self._time = time(*state["time"], tzinfo=self.timezone)
        self._last_fire_date = state["last_fire_date"]

    def __repr__(self) -> str:
        fields = []
        for field in "years", "months", "weeks", "days":
            value = getattr(self, field)
            if value > 0:
                fields.append(f"{field}={value}")

        fields.append(f"time={self._time.isoformat()!r}")
        fields.append(f"start_date='{self.start_date}'")
        if self.end_date:
            fields.append(f"end_date='{self.end_date}'")

        fields.append(f"timezone={timezone_repr(self.timezone)!r}")
        return f"{self.__class__.__name__}({', '.join(fields)})"
