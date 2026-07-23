
from __future__ import annotations

import re
from calendar import monthrange
from datetime import datetime
from re import Pattern
from typing import TYPE_CHECKING, ClassVar

import attrs
from attr.validators import instance_of, optional

from ..._converters import as_int
from ..._validators import non_negative_number, positive_number

if TYPE_CHECKING:
    from .fields import BaseField

WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def get_weekday_index(weekday: str) -> int:
    pass


@attrs.define(slots=True)
class AllExpression:
    value_re: ClassVar[Pattern] = re.compile(r"\*(?:/(?P<step>\d+))?$")

    step: int | None = attrs.field(
        converter=as_int,
        validator=optional([instance_of(int), positive_number]),
        default=None,
    )

    def validate_range(self, field_name: str, min_value: int, max_value: int) -> None:
        pass

    def get_next_value(self, dateval: datetime, field: BaseField) -> int | None:
        pass

    def __str__(self) -> str:
        return f"*/{self.step}" if self.step else "*"


@attrs.define(kw_only=True)
class RangeExpression(AllExpression):
    value_re: ClassVar[Pattern] = re.compile(
        r"(?P<first>\d+)(?:-(?P<last>\d+))?(?:/(?P<step>\d+))?$"
    )

    first: int = attrs.field(
        converter=as_int, validator=[instance_of(int), non_negative_number]
    )
    last: int | None = attrs.field(
        converter=as_int,
        validator=optional([instance_of(int), non_negative_number]),
        default=None,
    )

    def __attrs_post_init__(self) -> None:
        if self.last is None and self.step is None:
            self.last = self.first

        if self.last is not None and self.first > self.last:
            raise ValueError(
                "The minimum value in a range must not be higher than the maximum"
            )

    def validate_range(self, field_name: str, min_value: int, max_value: int) -> None:
        pass

    def get_next_value(self, dateval: datetime, field: BaseField) -> int | None:
        pass

    def __str__(self) -> str:
        if self.last != self.first and self.last is not None:
            rangeval = f"{self.first}-{self.last}"
        else:
            rangeval = str(self.first)

        if self.step:
            return f"{rangeval}/{self.step}"

        return rangeval


class MonthRangeExpression(RangeExpression):
    value_re: ClassVar[Pattern] = re.compile(
        r"(?P<first>[a-z]+)(?:-(?P<last>[a-z]+))?", re.IGNORECASE
    )

    def __init__(self, first: str, last: str | None = None):
        try:
            first_num = MONTHS.index(first.lower()) + 1
        except ValueError:
            raise ValueError(f"Invalid month name {first!r}") from None

        if last:
            try:
                last_num = MONTHS.index(last.lower()) + 1
            except ValueError:
                raise ValueError(f"Invalid month name {last!r}") from None
        else:
            last_num = None

        super().__init__(first=first_num, last=last_num)

    def __str__(self) -> str:
        if self.last != self.first and self.last is not None:
            return f"{MONTHS[self.first - 1]}-{MONTHS[self.last - 1]}"

        return MONTHS[self.first - 1]


@attrs.define(kw_only=True, init=False)
class WeekdayRangeExpression(RangeExpression):
    value_re: ClassVar[Pattern] = re.compile(
        r"(?P<first>[a-z]+)(?:-(?P<last>[a-z]+))?", re.IGNORECASE
    )

    def __init__(self, first: str, last: str | None = None):
        first_num = get_weekday_index(first)
        last_num = get_weekday_index(last) if last else None
        self.__attrs_init__(first=first_num, last=last_num)

    def __str__(self) -> str:
        if self.last != self.first and self.last is not None:
            return f"{WEEKDAYS[self.first]}-{WEEKDAYS[self.last]}"

        return WEEKDAYS[self.first]


@attrs.define(kw_only=True, init=False)
class WeekdayPositionExpression(AllExpression):
    options: ClassVar[tuple[str, ...]] = ("1st", "2nd", "3rd", "4th", "5th", "last")
    value_re: ClassVar[Pattern] = re.compile(
        f"(?P<option_name>{'|'.join(options)}) +(?P<weekday_name>(?:\\d+|\\w+))",
        re.IGNORECASE,
    )

    option_num: int
    weekday: int

    def __init__(self, *, option_name: str, weekday_name: str):
        option_num = self.options.index(option_name.lower())
        try:
            weekday = WEEKDAYS.index(weekday_name.lower())
        except ValueError:
            raise ValueError(f"Invalid weekday name {weekday_name!r}") from None

        self.__attrs_init__(option_num=option_num, weekday=weekday)

    def get_next_value(self, dateval: datetime, field: BaseField) -> int | None:
        pass

    def __str__(self) -> str:
        return f"{self.options[self.option_num]} {WEEKDAYS[self.weekday]}"


class LastDayOfMonthExpression(AllExpression):
    value_re: ClassVar[Pattern] = re.compile(r"last", re.IGNORECASE)

    def __init__(self) -> None:
        super().__init__(None)

    def get_next_value(self, dateval: datetime, field: BaseField) -> int | None:
        pass

    def __str__(self) -> str:
        return "last"
