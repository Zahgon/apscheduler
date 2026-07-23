from __future__ import annotations

from collections.abc import Callable
from inspect import isawaitable
from typing import Any

from .._structures import Job
from ..abc import JobExecutor


class AsyncJobExecutor(JobExecutor):

    async def run_job(self, func: Callable[..., Any], job: Job) -> Any:
        pass
