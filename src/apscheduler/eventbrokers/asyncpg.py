from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from contextlib import AsyncExitStack, asynccontextmanager
from logging import Logger
from typing import TYPE_CHECKING, Any

import asyncpg
import attrs
from anyio import (
    EndOfStream,
    create_memory_object_stream,
    move_on_after,
)
from anyio.abc import TaskStatus
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from asyncpg import Connection, InterfaceError
from attr.validators import instance_of

from .._events import Event
from .._exceptions import SerializationError
from .._utils import create_repr
from .base import BaseExternalEventBroker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


@attrs.define(eq=False, repr=False)
class AsyncpgEventBroker(BaseExternalEventBroker):

    dsn: str
    options: Mapping[str, Any] = attrs.field(
        factory=dict, validator=instance_of(Mapping)
    )
    channel: str = attrs.field(kw_only=True, default="apscheduler")
    max_idle_time: float = attrs.field(kw_only=True, default=10)

    _send: MemoryObjectSendStream[str] = attrs.field(init=False)

    @classmethod
    def from_async_sqla_engine(
        cls,
        engine: AsyncEngine,
        options: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncpgEventBroker:
        pass

    def __repr__(self) -> str:
        return create_repr(self, "dsn")

    @property
    def _temporary_failure_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    @asynccontextmanager
    async def _connect(self) -> AsyncGenerator[asyncpg.Connection, None]:
        pass

    async def start(self, exit_stack: AsyncExitStack, logger: Logger) -> None:
        pass

    async def _listen_notifications(
        self, receive: MemoryObjectReceiveStream[str], *, task_status: TaskStatus[None]
    ) -> None:
        pass

    async def publish(self, event: Event) -> None:
        pass
