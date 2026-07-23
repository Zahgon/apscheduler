
from __future__ import annotations

import re
from calendar import monthrange
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, ClassVar

from .expressions import (
    WEEKDAYS,
    AllExpression,
    LastDayOfMonthExpression,
    MonthRangeExpression,
    RangeExpression,
    WeekdayPositionExpression,
    WeekdayRangeExpression,
    get_weekday_index,
)

MIN_VALUES = {
    "year": 1970,
    "month": 1,
    "day": 1,
    "week": 1,
    "day_of_week": 0,
    "hour": 0,
    "minute": 0,
    "second": 0,
}
MAX_VALUES = {
    "year": 9999,
    "month": 12,
    "day": 31,
    "week": 53,
    "day_of_week": 7,
    "hour": 23,
    "minute": 59,
    "second": 59,
}
DEFAULT_VALUES: Mapping[str, str | int] = {
    "year": "*",
    "month": 1,
    "day": 1,
    "week": "*",
    "day_of_week": "*",
    "hour": 0,
    "minute": 0,
    "second": 0,
}
SEPARATOR = re.compile(" *, *")


class BaseField:
    __slots__ = "expressions", "name"

    real: ClassVar[bool] = True
    compilers: ClassVar[Any] = (AllExpression, RangeExpression)

    def __init_subclass__(cls, real: bool = True, extra_compilers: Sequence = ()):
        cls.real = real
        if extra_compilers:
            cls.compilers += extra_compilers

    def __init__(self, name: str, exprs: int | str):
        self.name = name
        self.expressions: list = []
        for expr in SEPARATOR.split(str(exprs).strip()):
            self.append_expression(expr)

    def get_min(self, dateval: datetime) -> int:
        pass

    def get_max(self, dateval: datetime) -> int:
        pass

    def get_value(self, dateval: datetime) -> int:
        pass

    def get_next_value(self, dateval: datetime) -> int | None:
        pass

    def append_expression(self, expr: str) -> None:
        pass

    def __str__(self) -> str:
        expr_strings = (str(e) for e in self.expressions)
        return ",".join(expr_strings)


class WeekField(BaseField, real=False):
    __slots__ = ()

    def get_value(self, dateval: datetime) -> int:
        pass


class DayOfMonthField(
    BaseField, extra_compilers=(WeekdayPositionExpression, LastDayOfMonthExpression)
):
    __slots__ = ()

    def get_max(self, dateval: datetime) -> int:
        pass


class DayOfWeekField(BaseField, real=False, extra_compilers=(WeekdayRangeExpression,)):
    __slots__ = ()

    def append_expression(self, expr: str) -> None:
        pass

    def get_value(self, dateval: datetime) -> int:
        pass


class MonthField(BaseField, extra_compilers=(MonthRangeExpression,)):
    __slots__ = ()
