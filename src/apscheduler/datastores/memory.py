from __future__ import annotations

from bisect import bisect_left, bisect_right, insort_right
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import MAXYEAR, datetime, timedelta, timezone
from functools import partial
from uuid import UUID

import attrs

from .. import JobOutcome
from .._enums import ConflictPolicy
from .._events import (
    JobAcquired,
    JobAdded,
    JobReleased,
    ScheduleAdded,
    ScheduleRemoved,
    ScheduleUpdated,
    TaskAdded,
    TaskRemoved,
    TaskUpdated,
)
from .._exceptions import ConflictingIdError, TaskLookupError
from .._structures import Job, JobResult, Schedule, ScheduleResult, Task
from .._utils import create_repr
from .base import BaseDataStore

max_datetime = datetime(MAXYEAR, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)


@attrs.define(eq=False, repr=False)
class MemoryDataStore(BaseDataStore):

    _tasks: dict[str, Task] = attrs.Factory(dict)
    _schedules: list[Schedule] = attrs.Factory(list)
    _schedules_by_id: dict[str, Schedule] = attrs.Factory(dict)
    _schedules_by_task_id: dict[str, set[Schedule]] = attrs.Factory(
        partial(defaultdict, set)
    )
    _jobs_by_id: dict[UUID, Job] = attrs.Factory(dict)
    _jobs_by_task_id: dict[str, set[Job]] = attrs.Factory(partial(defaultdict, set))
    _jobs_by_schedule_id: dict[str, set[Job]] = attrs.Factory(partial(defaultdict, set))
    _job_results: dict[UUID, JobResult] = attrs.Factory(dict)

    def __repr__(self) -> str:
        return create_repr(self)

    def _find_schedule_index(self, schedule: Schedule) -> int:
        pass

    async def get_schedules(self, ids: set[str] | None = None) -> list[Schedule]:
        pass

    async def add_task(self, task: Task) -> None:
        pass

    async def remove_task(self, task_id: str) -> None:
        pass

    async def get_task(self, task_id: str) -> Task:
        pass

    async def get_tasks(self) -> list[Task]:
        pass

    async def add_schedule(
        self, schedule: Schedule, conflict_policy: ConflictPolicy
    ) -> None:
        pass

    async def remove_schedules(
        self, ids: Iterable[str], *, finished: bool = False
    ) -> None:
        pass

    async def acquire_schedules(
        self, scheduler_id: str, lease_duration: timedelta, limit: int
    ) -> list[Schedule]:
        pass

    async def release_schedules(
        self, scheduler_id: str, results: Sequence[ScheduleResult]
    ) -> None:
        pass

    async def get_next_schedule_run_time(self) -> datetime | None:
        pass

    async def add_job(self, job: Job) -> None:
        pass

    async def get_jobs(self, ids: Iterable[UUID] | None = None) -> list[Job]:
        pass

    async def acquire_jobs(
        self, scheduler_id: str, lease_duration: timedelta, limit: int | None = None
    ) -> list[Job]:
        pass

    async def release_job(self, scheduler_id: str, job: Job, result: JobResult) -> None:
        pass

    async def get_job_result(self, job_id: UUID) -> JobResult | None:
        pass

    async def extend_acquired_schedule_leases(
        self, scheduler_id: str, schedule_ids: set[str], duration: timedelta
    ) -> None:
        pass

    async def extend_acquired_job_leases(
        self, scheduler_id: str, job_ids: set[UUID], duration: timedelta
    ) -> None:
        pass

    async def reap_abandoned_jobs(self, scheduler_id: str) -> None:
        pass

    async def cleanup(self) -> None:
        pass
