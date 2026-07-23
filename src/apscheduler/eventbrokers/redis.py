from __future__ import annotations

from asyncio import CancelledError
from contextlib import AsyncExitStack
from logging import Logger

import anyio
import attrs
import tenacity
from anyio import move_on_after
from attr.validators import instance_of
from redis import ConnectionError
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from redis.asyncio.connection import ConnectionPool

from .._events import Event
from .._utils import create_repr
from .base import BaseExternalEventBroker


@attrs.define(eq=False, repr=False)
class RedisEventBroker(BaseExternalEventBroker):

    client_or_url: Redis | str = attrs.field(validator=instance_of((Redis, str)))
    channel: str = attrs.field(kw_only=True, default="apscheduler")
    stop_check_interval: float = attrs.field(kw_only=True, default=1)

    _client: Redis = attrs.field(init=False)
    _close_on_exit: bool = attrs.field(init=False, default=False)
    _stopped: bool = attrs.field(init=False, default=True)

    def __attrs_post_init__(self) -> None:
        if isinstance(self.client_or_url, str):
            pool = ConnectionPool.from_url(self.client_or_url)
            self._client = Redis(connection_pool=pool)
            self._close_on_exit = True
        else:
            self._client = self.client_or_url

    def __repr__(self) -> str:
        return create_repr(self, "client_or_url")

    def _retry(self) -> tenacity.AsyncRetrying:
        pass

    async def _close_client(self) -> None:
        pass

    async def start(self, exit_stack: AsyncExitStack, logger: Logger) -> None:
        pass

    async def _listen_messages(self, pubsub: PubSub) -> None:
        pass

    async def publish(self, event: Event) -> None:
        pass
