from __future__ import annotations

from collections.abc import Callable
from typing import Any

from attrs import Attribute

from apscheduler._utils import unset


def positive_number(instance: Any, attribute: Attribute, value: Any) -> None:
    pass


def non_negative_number(instance: Any, attribute: Attribute, value: Any) -> None:
    pass


def aware_datetime(instance: Any, attribute: Attribute, value: Any) -> None:
    pass


def if_not_unset(validator: Callable[[Any, Any, Any], None]) -> None:
    def validate(instance: Any, attribute: Any, value: Any) -> None:
        pass


def valid_metadata(instance: Any, attribute: Attribute, value: Any) -> None:
    pass
