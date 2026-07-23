from __future__ import annotations

from contextlib import AsyncExitStack
from logging import Logger

import attrs

from .._retry import RetryMixin
from ..abc import DataStore, EventBroker, Serializer
from ..serializers.pickle import PickleSerializer


@attrs.define(kw_only=True)
class BaseDataStore(DataStore):

    _event_broker: EventBroker = attrs.field(init=False)
    _logger: Logger = attrs.field(init=False)

    async def start(
        self, exit_stack: AsyncExitStack, event_broker: EventBroker, logger: Logger
    ) -> None:
        pass


@attrs.define(kw_only=True)
class BaseExternalDataStore(BaseDataStore, RetryMixin):

    serializer: Serializer = attrs.field(factory=PickleSerializer)
    start_from_scratch: bool = attrs.field(default=False)
