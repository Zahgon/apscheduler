from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from contextlib import AsyncExitStack, asynccontextmanager
from logging import Logger
from typing import TYPE_CHECKING, Any

import attrs
from anyio import (
    EndOfStream,
    create_memory_object_stream,
    move_on_after,
)
from anyio.abc import TaskStatus
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from attr.validators import instance_of
from psycopg import AsyncConnection, InterfaceError

from .._events import Event
from .._exceptions import SerializationError
from .._utils import create_repr
from .._validators import positive_number
from .base import BaseExternalEventBroker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


def convert_options(value: Mapping[str, Any]) -> dict[str, Any]:
    pass


@attrs.define(eq=False, repr=False)
class PsycopgEventBroker(BaseExternalEventBroker):

    conninfo: str = attrs.field(validator=instance_of(str))
    options: Mapping[str, Any] = attrs.field(
        factory=dict, converter=convert_options, validator=instance_of(Mapping)
    )
    channel: str = attrs.field(
        kw_only=True, default="apscheduler", validator=instance_of(str)
    )
    max_idle_time: float = attrs.field(
        kw_only=True, default=10, validator=[instance_of((int, float)), positive_number]
    )

    _send: MemoryObjectSendStream[str] = attrs.field(init=False)

    @classmethod
    def from_async_sqla_engine(
        cls,
        engine: AsyncEngine,
        options: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> PsycopgEventBroker:
        pass

    def __repr__(self) -> str:
        return create_repr(self, "conninfo")

    @property
    def _temporary_failure_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    @asynccontextmanager
    async def _connect(self) -> AsyncGenerator[AsyncConnection, None]:
        pass

    async def start(self, exit_stack: AsyncExitStack, logger: Logger) -> None:
        pass

    async def _listen_notifications(self, *, task_status: TaskStatus[None]) -> None:
        pass

    async def _publish_notifications(
        self, receive: MemoryObjectReceiveStream[str], *, task_status: TaskStatus[None]
    ) -> None:
        pass

    async def publish(self, event: Event) -> None:
        pass
