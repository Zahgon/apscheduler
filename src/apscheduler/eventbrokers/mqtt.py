from __future__ import annotations

import sys
from concurrent.futures import Future
from contextlib import AsyncExitStack
from logging import Logger
from ssl import SSLContext
from typing import Any

import attrs
from anyio import to_thread
from anyio.from_thread import BlockingPortal
from attr.validators import in_, instance_of, optional
from paho.mqtt.client import Client, MQTTMessage
from paho.mqtt.enums import CallbackAPIVersion

from .._events import Event
from .._utils import create_repr
from .base import BaseExternalEventBroker

ALLOWED_TRANSPORTS = ("mqtt", "mqtts", "ws", "wss", "unix")


@attrs.define(eq=False, repr=False)
class MQTTEventBroker(BaseExternalEventBroker):

    host: str = attrs.field(default="localhost", validator=instance_of(str))
    port: int | None = attrs.field(default=None, validator=optional(instance_of(int)))
    transport: str = attrs.field(
        default="tcp", validator=in_(["tcp", "websocket", "unix"])
    )
    client_id: str | None = attrs.field(
        default=None, validator=optional(instance_of(str))
    )
    ssl: bool | SSLContext = attrs.field(
        default=False, validator=instance_of((bool, SSLContext))
    )
    topic: str = attrs.field(
        kw_only=True, default="apscheduler", validator=instance_of(str)
    )
    subscribe_qos: int = attrs.field(kw_only=True, default=0, validator=in_([0, 1, 2]))
    publish_qos: int = attrs.field(kw_only=True, default=0, validator=in_([0, 1, 2]))

    _use_tls: bool = attrs.field(init=False, default=False)
    _client: Client = attrs.field(init=False)
    _portal: BlockingPortal = attrs.field(init=False)
    _ready_future: Future[None] = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        if self.port is None:
            if self.transport == "tcp":
                self.port = 8883 if self.ssl else 1883
            elif self.transport == "websocket":
                self.port = 443 if self.ssl else 80

        self._client = Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
            transport=self.transport,
        )
        if isinstance(self.ssl, SSLContext):
            self._client.tls_set_context(self.ssl)
        elif self.ssl:
            self._client.tls_set()

    def __repr__(self) -> str:
        return create_repr(self, "host", "port", "transport")

    async def start(self, exit_stack: AsyncExitStack, logger: Logger) -> None:
        pass

    def _on_connect(self, client: Client, *_: Any) -> None:
        pass

    def _on_connect_fail(self, *_: Any) -> None:
        pass

    def _on_disconnect(self, *args: Any) -> None:
        pass

    def _on_subscribe(self, *_: Any) -> None:
        pass

    def _on_message(self, _: Any, __: Any, msg: MQTTMessage) -> None:
        pass

    async def publish(self, event: Event) -> None:
        pass
