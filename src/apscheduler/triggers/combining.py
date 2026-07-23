from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Any

import attrs

from .._converters import as_aware_datetime, as_timedelta, list_converter
from .._exceptions import MaxIterationsReached
from .._marshalling import marshal_object, unmarshal_object
from .._utils import require_state_version
from ..abc import Trigger


@attrs.define
class BaseCombiningTrigger(Trigger):
    triggers: list[Trigger]
    _next_fire_times: list[datetime | None] = attrs.field(
        init=False, eq=False, converter=list_converter(as_aware_datetime), factory=list
    )

    def __getstate__(self) -> dict[str, Any]:
        return {
            "version": 1,
            "triggers": [marshal_object(trigger) for trigger in self.triggers],
            "next_fire_times": self._next_fire_times,
        }

    @abstractmethod
    def __setstate__(self, state: dict[str, Any]) -> None:
        self.triggers = [
            unmarshal_object(*trigger_state) for trigger_state in state["triggers"]
        ]
        self._next_fire_times = state["next_fire_times"]


@attrs.define
class AndTrigger(BaseCombiningTrigger):

    threshold: timedelta = attrs.field(converter=as_timedelta, default=1)
    max_iterations: int | None = 10000

    def next(self) -> datetime | None:
        pass

    def __getstate__(self) -> dict[str, Any]:
        state = super().__getstate__()
        state["threshold"] = self.threshold
        state["max_iterations"] = self.max_iterations
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        require_state_version(self, state, 1)
        super().__setstate__(state)
        self.threshold = state["threshold"]
        self.max_iterations = state["max_iterations"]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.triggers}, "
            f"threshold={self.threshold.total_seconds()}, "
            f"max_iterations={self.max_iterations})"
        )


@attrs.define
class OrTrigger(BaseCombiningTrigger):

    def next(self) -> datetime | None:
        pass

    def __setstate__(self, state: dict[str, Any]) -> None:
        require_state_version(self, state, 1)
        super().__setstate__(state)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.triggers})"
