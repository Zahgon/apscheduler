from __future__ import annotations

from base64 import b64decode, b64encode
from collections.abc import Callable, Iterable
from contextlib import AsyncExitStack
from inspect import iscoroutine
from logging import Logger
from typing import Any

import attrs
from anyio import CapacityLimiter, create_task_group, to_thread
from anyio.abc import TaskGroup

from .. import _events
from .._events import Event
from .._exceptions import DeserializationError
from .._retry import RetryMixin
from ..abc import EventBroker, Serializer, Subscription
from ..serializers.json import JSONSerializer


@attrs.define(eq=False, frozen=True)
class LocalSubscription(Subscription):
    callback: Callable[[Event], Any]
    event_types: set[type[Event]] | None
    one_shot: bool
    is_async: bool
    token: object
    _source: BaseEventBroker

    def unsubscribe(self) -> None:
        pass


@attrs.define(kw_only=True)
class BaseEventBroker(EventBroker):
    _logger: Logger = attrs.field(init=False)
    _subscriptions: dict[object, LocalSubscription] = attrs.field(
        init=False, factory=dict
    )
    _task_group: TaskGroup = attrs.field(init=False)
    _thread_limiter: CapacityLimiter = attrs.field(init=False)

    async def start(self, exit_stack: AsyncExitStack, logger: Logger) -> None:
        pass

    def subscribe(
        self,
        callback: Callable[[Event], Any],
        event_types: Iterable[type[Event]] | None = None,
        *,
        is_async: bool = True,
        one_shot: bool = False,
    ) -> Subscription:
        pass

    def unsubscribe(self, token: object) -> None:
        pass

    async def publish_local(self, event: Event) -> None:
        pass

    async def _deliver_event(
        self, subscription: LocalSubscription, event: Event
    ) -> None:
        pass


@attrs.define(kw_only=True)
class BaseExternalEventBroker(BaseEventBroker, RetryMixin):

    serializer: Serializer = attrs.field(factory=JSONSerializer)

    def generate_notification(self, event: Event) -> bytes:
        pass

    def generate_notification_str(self, event: Event) -> str:
        pass

    def _reconstitute_event(self, event_type: str, serialized: bytes) -> Event | None:
        pass

    def reconstitute_event(self, payload: bytes) -> Event | None:
        pass

    def reconstitute_event_str(self, payload: str) -> Event | None:
        pass
