from __future__ import annotations

from logging import Logger

import attrs
from attr.validators import instance_of
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)
from tenacity.stop import stop_base
from tenacity.wait import wait_base


@attrs.define(kw_only=True, frozen=True)
class RetrySettings:

    stop: stop_base = attrs.field(
        validator=instance_of(stop_base),
        default=stop_after_delay(60),
    )
    wait: wait_base = attrs.field(
        validator=instance_of(wait_base),
        default=wait_exponential(min=0.5, max=20),
    )


@attrs.define(kw_only=True, slots=False)
class RetryMixin:

    retry_settings: RetrySettings = attrs.field(default=RetrySettings())
    _logger: Logger = attrs.field(init=False)

    @property
    def _temporary_failure_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    def _retry(self) -> AsyncRetrying:
        pass
