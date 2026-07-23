from __future__ import annotations

import attrs

from .._events import Event
from .._utils import create_repr
from .base import BaseEventBroker


@attrs.define(eq=False, repr=False)
class LocalEventBroker(BaseEventBroker):

    def __repr__(self) -> str:
        return create_repr(self)

    async def publish(self, event: Event) -> None:
        pass
