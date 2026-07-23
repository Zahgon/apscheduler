from __future__ import annotations

from collections.abc import Callable
from contextlib import AsyncExitStack
from functools import partial
from typing import Any

import attrs
from anyio import CapacityLimiter, to_thread

from .._structures import Job
from ..abc import JobExecutor


@attrs.define(eq=False, kw_only=True)
class ThreadPoolJobExecutor(JobExecutor):

    max_workers: int = 40
    _limiter: CapacityLimiter = attrs.field(init=False)

    async def start(self, exit_stack: AsyncExitStack) -> None:
        pass

    async def run_job(self, func: Callable[..., Any], job: Job) -> Any:
        pass
